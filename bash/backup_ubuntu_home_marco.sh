#!/usr/bin/env bash
#
# Auto backup script
#
# Copyright (C) 2016 Teddysun <i@teddysun.com>
# Optimized by Assistant
#
# URL: https://teddysun.com/469.html
#
# Features:
# - Backup MySQL/MariaDB/Percona databases, files, and directories
# - Backup file encryption (AES256-cbc)
# - Transfer to Google Drive (requires rclone)
# - Transfer to FTP server (requires curl)
# - Auto-delete old backups (local and remote)
#

# Stop on error
set -e

[[ $EUID -ne 0 ]] && echo "Error: This script must be run as root!" && exit 1

########## START OF CONFIG ##########

# Encrypt flag (true: encrypt, false: not encrypt)
ENCRYPTFLG=false

# WARNING: KEEP THE PASSWORD SAFE!!!
# The password used to encrypt the backup
BACKUPPASS="password"

# MySQL configuration
MYSQL_ROOT_NAME=""
MYSQL_ROOT_PASSWORD=""
# List of databases to backup (leave empty for all)
MYSQL_DATABASE_NAME=()

# Directory to store backups
LOCALDIR="/home/backups/"
TEMPDIR="/home/backups/temp/"
LOGFILE="/home/backups/backup.log"

# Backup List
BACKUP=(
    "/opt/docker/chinesesubfinder/docker-compose.yml"
    "/opt/docker/chinesesubfinder/config"
    "/opt/docker/jellyfin/docker-compose.yml"
    "/opt/docker/jellyfin/config/config"
    "/opt/docker/nas-tools/docker-compose.yml"
    "/opt/docker/nas-tools/config"
    "/opt/docker/qinglong/docker-compose.yml"
    "/opt/docker/qinglong/data"
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
    "/opt/docker/immich-app/docker-compose.yml"
    "/opt/docker/immich-app/.env"
    "/opt/docker/pixman/docker-compose.yml"
    "/etc/systemd/system"
)

# Days to keep local backups
LOCALAGEDAILIES="7"

# Remote deletion flag
DELETE_REMOTE_FILE_FLG=true

# Google Drive (Rclone)
RCLONE_FLG=false
RCLONE_NAME=""
RCLONE_FOLDER=""

# FTP Server
FTP_FLG=true
FTP_HOST="${ftp_host}"
FTP_USER="${ftp_user}"
FTP_PASS="${ftp_passwd}"
FTP_DIR="UbuntuBackUp"

########## END OF CONFIG ##########

# Date & Time variables
BACKUPDATE=$(date +%Y%m%d%H%M%S)
HOSTNAME_FULL=$(hostname)

# File names
TARFILE="${LOCALDIR}${HOSTNAME_FULL}_${BACKUPDATE}.tgz"
ENC_TARFILE="${TARFILE}.enc"
SQLFILE="${TEMPDIR}mysql_${BACKUPDATE}.sql"

log() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S") $1" >> "${LOGFILE}"
}

check_commands() {
    local BINARIES=( cat cd du date dirname echo openssl mysql mysqldump pwd rm tar find )
    for BINARY in "${BINARIES[@]}"; do
        if ! command -v "$BINARY" >/dev/null 2>&1; then
            log "ERROR: $BINARY is not installed. Install it and try again."
            exit 1
        fi
    done

    # Check rclone
    RCLONE_AVAILABLE=false
    if command -v "rclone" >/dev/null 2>&1; then
        RCLONE_AVAILABLE=true
    fi

    # Check curl for FTP
    if ${FTP_FLG}; then
        if ! command -v "curl" >/dev/null 2>&1; then
            log "ERROR: curl is not installed. Install it and try again for FTP support."
            exit 1
        fi
    fi
}

