#!/usr/bin/env bash
# ==============================================================================
# 脚本名称: backup_ubuntu_home_marco.sh
# 脚本说明: Ubuntu 主机自动化备份脚本（支持系统文件、Docker 配置、MySQL、加密与异地传输）
# 适用主机: ubuntu_home_marco
# 功能特性:
#   1. 支持备份 MySQL/MariaDB 单个或所有数据库
#   2. 支持备份系统关键配置文件、Docker Compose 项目配置与应用数据
#   3. 支持 AES-256-CBC 对称加密归档（可选）
#   4. 支持通过 Rclone 同步上传至 Google Drive 网盘（可选）
#   5. 支持通过 Curl 同步上传至远程 FTP 服务器（可选）
#   6. 智能本地旧备份自动删除（find -mtime +N，防满盘）与远端同步清理
#   7. Exit Trap 机制：保障异常或中断时临时 SQL 清理与本地旧备份保底清理
# ==============================================================================

# 遇到未捕获错误立即退出（由 EXIT trap 负责清理和日志记录）
set -e

# 检查执行权限（必须为 root 用户）
[[ $EUID -ne 0 ]] && echo "Error: This script must be run as root!" && exit 1

# 自动加载环境变量文件
if [ -f "/etc/env_addon" ]; then
    set -a
    . /etc/env_addon
    set +a
fi

# ==============================================================================
# 配置区域 (START OF CONFIG)
# ==============================================================================

# --- 加密设置 ---
# 是否加密备份文件 (true: 加密, false: 不加密)
ENCRYPTFLG=false

# 备份加密密码（请妥善保管；若开启加密，解密时需使用相同密码）
# 解密示例: openssl enc -aes-256-cbc -d -md sha512 -pbkdf2 -in [加密文件.enc] -out [解密文件.tgz] -pass pass:[密码]
BACKUPPASS="password"

# --- MySQL 数据库配置 ---
MYSQL_ROOT_NAME=""                     # MySQL root 用户名（留空则跳过 MySQL 备份）
MYSQL_ROOT_PASSWORD=""                 # MySQL root 密码
MYSQL_DATABASE_NAME=()                 # 指定备份的数据库列表，留空 array 则备份所有数据库

# --- 存储路径与日志 ---
LOCALDIR="/home/backups/"              # 本地备份归档存放根目录
TEMPDIR="/home/backups/temp/"          # 临时工作目录（用于存放临时 SQL 转储）
LOGFILE="/home/backups/backup.log"     # 备份操作日志输出路径

# --- 备份文件与目录清单 ---
BACKUP=(
    "/opt/docker/study_xxqg/docker-compose.yml"
    "/opt/docker/study_xxqg/config"
    "/opt/aria2/aria2.conf"
    "/opt/frp/frpc.toml"
    "/etc/crontab"
    "/usr/lib/systemd/system"
    "/root/.bashrc"
    "/etc/hostname"
    "/etc/vsftpd.conf"
    "/etc/env_addon"
    "/etc/nginx/conf.d"
    "/etc/systemd/system"
)

# --- 保留天数与清理策略 ---
LOCALAGEDAILIES="7"                    # 本地备份保留天数（超过该天数的文件将被自动删除）
DELETE_REMOTE_FILE_FLG=true            # 是否同步清理远端（Google Drive / FTP）超过保留天数的旧备份

# --- Google Drive (Rclone) 配置 ---
RCLONE_FLG=false                       # 是否上传到 Google Drive (true: 上传, false: 不上传)
RCLONE_NAME=""                         # Rclone 配置的远程驱动器名称 (如 "remote")
RCLONE_FOLDER=""                       # Rclone 远端保存目录

# --- FTP 服务器配置 ---
FTP_FLG=true                           # 是否上传到 FTP 服务器 (true: 上传, false: 不上传)
FTP_HOST="${ftp_host:-nas.home.marco}" # FTP 主机地址
FTP_USER="${ftp_user:-marco}"          # FTP 用户名
FTP_PASS="${ftp_passwd:-}"             # FTP 密码
FTP_DIR="nas-backup/UbuntuBackUp"      # FTP 远端保存目录

# ==============================================================================
# 配置区域结束 (END OF CONFIG)
# ==============================================================================

# 日期与主机名变量
BACKUPDATE=$(date +%Y%m%d%H%M%S)
HOSTNAME_FULL=$(hostname)

# 生成的目标备份文件名定义
TARFILE="${LOCALDIR}${HOSTNAME_FULL}_${BACKUPDATE}.tgz"
ENC_TARFILE="${TARFILE}.enc"
SQLFILE="${TEMPDIR}mysql_${BACKUPDATE}.sql"

# ------------------------------------------------------------------------------
# 日志记录函数 (写入日志文件同时可供追踪)
# ------------------------------------------------------------------------------
log() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S") $1" >> "${LOGFILE}"
    echo "$1"
}

