#!/usr/bin/env bash
#
# Auto backup script
#
# Copyright (C) 2016 Teddysun <i@teddysun.com>
#
# URL: https://teddysun.com/469.html
#
# You must to modify the config before run it!!!
# Backup MySQL/MariaDB/Percona datebases, files and directories
# Backup file is encrypted with AES256-cbc with SHA1 message-digest (option)
# Auto transfer backup file to Google Drive (need install gdrive command) (option)
# Auto transfer backup file to FTP server (option)
# Auto delete Google Drive's or FTP server's remote file (option)
#

[[ $EUID -ne 0 ]] && echo "Error: This script must be run as root!" && exit 1

########## START OF CONFIG ##########

# Encrypt flag (true: encrypt, false: not encrypt)
ENCRYPTFLG=false

# WARNING: KEEP THE PASSWORD SAFE!!!
# The password used to encrypt the backup
# To decrypt backups made by this script, run the following command:
# openssl enc -aes256 -in [encrypted backup] -out decrypted_backup.tgz -pass pass:[backup password] -d -md sha1
BACKUPPASS="password"

# mysql username
MYSQL_ROOT_NAME=""

# OPTIONAL: If you want backup MySQL database, enter the MySQL root password below
MYSQL_ROOT_PASSWORD=""

# Below is a list of MySQL database name that will be backed up
# If you want backup ALL databases, leave it blank.
MYSQL_DATABASE_NAME[0]=""

# Directory to store backups
LOCALDIR="/home/backups/"

# Temporary directory used during backup creation
TEMPDIR="/home/backups/temp/"

# File to log the outcome of backups
LOGFILE="/home/backups/backup.log"

# Below is a list of files and directories that will be backed up in the tar backup
# For example:
# File: /data/www/default/test.tgz
# Directory: /data/www/default/test
BACKUP[0]="/opt/docker/chinesesubfinder/docker-compose.yml"
BACKUP[1]="/opt/docker/chinesesubfinder/config"
BACKUP[2]="/opt/docker/jellyfin/docker-compose.yml"
BACKUP[3]="/opt/docker/jellyfin/config/config"
BACKUP[4]="/opt/docker/nas-tools/docker-compose.yml"
BACKUP[5]="/opt/docker/nas-tools/config"
BACKUP[6]="/opt/docker/qinglong/docker-compose.yml"
BACKUP[7]="/opt/docker/qinglong/data"
BACKUP[8]="/opt/docker/study_xxqg/docker-compose.yml"
BACKUP[9]="/opt/docker/study_xxqg/config"
BACKUP[10]="/opt/aria2/aria2.conf"
BACKUP[11]="/opt/frp/frpc.toml"
BACKUP[12]="/etc/crontab"
BACKUP[13]="/usr/lib/systemd/system"
BACKUP[14]="/root/.bashrc"
BACKUP[15]="/etc/hostname"
BACKUP[16]="/etc/vsftpd.conf"
BACKUP[17]="/etc/env_addon"
BACKUP[18]="/etc/nginx/conf.d"
BACKUP[19]="/opt/docker/immich-app/docker-compose.yml"
BACKUP[20]="/opt/docker/immich-app/.env"
BACKUP[21]="/etc/systemd/system"

# Number of days to store daily local backups (default 7 days)
LOCALAGEDAILIES="7"

# Delete Googole Drive's & FTP server's remote file flag (true: delete, false: not delete)
DELETE_REMOTE_FILE_FLG=true

# Upload to google drive flag (true: upload, false: not upload)
RCLONE_FLG=false

# Rclone remote name
RCLONE_NAME=""

# Rclone remote folder name (default "")
RCLONE_FOLDER=""

# Upload to FTP server flag (true: upload, false: not upload)
FTP_FLG=true

# FTP server
# OPTIONAL: If you want upload to FTP server, enter the Hostname or IP address below
FTP_HOST=${ftp_host}

# FTP username
# OPTIONAL: If you want upload to FTP server, enter the FTP username below
FTP_USER=${ftp_user}

# FTP password
# OPTIONAL: If you want upload to FTP server, enter the username's password below
FTP_PASS=${ftp_passwd}

# FTP server remote folder
# OPTIONAL: If you want upload to FTP server, enter the FTP remote folder below
# For example: public_html
FTP_DIR="UbuntuBackUp"

########## END OF CONFIG ##########



# Date & Time
DAY=$(date +%d)
MONTH=$(date +%m)
YEAR=$(date +%C%y)
BACKUPDATE=$(date +%Y%m%d%H%M%S)
# Backup file name
TARFILE="${LOCALDIR}""$(hostname)"_"${BACKUPDATE}".tgz
# Encrypted backup file name
ENC_TARFILE="${TARFILE}.enc"
# Backup MySQL dump file name
SQLFILE="${TEMPDIR}mysql_${BACKUPDATE}.sql"

log() {
#    echo "$(date "+%Y-%m-%d %H:%M:%S")" "$1"
    echo -e "$(date "+%Y-%m-%d %H:%M:%S")" "$1" >> ${LOGFILE}
}

