#!/usr/bin/env bash
# ==============================================================================
# 脚本名称: backup.sh
# 脚本说明: Linux 服务器通用自动化备份脚本（支持 MySQL、文件目录打包、AES-256 加密及多端异地同步）
# 参考来源: Teddysun <i@teddysun.com> (https://teddysun.com/469.html)
# 功能特性:
#   1. 支持备份 MySQL 数据库（指定数据库或全量导出）
#   2. 支持备份网站目录、Nginx、FRP、系统服务与环境配置
#   3. 支持 OpenSSL AES-256-CBC 密码加密（增加 salt 与 pbkdf2 高迭代防爆破）
#   4. 支持 Google Drive (通过 Rclone) 与远程 FTP 服务器上传（使用现代 curl 方案）
#   5. 智能本地旧备份自动删除（基于时间戳解析）与远端主动扫描过期清理闭环
#   6. Exit Trap 安全退出保障：异常退出时清理临时 SQL 并保障本地旧备份兜底清理
# ==============================================================================

# 遇到未捕获错误立即退出（由 EXIT trap 负责清理和日志记录）
set -e

# 检查执行权限（必须为 root 用户）
[[ $EUID -ne 0 ]] && echo "Error: This script must be run as root!" && exit 1

# 自动加载环境变量文件（优先支持系统全局凭据文件）
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

# 备份加密密码（支持环境变量 BACKUP_ENCRYPT_PASSWORD 或 /etc/env_addon 中的 backup_passwd）
# 解密命令示例:
# openssl enc -aes-256-cbc -d -md sha512 -pbkdf2 -iter 100000 -in [加密文件.enc] -out [解密文件.tgz] -pass pass:[密码]
BACKUPPASS="${BACKUP_ENCRYPT_PASSWORD:-${backup_passwd:-}}"

# --- MySQL 数据库配置 ---
MYSQL_ROOT_NAME="${BACKUP_MYSQL_USER_NAME:-${mysql_user:-}}"          # MySQL 用户名
MYSQL_ROOT_PASSWORD="${BACKUP_MYSQL_USER_PASSWORD:-${mysql_passwd:-}}"  # MySQL 密码（留空跳过 MySQL 备份）

# 需要备份的 MySQL 数据库列表（留空 array 则全量备份所有数据库）
MYSQL_DATABASE_NAME=(
    "blog"
    "users_igd"
    "users_cg"
    "users_eg"
)

# --- 存储路径与日志 ---
LOCALDIR="/home/backups/"                           # 本地备份归档存储目录
TEMPDIR="/home/backups/temp/"                       # 临时工作目录（存放临时 SQL 转储）
LOGFILE="/home/backups/backup.log"                  # 备份日志记录路径

# --- 备份文件与目录清单 ---
# 包含网站根目录、Nginx 配置、FRP 配置、Systemd 服务、Crontab、环境变量及 Docker 配置等
BACKUP=(
    # --- 1. 网站目录与应用数据 ---
    "/home/www/blog/usr"
    "/home/www/lovestory/data.json"
    "/home/www/lovestory/uploads"
    "/home/www/lovestory/.env"

    # --- 2. Web 服务器与反向代理 (Nginx) ---
    "/opt/nginx/conf"
    "/opt/nginx/niekun.net"
    "/opt/nginx/users"

    # --- 3. 代理与内网穿透服务 ---
    "/opt/frp/frps.toml"
    "/usr/local/etc/v2ray"

    # --- 4. 下载与文件共享存储 ---
    "/opt/aria2/aria2.conf"
    "/etc/vsftpd.conf"

    # --- 5. 系统核心配置与环境 ---
    "/etc/hostname"
    "/etc/crontab"
    "/etc/env_addon"
    "/etc/netplan/01-netcfg.yaml"
    "/root/.bashrc"

    # --- 6. 系统服务 Unit (Systemd) ---
    "/usr/lib/systemd/system"
    "/etc/systemd/system"

    # --- 7. Docker 容器应用配置 ---
    "/opt/docker/rustdesk/docker-compose.yml"
    "/opt/docker/miniflux/docker-compose.yml"

    # --- 8. 自定义 Python 业务服务与运维凭据 ---
    "/home/script/igd/app.log"
    "/home/script/igd/interferenceGrindingDressingServer.py"
    "/home/script/igd/requirements.txt"
    "/home/script/cg/app.log"
    "/home/script/cg/camGrindingServer.py"
    "/home/script/cg/requirements.txt"
    "/home/script/eg/app.log"
    "/home/script/eg/enveloGrinding.py"
    "/home/script/eg/requirements.txt"
    "/home/script/marco_pem"
)

# --- 保留天数与清理策略 ---
LOCALAGEDAILIES="1"                                 # 本地每日备份保留天数（超过该天数的旧备份将被删除）
DELETE_REMOTE_FILE_FLG=true                         # 是否同步删除 Google Drive 或 FTP 上的过期备份 (true/false)

# --- Google Drive (Rclone) 配置 ---
RCLONE_FLG=true                                     # 是否上传到 Google Drive (true: 上传, false: 不上传)
RCLONE_NAME="remote"                                # Rclone 远端配置名称
RCLONE_FOLDER="BandwagonBackup"                     # Google Drive 远端保存文件夹

