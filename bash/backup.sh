#!/usr/bin/env bash
# ==============================================================================
# 脚本名称: backup.sh
# 脚本说明: Linux 服务器通用自动化备份脚本（支持 MySQL、文件目录打包、AES-256 加密及多端异地同步）
# 参考来源: Teddysun <i@teddysun.com> (https://teddysun.com/469.html)
# 功能特性:
#   1. 支持备份 MySQL 数据库（指定数据库或全量导出）
#   2. 支持备份网站目录、Nginx、FRP、系统服务与环境配置
#   3. 支持 OpenSSL AES-256-CBC 密码加密
#   4. 支持 Google Drive (通过 Rclone) 与远程 FTP 服务器上传
#   5. 智能本地旧备份自动删除（基于 find -mtime，兼容各类主机名）与远端同步清理
#   6. Exit Trap 安全退出保障：异常退出时清理临时 SQL 并保障本地旧备份清理
# ==============================================================================

# 检查执行权限（必须为 root 用户）
[[ $EUID -ne 0 ]] && echo "Error: This script must be run as root!" && exit 1

# ==============================================================================
# 配置区域 (START OF CONFIG)
# ==============================================================================

# --- 加密设置 ---
# 是否加密备份文件 (true: 加密, false: 不加密)
ENCRYPTFLG=true

# 备份加密密码（建议通过环境变量 BACKUP_ENCRYPT_PASSWORD 传入）
# 解密命令示例:
# openssl enc -aes-256-cbc -md sha512 -pbkdf2 -d -in [加密备份.enc] -out [解密备份.tgz] -pass pass:[备份密码]
BACKUPPASS=${BACKUP_ENCRYPT_PASSWORD}

# --- MySQL 数据库配置 ---
MYSQL_ROOT_NAME=${BACKUP_MYSQL_USER_NAME}          # MySQL 用户名
MYSQL_ROOT_PASSWORD=${BACKUP_MYSQL_USER_PASSWORD}  # MySQL 密码（留空则跳过 MySQL 备份）

# 需要备份的 MySQL 数据库列表（如果需要备份所有数据库，请将数组置空）
MYSQL_DATABASE_NAME[0]="blog"
MYSQL_DATABASE_NAME[1]="users_igd"
MYSQL_DATABASE_NAME[2]="users_cg"

# --- 存储路径与日志 ---
LOCALDIR="/home/backups/"                           # 本地备份归档存储目录
TEMPDIR="/home/backups/temp/"                       # 临时工作目录（存放临时 SQL 转储）
LOGFILE="/home/backups/backup.log"                  # 备份日志记录路径

# --- 备份文件与目录清单 ---
# 包含网站根目录、Nginx 配置、FRP 配置、Systemd 服务、Crontab、环境变量及 Docker 配置等
BACKUP[0]="/home/www/blog/usr"
BACKUP[1]="/opt/nginx/conf"
BACKUP[2]="/opt/nginx/niekun.net"
BACKUP[3]="/opt/nginx/users"
BACKUP[4]="/opt/frp/frps.toml"
BACKUP[5]="/opt/aria2/aria2.conf"
BACKUP[6]="/usr/local/etc/v2ray"
BACKUP[7]="/etc/crontab"
BACKUP[8]="/usr/lib/systemd/system"
BACKUP[9]="/root/.bashrc"
BACKUP[10]="/etc/env_addon"
BACKUP[11]="/opt/docker/rustdesk/docker-compose.yml"
BACKUP[12]="/opt/docker/miniflux/docker-compose.yml"
BACKUP[13]="/etc/hostname"
BACKUP[14]="/etc/vsftpd.conf"
BACKUP[15]="/etc/systemd/system"
BACKUP[16]="/home/script/igd/app.log"
BACKUP[17]="/home/script/cg/app.log"
BACKUP[18]="/home/script/eg/app.log"
BACKUP[19]="/etc/netplan/01-netcfg.yaml"
BACKUP[20]="/home/www/lovestory/data.json"
BACKUP[21]="/home/www/lovestory/uploads"
BACKUP[22]="/home/www/lovestory/.env"

# --- 保留天数与清理策略 ---
LOCALAGEDAILIES="1"                                 # 本地每日备份保留天数（超过该天数的旧备份将被删除）
DELETE_REMOTE_FILE_FLG=true                         # 是否同步删除 Google Drive 或 FTP 上的过期备份 (true/false)

# --- Google Drive (Rclone) 配置 ---
RCLONE_FLG=true                                     # 是否上传到 Google Drive (true: 上传, false: 不上传)
RCLONE_NAME="remote"                                # Rclone 远端配置名称
RCLONE_FOLDER="BandwagonBackup"                     # Google Drive 远端保存文件夹