# ------------------------------------------------------------------------------
# 检查所需命令行工具依赖是否齐全
# ------------------------------------------------------------------------------
check_commands() {
    local BINARIES=('cat' 'cd' 'du' 'date' 'dirname' 'echo' 'openssl' 'mysql' 'mysqldump' 'pwd' 'rm' 'tar' 'find')
    for BINARY in "${BINARIES[@]}"; do
        if [ "$BINARY" = "mysql" ] || [ "$BINARY" = "mysqldump" ]; then
            if [ -n "${MYSQL_ROOT_PASSWORD}" ] && ! command -v "$BINARY" >/dev/null 2>&1; then
                log "WARN: Command not found: $BINARY (MySQL backup enabled but client tools missing)"
            fi
            continue
        fi
        if ! command -v "$BINARY" >/dev/null 2>&1; then
            log "ERROR: Required command not found: $BINARY"
            exit 1
        fi
    done

    # 检查 Rclone 是否可用
    RCLONE_AVAILABLE=false
    if ${RCLONE_FLG}; then
        if command -v rclone >/dev/null 2>&1; then
            RCLONE_AVAILABLE=true
        else
            log "WARN: rclone not found, Google Drive upload will be skipped."
        fi
    fi

    if ${FTP_FLG} && ! command -v curl >/dev/null 2>&1; then
        log "ERROR: curl is required for FTP upload but not found."
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# 导出 MySQL 数据库
# ------------------------------------------------------------------------------
mysql_backup() {
    if [ -z "${MYSQL_ROOT_PASSWORD}" ]; then
        log "MySQL root password not set, skipping MySQL backup."
        return
    fi

    log "Starting MySQL dump..."
    local MYSQL_CMD="mysqldump --quick --single-transaction"
    [ -n "${MYSQL_ROOT_NAME}" ] && MYSQL_CMD+=" -u ${MYSQL_ROOT_NAME}"
    MYSQL_CMD+=" -p${MYSQL_ROOT_PASSWORD}"

    if [ ${#MYSQL_DATABASE_NAME[@]} -eq 0 ]; then
        log "Dumping all databases..."
        ${MYSQL_CMD} --all-databases > "${SQLFILE}" 2>/dev/null || { log "ERROR: mysqldump failed"; return 1; }
    else
        log "Dumping specific databases: ${MYSQL_DATABASE_NAME[*]}..."
        ${MYSQL_CMD} --databases "${MYSQL_DATABASE_NAME[@]}" > "${SQLFILE}" 2>/dev/null || { log "ERROR: mysqldump failed"; return 1; }
    fi
    log "MySQL dump completed: ${SQLFILE}"
}

# ------------------------------------------------------------------------------
# 打包备份文件（支持 tar 打包与 openssl 加密）
# ------------------------------------------------------------------------------
create_backup_archive() {
    local valid_items=()
    for item in "${BACKUP[@]}"; do
        if [ -e "$item" ]; then
            valid_items+=("$item")
        else
            log "Notice: Backup target not found (skipping): $item"
        fi
    done

    if [ -f "${SQLFILE}" ]; then
        valid_items+=("${SQLFILE}")
    fi

    if [ ${#valid_items[@]} -eq 0 ]; then
        log "ERROR: No valid files or directories found to backup."
        exit 1
    fi

    log "Creating tar archive..."
    tar -zcPf "${TARFILE}" "${valid_items[@]}"
    log "Tar backup completed: ${TARFILE}"

    local FINAL_FILE="${TARFILE}"

    if ${ENCRYPTFLG}; then
        log "Encrypting backup archive with AES-256-CBC..."
        openssl enc -aes-256-cbc -salt -md sha512 -pbkdf2 -iter 100000 \
            -in "${TARFILE}" -out "${ENC_TARFILE}" -pass "pass:${BACKUPPASS}"
        rm -f "${TARFILE}"
        FINAL_FILE="${ENC_TARFILE}"
        log "Encryption completed: ${ENC_TARFILE}"
    fi

    rm -f "${TEMPDIR}"/*.sql 2>/dev/null || true
    export UPLOAD_FILE="${FINAL_FILE}"
    local SIZE
    SIZE=$(du -h "${FINAL_FILE}" | awk '{print $1}')
    log "Backup ready: ${FINAL_FILE} (Size: ${SIZE})"
}

# ------------------------------------------------------------------------------
# 上传至 Google Drive (借助 Rclone)
# ------------------------------------------------------------------------------
rclone_upload() {
    if ! ${RCLONE_FLG} || ! ${RCLONE_AVAILABLE}; then return; fi
    log "Uploading to Google Drive via rclone: ${RCLONE_NAME}:${RCLONE_FOLDER}"
    if rclone copy "${UPLOAD_FILE}" "${RCLONE_NAME}:${RCLONE_FOLDER}"; then
        log "Rclone upload successful."
    else
        log "ERROR: Rclone upload failed."
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 上传至 FTP 服务器 (借助 Curl)
# ------------------------------------------------------------------------------
ftp_upload() {
    if ! ${FTP_FLG}; then return; fi
    log "Uploading to FTP: ftp://${FTP_HOST}/${FTP_DIR}"
    local FILENAME
    FILENAME=$(basename "${UPLOAD_FILE}")

    if curl --fail --silent --show-error --ftp-create-dirs \
            -T "${UPLOAD_FILE}" \
            -u "${FTP_USER}:${FTP_PASS}" \
            "ftp://${FTP_HOST}/${FTP_DIR}/"; then
        log "FTP upload successful: ${FILENAME}"
    else
        log "ERROR: FTP upload failed."
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 解析远端文件名时间戳并计算是否超过保留天数（用于远端清理）
# ------------------------------------------------------------------------------
get_file_date_legacy() {
    local filename="$1"
    local file_date
    if [[ "$filename" =~ _([0-9]{8})[0-9]*\.tgz(\.enc)?$ ]]; then
        file_date="${BASH_REMATCH[1]}"
    else
        return 1
    fi

    local file_sec
    file_sec=$(date -d "${file_date}" +%s 2>/dev/null || true)
    [ -z "$file_sec" ] && return 1

    local now_sec
    now_sec=$(date +%s)
    local diff_days=$(( (now_sec - file_sec) / 86400 ))

    if [ $diff_days -gt "${LOCALAGEDAILIES}" ]; then
        return 0
    else
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 清理本地过期备份（基于 find -mtime，支持 .tgz, .enc, .tar.gz）
# ------------------------------------------------------------------------------
clean_local_files() {
    log "Cleaning local backups older than ${LOCALAGEDAILIES} days in ${LOCALDIR}..."
    local count=0
    while IFS= read -r -d '' file; do
        if get_file_date_legacy "$(basename "$file")"; then
            log "Deleting old local backup: $file"
            rm -f "$file"
            ((count++)) || true
        fi
    done < <(find "${LOCALDIR}" -maxdepth 1 \( -name "${HOSTNAME_FULL}_*.tgz" -o -name "${HOSTNAME_FULL}_*.tgz.enc" \) -print0)
    log "Local cleanup finished. Removed ${count} file(s)."
}

# ------------------------------------------------------------------------------
# 清理远端过期备份（Google Drive / FTP）
# ------------------------------------------------------------------------------
clean_remote_files() {
    if ! ${DELETE_REMOTE_FILE_FLG}; then return; fi

    if ${RCLONE_FLG} && ${RCLONE_AVAILABLE}; then
        log "Checking Google Drive for old files..."
        rclone lsf "${RCLONE_NAME}:${RCLONE_FOLDER}" | while read -r remote_file; do
            if get_file_date_legacy "$remote_file"; then
                 log "Deleting old Drive file: $remote_file"
                 rclone delete "${RCLONE_NAME}:${RCLONE_FOLDER}/$remote_file"
            fi
        done
    fi

    if ${FTP_FLG}; then
        log "Checking FTP for old files..."
        local ftp_files
        ftp_files=$(curl --silent --list-only -u "${FTP_USER}:${FTP_PASS}" "ftp://${FTP_HOST}/${FTP_DIR}/" || true)
        for remote_file in $ftp_files; do
            if get_file_date_legacy "$remote_file"; then
                 log "Deleting old FTP file: $remote_file"
                 curl --silent -u "${FTP_USER}:${FTP_PASS}" "ftp://${FTP_HOST}/${FTP_DIR}/" -Q "DELE $remote_file" >/dev/null 2>&1 || true
            fi
        done
    fi
}

# ------------------------------------------------------------------------------
# 退出兜底处理函数 (Exit Trap)
# 无论脚本正常完成还是由于 set -e 中断，均能清理临时 SQL 并执行本地旧备份清理
# ------------------------------------------------------------------------------
cleanup_on_exit() {
    local exit_code=$?
    rm -f "${TEMPDIR}"/*.sql 2>/dev/null || true
    clean_local_files >/dev/null 2>&1 || true
    if [ $exit_code -ne 0 ]; then
        log "Backup script finished with exit status ${exit_code}."
    fi
}

# ------------------------------------------------------------------------------
# 主流程执行 (Main Execution)
# ------------------------------------------------------------------------------
trap cleanup_on_exit EXIT
STARTTIME=$(date +%s)

# 确保本地备份和临时目录存在
[ ! -d "${LOCALDIR}" ] && mkdir -p "${LOCALDIR}"
[ ! -d "${TEMPDIR}" ] && mkdir -p "${TEMPDIR}"

log "=== Backup Job Started ==="

# 1. 检查依赖与环境
check_commands

# 2. 导出数据库
mysql_backup

# 3. 生成归档并加密
create_backup_archive

# 4. 上传至异地存储
log "=== Uploading ==="
rclone_upload
ftp_upload

# 5. 执行常规清理
log "=== Cleanup ==="
clean_local_files
clean_remote_files

ENDTIME=$(date +%s)
DURATION=$((ENDTIME - STARTTIME))
log "=== All Done (Duration: ${DURATION}s) ==="