mysql_backup() {
    if [ -z "${MYSQL_ROOT_PASSWORD}" ]; then
        log "MySQL root password not set, skipping MySQL backup."
        return
    fi
    
    log "MySQL dump start"
    
    # Test connection
    if ! mysql -u "${MYSQL_ROOT_NAME}" -p"${MYSQL_ROOT_PASSWORD}" -e "exit" 2>/dev/null; then
        log "ERROR: MySQL root password incorrect."
        exit 1
    fi

    if [ ${#MYSQL_DATABASE_NAME[@]} -eq 0 ]; then
        mysqldump -u "${MYSQL_ROOT_NAME}" -p"${MYSQL_ROOT_PASSWORD}" --all-databases > "${SQLFILE}" 2>/dev/null
        log "MySQL all databases dump: ${SQLFILE}"
        BACKUP+=("${SQLFILE}")
    else
        for db in "${MYSQL_DATABASE_NAME[@]}"; do
            DBFILE="${TEMPDIR}${db}_${BACKUPDATE}.sql"
            mysqldump -u "${MYSQL_ROOT_NAME}" -p"${MYSQL_ROOT_PASSWORD}" "${db}" > "${DBFILE}" 2>/dev/null
            log "MySQL database [${db}] dump: ${DBFILE}"
            BACKUP+=("${DBFILE}")
        done
    fi
    log "MySQL dump completed"
}

create_backup_archive() {
    local FINAL_FILE

    [ ${#BACKUP[@]} -eq 0 ] && log "ERROR: No files to backup." && exit 1

    log "Creating tar archive..."
    # Use -P (absolute names) and keep existing logic
    if ! tar -zcPf "${TARFILE}" "${BACKUP[@]}"; then
        log "ERROR: Tar backup failed."
        exit 1
    fi
    log "Tar backup completed: ${TARFILE}"

    if ${ENCRYPTFLG}; then
        log "Encrypting backup..."
        openssl enc -aes-256-cbc -md sha512 -pbkdf2 -pass "pass:${BACKUPPASS}" -in "${TARFILE}" -out "${ENC_TARFILE}"
        log "Encryption completed: ${ENC_TARFILE}"
        
        rm -f "${TARFILE}"
        FINAL_FILE="${ENC_TARFILE}"
    else
        FINAL_FILE="${TARFILE}"
    fi

    # Cleanup temp SQL files
    rm -f "${TEMPDIR}"/*.sql 2>/dev/null || true

    # Export for upload functions
    export UPLOAD_FILE="${FINAL_FILE}"
    local SIZE
    SIZE=$(du -h "${UPLOAD_FILE}" | awk '{print $1}')
    log "Backup ready: ${UPLOAD_FILE} (Size: ${SIZE})"
}

rclone_upload() {
    if ${RCLONE_FLG} && ${RCLONE_AVAILABLE}; then
        [ -z "${RCLONE_NAME}" ] && log "ERROR: RCLONE_NAME empty." && return 1
        
        log "Uploading to Google Drive: ${RCLONE_NAME}:${RCLONE_FOLDER}"
        
        # Ensure directory exists (mkdir is idempotent in rclone usually, but nice to be explicit if needed)
        if [ -n "${RCLONE_FOLDER}" ]; then
            rclone mkdir "${RCLONE_NAME}:${RCLONE_FOLDER}" >/dev/null 2>&1 || true
        fi
        
        if rclone copy "${UPLOAD_FILE}" "${RCLONE_NAME}:${RCLONE_FOLDER}" >> "${LOGFILE}" 2>&1; then
             log "Google Drive upload success."
        else
             log "ERROR: Google Drive upload failed."
             return 1
        fi
    fi
}

ftp_upload() {
    if ${FTP_FLG}; then
        log "Uploading to FTP: ftps://${FTP_HOST}/${FTP_DIR}"
        
        # Use curl for upload. --ftp-create-dirs handles the directory creation.
        # -T uploads the file.
        # -u user:pass
        # -k (insecure) if you use strict SSL/TLS certificates and they are self-signed, 
        # but standard ftp often doesn't need it. 
        # Using ftp:// scheme.
        
        local FILENAME
        FILENAME=$(basename "${UPLOAD_FILE}")
        
        if curl --fail --silent --show-error --ftp-create-dirs \
             -T "${UPLOAD_FILE}" \
             -u "${FTP_USER}:${FTP_PASS}" \
             "ftp://${FTP_HOST}/${FTP_DIR}/"; then
            log "FTP upload success."
        else
            log "ERROR: FTP upload failed."
            return 1
        fi
    fi
}

# Legacy logic support for remote cleanup based on filename date parsing
get_file_date_legacy() {
    local fname=$1
    # Filename format: hostname_YYYYMMDDHHMMSS.tgz
    # Parsing date from format
    local date_part
    date_part=$(echo "$fname" | grep -oE '[0-9]{14}' | head -1)

    if [ -z "$date_part" ]; then
        return 1
    fi
    
    local file_ts
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS date
        file_ts=$(date -j -f "%Y%m%d%H%M%S" "$date_part" +%s 2>/dev/null)
    else
        # Linux date
        file_ts=$(date -d "${date_part:0:8} ${date_part:8:2}:${date_part:10:2}:${date_part:12:2}" +%s 2>/dev/null)
    fi

    if [ -z "$file_ts" ]; then
        return 1
    fi

    local current_ts
    current_ts=$(date +%s)
    local diff=$(( (current_ts - file_ts) / 86400 ))

    if [ "$diff" -gt "$LOCALAGEDAILIES" ]; then
        return 0 # True, it is old
    else
        return 1 # False, it is not old
    fi
}

clean_local_files() {
    cd "${LOCALDIR}" || exit
    log "Cleaning up local files older than ${LOCALAGEDAILIES} days..."
    
    # Modern find command
    # Looks for .tgz or .enc files older than N days
    find "${LOCALDIR}" -maxdepth 1 \( -name "*.tgz" -o -name "*.enc" \) -type f -mtime +"${LOCALAGEDAILIES}" -print -delete | while read -r file; do
        log "Deleted local old backup: $file"
    done
}

clean_remote_files() {
    if ! ${DELETE_REMOTE_FILE_FLG}; then return; fi

    # Rclone Cleanup
    if ${RCLONE_FLG} && ${RCLONE_AVAILABLE}; then
        # List files, filter by regex for backup format, check date
        # This is expensive, so we only try if we really want to supported it.
        # The original script deleted the specific file that was locally deleted.
        # We will iterate remote files and check dates since we are now decoupled.
        
        log "Checking Google Drive for old files..."
        # Get list of files
        rclone lsf "${RCLONE_NAME}:${RCLONE_FOLDER}" | while read -r remote_file; do
            if get_file_date_legacy "$remote_file"; then
                 log "Deleting old Drive file: $remote_file"
                 rclone delete "${RCLONE_NAME}:${RCLONE_FOLDER}/$remote_file"
            fi
        done
    fi

    # FTP Cleanup
    if ${FTP_FLG}; then
        log "Checking FTP for old files..."
        # List files using curl
        # curl -l lists filenames only
        local ftp_files
        ftp_files=$(curl --silent --list-only -u "${FTP_USER}:${FTP_PASS}" "ftp://${FTP_HOST}/${FTP_DIR}/" || true)
        
        for remote_file in $ftp_files; do
            if get_file_date_legacy "$remote_file"; then
                 log "Deleting old FTP file: $remote_file"
                 # Delete using curl -Q (quote command)
                 curl --silent -u "${FTP_USER}:${FTP_PASS}" "ftp://${FTP_HOST}/${FTP_DIR}/" -Q "DELE $remote_file" || log "Failed to delete $remote_file"
            fi
        done
    fi
}


# Main Execution
STARTTIME=$(date +%s)

[ ! -d "${LOCALDIR}" ] && mkdir -p "${LOCALDIR}"
[ ! -d "${TEMPDIR}" ] && mkdir -p "${TEMPDIR}"

log "=== Backup Job Started ==="

check_commands
mysql_backup
create_backup_archive

log "=== Uploading ==="
rclone_upload
ftp_upload

log "=== Cleanup ==="
clean_local_files
clean_remote_files

ENDTIME=$(date +%s)
DURATION=$((ENDTIME - STARTTIME))
log "=== All Done (Duration: ${DURATION}s) ==="