# --- FTP 服务器配置 ---
FTP_FLG=false                                       # 是否上传到 FTP 服务器 (true: 上传, false: 不上传)
FTP_HOST=""                                         # FTP 服务器 IP 或域名
FTP_USER=""                                         # FTP 登录用户名
FTP_PASS=""                                         # FTP 登录密码
FTP_DIR=""                                          # FTP 远程存放目录（例如: public_html）

# ==============================================================================
# 配置区域结束 (END OF CONFIG)
# ==============================================================================

# 日期与时间变量
DAY=$(date +%d)
MONTH=$(date +%m)
YEAR=$(date +%C%y)
BACKUPDATE=$(date +%Y%m%d%H%M%S)

# 目标归档文件名
TARFILE="${LOCALDIR}""$(hostname)"_"${BACKUPDATE}".tgz
ENC_TARFILE="${TARFILE}.enc"
SQLFILE="${TEMPDIR}mysql_${BACKUPDATE}.sql"

# ------------------------------------------------------------------------------
# 日志记录函数
# ------------------------------------------------------------------------------
log() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S")" "$1" >> ${LOGFILE}
}

# ------------------------------------------------------------------------------
# 检查所需命令行工具依赖是否齐全
# ------------------------------------------------------------------------------
check_commands() {
    BINARIES=( cat cd du date dirname echo openssl mysql mysqldump pwd rm tar find )
    
    for BINARY in "${BINARIES[@]}"; do
        if [ ! "$(command -v "$BINARY")" ]; then
            log "$BINARY is not installed. Install it and try again"
            exit 1
        fi
    done

    # 检查 Rclone
    RCLONE_COMMAND=false
    if [ "$(command -v "rclone")" ]; then
        RCLONE_COMMAND=true
    fi

    # 检查 FTP 工具
    if ${FTP_FLG}; then
        if [ ! "$(command -v "ftp")" ]; then
            log "ftp is not installed. Install it and try again"
            exit 1
        fi
    fi
}

# ------------------------------------------------------------------------------
# 计算文件可读大小
# ------------------------------------------------------------------------------
calculate_size() {
    local file_name=$1
    local file_size=$(du -h $file_name 2>/dev/null | awk '{print $1}')
    if [ "x${file_size}" = "x" ]; then
        echo "unknown"
    else
        echo "${file_size}"
    fi
}

# ------------------------------------------------------------------------------
# 导出 MySQL 数据库
# ------------------------------------------------------------------------------
mysql_backup() {
    if [ -z ${MYSQL_ROOT_PASSWORD} ]; then
        log "MySQL root password not set, MySQL backup skipped"
    else
        log "MySQL dump start"
        mysql -u ${MYSQL_ROOT_NAME} -p${MYSQL_ROOT_PASSWORD} 2>/dev/null <<EOF
exit
EOF
        if [ $? -ne 0 ]; then
            log "MySQL root password is incorrect. Please check it and try again"
            exit 1
        fi
    
        if [ "${MYSQL_DATABASE_NAME[*]}" == "" ]; then
            # 导出所有数据库
            mysqldump -u ${MYSQL_ROOT_NAME} -p${MYSQL_ROOT_PASSWORD} --all-databases > "${SQLFILE}" 2>/dev/null
            if [ $? -ne 0 ]; then
                log "MySQL all databases backup failed"
                exit 1
            fi
            log "MySQL all databases dump file name: ${SQLFILE}"
            BACKUP=(${BACKUP[*]} ${SQLFILE})
        else
            # 依次导出指定的各数据库
            for db in ${MYSQL_DATABASE_NAME[*]}
            do
                unset DBFILE
                DBFILE="${TEMPDIR}${db}_${BACKUPDATE}.sql"
                mysqldump -u ${MYSQL_ROOT_NAME} -p${MYSQL_ROOT_PASSWORD} ${db} > "${DBFILE}" 2>/dev/null
                if [ $? -ne 0 ]; then
                    log "MySQL database name [${db}] backup failed, please check database name is correct and try again"
                    exit 1
                fi
                log "MySQL database name [${db}] dump file name: ${DBFILE}"
                BACKUP=(${BACKUP[*]} ${DBFILE})
            done
        fi
        log "MySQL dump completed"
    fi
}