# Check for list of mandatory binaries
check_commands() {
    # This section checks for all of the binaries used in the backup
    BINARIES=( cat cd du date dirname echo openssl mysql mysqldump pwd rm tar )
    
    # Iterate over the list of binaries, and if one isn't found, abort
    for BINARY in "${BINARIES[@]}"; do
        if [ ! "$(command -v "$BINARY")" ]; then
            log "$BINARY is not installed. Install it and try again"
            exit 1
        fi
    done

    # check gdrive command
    RCLONE_COMMAND=false
    if [ "$(command -v "rclone")" ]; then
        RCLONE_COMMAND=true
    fi

    # check ftp command
    if ${FTP_FLG}; then
        if [ ! "$(command -v "ftp")" ]; then
            log "ftp is not installed. Install it and try again"
            exit 1
        fi
    fi
}

calculate_size() {
    local file_name=$1
    local file_size=$(du -h $file_name 2>/dev/null | awk '{print $1}')
    if [ "x${file_size}" = "x" ]; then
        echo "unknown"
    else
        echo "${file_size}"
    fi
}

# Backup MySQL databases
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
            mysqldump -u ${MYSQL_ROOT_NAME} -p${MYSQL_ROOT_PASSWORD} --all-databases > "${SQLFILE}" 2>/dev/null
            if [ $? -ne 0 ]; then
                log "MySQL all databases backup failed"
                exit 1
            fi
            log "MySQL all databases dump file name: ${SQLFILE}"
            #Add MySQL backup dump file to BACKUP list
            BACKUP=(${BACKUP[*]} ${SQLFILE})
        else
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
                #Add MySQL backup dump file to BACKUP list
                BACKUP=(${BACKUP[*]} ${DBFILE})
            done
        fi
        log "MySQL dump completed"
    fi
}

start_backup() {
    [ "${BACKUP[*]}" == "" ] && echo "Error: You must to modify the [$(basename $0)] config before run it!" && exit 1

    log "Tar backup file start"
    tar -zcPf ${TARFILE} ${BACKUP[*]}
    if [ $? -gt 1 ]; then
        log "Tar backup file failed"
        exit 1
    fi
    log "Tar backup file completed"

    # Encrypt tar file
    if ${ENCRYPTFLG}; then
        log "Encrypt backup file start"
        openssl enc -aes-256-cbc -md sha512 -pbkdf2 -pass pass:${BACKUPPASS} -in "${TARFILE}" -out "${ENC_TARFILE}"
        log "Encrypt backup file completed"

        # Delete unencrypted tar
        log "Delete unencrypted tar file: ${TARFILE}"
        rm -f ${TARFILE}
    fi

    # Delete MySQL temporary dump file
    for sql in `ls ${TEMPDIR}*.sql`
    do
        log "Delete MySQL temporary dump file: ${sql}"
        rm -f ${sql}
    done

    if ${ENCRYPTFLG}; then
        OUT_FILE="${ENC_TARFILE}"
    else
        OUT_FILE="${TARFILE}"
    fi
    log "File name: ${OUT_FILE}, File size: `calculate_size ${OUT_FILE}`"
}

# Transfer backup file to Google Drive
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

# Tranferring backup file to FTP server
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

# Get file date
get_file_date() {
    #Approximate a 30-day month and 365-day year
    DAYS=$(( $((10#${YEAR}*365)) + $((10#${MONTH}*30)) + $((10#${DAY})) ))

    unset FILEYEAR FILEMONTH FILEDAY FILEDAYS FILEAGE
    FILEYEAR=$(echo "$1" | cut -d_ -f2 | cut -c 1-4)
    FILEMONTH=$(echo "$1" | cut -d_ -f2 | cut -c 5-6)
    FILEDAY=$(echo "$1" | cut -d_ -f2 | cut -c 7-8)

    if [[ "${FILEYEAR}" && "${FILEMONTH}" && "${FILEDAY}" ]]; then
        #Approximate a 30-day month and 365-day year
        FILEDAYS=$(( $((10#${FILEYEAR}*365)) + $((10#${FILEMONTH}*30)) + $((10#${FILEDAY})) ))
        FILEAGE=$(( 10#${DAYS} - 10#${FILEDAYS} ))
        return 0
    fi

    return 1
}

# Delete Google Drive's old backup file
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

# Delete FTP server's old backup file
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

# Clean up old file
clean_up_files() {
    cd ${LOCALDIR} || exit

    if ${ENCRYPTFLG}; then
        LS=($(ls *.enc))
    else
        LS=($(ls *.tgz))
    fi
    for f in ${LS[@]}; do
        get_file_date ${f}
        if [ $? -eq 0 ]; then
            if [[ ${FILEAGE} -gt ${LOCALAGEDAILIES} ]]; then
                rm -f ${f}
                log "Old backup file name: ${f} has been deleted"
                delete_gdrive_file ${f}
                delete_ftp_file ${f}
            fi
        fi
    done
}

# Main progress
STARTTIME=$(date +%s)

# Check if the backup folders exist and are writeable
[ ! -d "${LOCALDIR}" ] && mkdir -p ${LOCALDIR}
[ ! -d "${TEMPDIR}" ] && mkdir -p ${TEMPDIR}

log "Backup progress start"
check_commands
mysql_backup
start_backup
log "Backup progress complete"

log "Upload progress start"
rclone_upload
ftp_upload
log "Upload progress complete"

log "Cleaning up"
clean_up_files

ENDTIME=$(date +%s)
DURATION=$((ENDTIME - STARTTIME))
log "All done"
log "Backup and transfer completed in ${DURATION} seconds"