# --- FTP 服务器配置 ---
FTP_FLG=false                                       # 是否上传到 FTP 服务器 (true: 上传, false: 不上传)
FTP_HOST="${FTP_HOST:-${ftp_host:-}}"              # FTP 服务器 IP 或域名
FTP_USER="${FTP_USER:-${ftp_user:-}}"              # FTP 登录用户名
FTP_PASS="${FTP_PASS:-${ftp_passwd:-}}"          # FTP 登录密码
FTP_DIR="${FTP_DIR:-}"                              # FTP 远程存放目录（例如: public_html）

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
# 日志记录函数 (写入日志文件同时输出至控制台)
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

    # 检查 FTP 上传所需工具 (基于 curl)
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
# 打包备份文件（预检目标存在性，支持 tar 打包与 openssl 高强度加密）
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
    [ -z "${RCLONE_NAME}" ] && log "Error: RCLONE_NAME cannot be empty!" && return 1
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
    [ -z "${FTP_HOST}" ] && log "Error: FTP_HOST cannot be empty!" && return 1
    [ -z "${FTP_USER}" ] && log "Error: FTP_USER cannot be empty!" && return 1
    [ -z "${FTP_PASS}" ] && log "Error: FTP_PASS cannot be empty!" && return 1
    log "Uploading to FTP: ftp://${FTP_HOST}/${FTP_DIR}"
    local FILENAME
    FILENAME=$(basename "${UPLOAD_FILE}")

    local target_url="ftp://${FTP_HOST}/"
    [ -n "${FTP_DIR}" ] && target_url="ftp://${FTP_HOST}/${FTP_DIR}/"

    if curl --fail --silent --show-error --ftp-create-dirs \
            -T "${UPLOAD_FILE}" \
            -u "${FTP_USER}:${FTP_PASS}" \
            "${target_url}"; then
        log "FTP upload successful: ${FILENAME}"
    else
        log "ERROR: FTP upload failed."
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 解析文件名中的时间戳并计算是否超过保留天数（跨平台兼容 Linux / macOS）
# ------------------------------------------------------------------------------
get_file_date_legacy() {
    local filename="$1"
    local file_date
    if [[ "$filename" =~ _([0-9]{8})[0-9]*\.(tgz|tar\.gz)(\.enc)?$ ]]; then
        file_date="${BASH_REMATCH[1]}"
    else
        return 1
    fi

    local file_sec
    if [[ "$OSTYPE" == "darwin"* ]]; then
        file_sec=$(date -j -f "%Y%m%d" "${file_date}" +%s 2>/dev/null || true)
    else
        file_sec=$(date -d "${file_date}" +%s 2>/dev/null || true)
    fi
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
# 清理本地过期备份（基于文件名时间戳解析）
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
    done < <(find "${LOCALDIR}" -maxdepth 1 \( -name "${HOSTNAME_FULL}_*.tgz" -o -name "${HOSTNAME_FULL}_*.tgz.enc" -o -name "${HOSTNAME_FULL}_*.tar.gz" -o -name "${HOSTNAME_FULL}_*.tar.gz.enc" \) -print0 2>/dev/null)
    log "Local cleanup finished. Removed ${count} file(s)."
}

# ------------------------------------------------------------------------------
# 清理远端过期备份（Google Drive / FTP 主动扫描比对与清理）
# ------------------------------------------------------------------------------
clean_remote_files() {
    if ! ${DELETE_REMOTE_FILE_FLG}; then return; fi

    if ${RCLONE_FLG} && ${RCLONE_AVAILABLE}; then
        log "Checking Google Drive for old files..."
        rclone lsf "${RCLONE_NAME}:${RCLONE_FOLDER}" 2>/dev/null | while read -r remote_file; do
            if [[ "$remote_file" == "${HOSTNAME_FULL}_"* ]] && get_file_date_legacy "$remote_file"; then
                 log "Deleting old Drive file: $remote_file"
                 rclone delete "${RCLONE_NAME}:${RCLONE_FOLDER}/$remote_file" 2>/dev/null || true
            fi
        done
    fi

    if ${FTP_FLG}; then
        [ -z "${FTP_HOST}" ] || [ -z "${FTP_USER}" ] || [ -z "${FTP_PASS}" ] && return
        log "Checking FTP for old files..."
        local ftp_target="ftp://${FTP_HOST}/"
        [ -n "${FTP_DIR}" ] && ftp_target="ftp://${FTP_HOST}/${FTP_DIR}/"
        local ftp_files
        ftp_files=$(curl --silent --list-only -u "${FTP_USER}:${FTP_PASS}" "${ftp_target}" 2>/dev/null || true)
        for remote_file in $ftp_files; do
            if [[ "$remote_file" == "${HOSTNAME_FULL}_"* ]] && get_file_date_legacy "$remote_file"; then
                 log "Deleting old FTP file: $remote_file"
                 curl --silent -u "${FTP_USER}:${FTP_PASS}" "${ftp_target}" -Q "DELE $remote_file" >/dev/null 2>&1 || true
            fi
        done
    fi
}

# ------------------------------------------------------------------------------
# 退出兜底处理函数 (Exit Trap)
# 无论脚本正常结束或异常中断，均能清理临时 SQL 并保障本地旧备份清理执行
# ------------------------------------------------------------------------------
cleanup_on_exit() {
    local exit_code=$?
    # 强制清理临时 SQL 文件
    rm -f "${TEMPDIR}"/*.sql 2>/dev/null || true
    # 兜底执行本地旧备份清理，防止因异常退出导致旧备份不断累积满盘
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