# ------------------------------------------------------------------------------
# 打包并加密备份归档
# ------------------------------------------------------------------------------
start_backup() {
    [ "${BACKUP[*]}" == "" ] && echo "Error: You must to modify the [$(basename $0)] config before run it!" && exit 1

    log "Tar backup file start"
    # 使用 -P 保留绝对路径
    tar -zcPf ${TARFILE} ${BACKUP[*]}
    if [ $? -gt 1 ]; then
        log "Tar backup file failed"
        exit 1
    fi
    log "Tar backup file completed"

    # 若开启加密，使用 AES-256-CBC 进行加密，并清理未加密文件
    if ${ENCRYPTFLG}; then
        log "Encrypt backup file start"
        openssl enc -aes-256-cbc -md sha512 -pbkdf2 -pass pass:${BACKUPPASS} -in "${TARFILE}" -out "${ENC_TARFILE}"
        log "Encrypt backup file completed"

        log "Delete unencrypted tar file: ${TARFILE}"
        rm -f ${TARFILE}
    fi

    # 清理本次导出的临时 SQL 文件
    rm -f "${TEMPDIR}"/*.sql 2>/dev/null || true

    if ${ENCRYPTFLG}; then
        OUT_FILE="${ENC_TARFILE}"
    else
        OUT_FILE="${TARFILE}"
    fi
    log "File name: ${OUT_FILE}, File size: `calculate_size ${OUT_FILE}`"
}

# ------------------------------------------------------------------------------
# 上传备份归档至 Google Drive (借助 Rclone)
# ------------------------------------------------------------------------------
rclone_upload() {
    if ${RCLONE_FLG} && ${RCLONE_COMMAND}; then
        [ -z "${RCLONE_NAME}" ] && log "Error: RCLONE_NAME can not be empty!" && return 1
        if [ -n "${RCLONE_FOLDER}" ]; then
            rclone ls ${RCLONE_NAME}:${RCLONE_FOLDER} 2>&1 > /dev/null
            if [ $? -ne 0 ]; then
                log "Create the path ${RCLONE_NAME}:${RCLONE_FOLDER}"
                rclone mkdir ${RCLONE_NAME}:${RCLONE_FOLDER}
            fi
        fi
        log "Tranferring backup file: ${OUT_FILE} to Google Drive"
        rclone copy ${OUT_FILE} ${RCLONE_NAME}:${RCLONE_FOLDER} >> ${LOGFILE}
        if [ $? -ne 0 ]; then
            log "Error: Tranferring backup file: ${OUT_FILE} to Google Drive failed"
            return 1
        fi
        log "Tranferring backup file: ${OUT_FILE} to Google Drive completed"
    fi
}

# ------------------------------------------------------------------------------
# 上传备份归档至 FTP 服务器
# ------------------------------------------------------------------------------
ftp_upload() {
    if ${FTP_FLG}; then
        [ -z "${FTP_HOST}" ] && log "Error: FTP_HOST can not be empty!" && return 1
        [ -z "${FTP_USER}" ] && log "Error: FTP_USER can not be empty!" && return 1
        [ -z "${FTP_PASS}" ] && log "Error: FTP_PASS can not be empty!" && return 1
        [ -z "${FTP_DIR}" ] && log "Error: FTP_DIR can not be empty!" && return 1
        local FTP_OUT_FILE=$(basename ${OUT_FILE})
        log "Tranferring backup file: ${FTP_OUT_FILE} to FTP server"
        ftp -in ${FTP_HOST} 2>&1 >> ${LOGFILE} <<EOF
user $FTP_USER $FTP_PASS
binary
lcd $LOCALDIR
cd $FTP_DIR
put $FTP_OUT_FILE
quit
EOF
        if [ $? -ne 0 ]; then
            log "Error: Tranferring backup file: ${FTP_OUT_FILE} to FTP server failed"
            return 1
        fi
        log "Tranferring backup file: ${FTP_OUT_FILE} to FTP server completed"
    fi
}

# ------------------------------------------------------------------------------
# 解析文件名中的 14 位时间戳并计算文件天数（用于远端文件过期比对）
# ------------------------------------------------------------------------------
get_file_date() {
    local fname=$1
    local date_part
    # 提取文件名中的 14 位时间戳 (YYYYMMDDHHMMSS)，避免因主机名包含下划线导致截取失败
    date_part=$(echo "$fname" | grep -oE '[0-9]{14}' | head -1)

    if [ -z "$date_part" ]; then
        return 1
    fi
    
    local file_ts
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS 日期转换
        file_ts=$(date -j -f "%Y%m%d%H%M%S" "$date_part" +%s 2>/dev/null)
    else
        # Linux 日期转换
        file_ts=$(date -d "${date_part:0:8} ${date_part:8:2}:${date_part:10:2}:${date_part:12:2}" +%s 2>/dev/null)
    fi

    if [ -z "$file_ts" ]; then
        return 1
    fi

    local current_ts
    current_ts=$(date +%s)
    FILEAGE=$(( (current_ts - file_ts) / 86400 ))
    return 0
}

# ------------------------------------------------------------------------------
# 删除 Google Drive 上的指定过期备份文件
# ------------------------------------------------------------------------------
delete_gdrive_file() {
    local FILENAME=$1
    if ${DELETE_REMOTE_FILE_FLG} && ${RCLONE_COMMAND}; then
        rclone ls ${RCLONE_NAME}:${RCLONE_FOLDER}/${FILENAME} 2>&1 > /dev/null
        if [ $? -eq 0 ]; then
            rclone delete ${RCLONE_NAME}:${RCLONE_FOLDER}/${FILENAME} >> ${LOGFILE}
            if [ $? -eq 0 ]; then
                log "Google Drive's old backup file: ${FILENAME} has been deleted"
            else
                log "Failed to delete Google Drive's old backup file: ${FILENAME}"
            fi
        else
            log "Google Drive's old backup file: ${FILENAME} is not exist"
        fi
    fi
}

# ------------------------------------------------------------------------------
# 删除 FTP 服务器上的指定过期备份文件
# ------------------------------------------------------------------------------
delete_ftp_file() {
    local FILENAME=$1
    if ${DELETE_REMOTE_FILE_FLG} && ${FTP_FLG}; then
        ftp -in ${FTP_HOST} 2>&1 >> ${LOGFILE} <<EOF
user $FTP_USER $FTP_PASS
cd $FTP_DIR
del $FILENAME
quit
EOF
        if [ $? -eq 0 ]; then
            log "FTP server's old backup file name: ${FILENAME} has been deleted"
        else
            log "Failed to delete FTP server's old backup file: ${FILENAME}"
        fi
    fi
}

# ------------------------------------------------------------------------------
# 清理本地及远端过期备份文件（基于 find -mtime，同时清理残留 SQL）
# ------------------------------------------------------------------------------
clean_up_files() {
    log "Starting cleanup of old backup files..."

    # 1. 查找并删除 LOCALDIR 下超过 LOCALAGEDAILIES 天的历史备份文件（支持 .tgz, .enc, .tar.gz）
    if [ -d "${LOCALDIR}" ]; then
        while IFS= read -r -d '' file; do
            local basename_file
            basename_file=$(basename "$file")
            rm -f "$file"
            log "Local old backup file deleted: ${basename_file}"
            
            # 若开启远端删除，同步清理 Google Drive 与 FTP 上的同名旧备份
            delete_gdrive_file "${basename_file}"
            delete_ftp_file "${basename_file}"
        done < <(find "${LOCALDIR}" -maxdepth 1 \( -name "*.tgz" -o -name "*.enc" -o -name "*.tar.gz" \) -type f -mtime +"${LOCALAGEDAILIES}" -print0 2>/dev/null)
    fi

    # 2. 清理临时目录中遗留超过 1 天的 SQL 转储文件
    if [ -d "${TEMPDIR}" ]; then
        find "${TEMPDIR}" -maxdepth 1 -name "*.sql" -type f -mtime +1 -delete 2>/dev/null || true
    fi

    log "Cleanup completed"
}

# ------------------------------------------------------------------------------
# 退出兜底处理函数 (Exit Trap)
# 无论脚本正常结束或异常中断，均能清理临时 SQL 并保障本地旧备份清理执行
# ------------------------------------------------------------------------------
cleanup_on_exit() {
    local exit_code=$?
    # 强制清理临时 sql 文件
    rm -f "${TEMPDIR}"/*.sql 2>/dev/null || true
    # 兜底执行本地旧备份清理，防止因异常退出导致旧备份不断累积满盘
    clean_up_files >/dev/null 2>&1 || true
    if [ $exit_code -ne 0 ]; then
        log "Backup script ended with error status ${exit_code}."
    fi
}

# ------------------------------------------------------------------------------
# 主流程执行 (Main Execution)
# ------------------------------------------------------------------------------
trap cleanup_on_exit EXIT
STARTTIME=$(date +%s)

# 确保本地备份和临时目录存在
[ ! -d "${LOCALDIR}" ] && mkdir -p ${LOCALDIR}
[ ! -d "${TEMPDIR}" ] && mkdir -p ${TEMPDIR}

log "Backup progress start"

# 1. 检查依赖与环境
check_commands

# 2. 导出数据库
mysql_backup

# 3. 生成归档并加密
start_backup
log "Backup progress complete"

# 4. 上传至异地存储
log "Upload progress start"
rclone_upload
ftp_upload
log "Upload progress complete"

# 5. 执行清理
log "Cleaning up"
clean_up_files

ENDTIME=$(date +%s)
DURATION=$((ENDTIME - STARTTIME))
log "All done"
log "Backup and transfer completed in ${DURATION} seconds"

