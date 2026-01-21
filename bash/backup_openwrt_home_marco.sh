#!/usr/bin/env bash

# Prerequisites:
# 1. sshpass: apt install sshpass
# 2. curl: apt install curl

# --- Configuration ---
# OpenWrt Router Details
ROUTER_IP=$router_ip       # Replace with your router IP
ROUTER_USER=$router_user
ROUTER_PASS=$router_passwd # Consider using SSH keys instead of password for security

# FTP Server Details
FTP_HOST=$ftp_host
FTP_USER=$ftp_user
FTP_PASS=$ftp_passwd
FTP_DIR="nas-backup/OpenwrtBackup"    # Remote directory on FTP server

# Local Settings
LOCAL_BACKUP_DIR="/tmp/openwrt_backups"
LOGFILE="/home/backups/backup_openwrt.log"
DATE_STR=$(date +%Y%m%d%H%M%S)
BACKUP_FILENAME="backup-${HOSTNAME}-${DATE_STR}.tar.gz"
REMOTE_TEMP_PATH="/tmp/${BACKUP_FILENAME}"

# Ensure local backup directory exists
mkdir -p "$LOCAL_BACKUP_DIR"

log() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S") [INFO] $1" >> "${LOGFILE}"
    echo "[INFO] $1"
}

error() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S") [ERROR] $1" >> "${LOGFILE}"
    echo "[ERROR] $1" >&2
}

# --- Step 1: Generate Backup on OpenWrt ---
log "Starting OpenWrt backup process..."
sshpass -p "$ROUTER_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP" \
    "umask go=; sysupgrade -b $REMOTE_TEMP_PATH"

if [ "$?" -ne 0 ]; then
    error "Failed to generate backup on OpenWrt."
    exit 1
fi
log "Backup generated successfully on router: $REMOTE_TEMP_PATH"

# --- Step 2: Download Backup to Local Machine ---
sshpass -p "$ROUTER_PASS" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP:$REMOTE_TEMP_PATH" "$LOCAL_BACKUP_DIR/"

if [ "$?" -ne 0 ]; then
    error "Failed to download backup from OpenWrt."
    # Attempt cleanup on router even if download failed
    sshpass -p "$ROUTER_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP" "rm -f $REMOTE_TEMP_PATH"
    exit 1
fi
log "Backup downloaded to: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME"

# --- Step 3: Upload to FTP Server ---
# Ensure the remote directory exists (optional, some servers might error if it already exists or if parent dirs missing)
# curl --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" "ftp://$FTP_HOST/$FTP_DIR/"

log "Uploading to FTP server..."
curl --silent --show-error --fail -u "$FTP_USER:$FTP_PASS" \
    -T "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME" \
    "ftp://$FTP_HOST/$FTP_DIR/"

if [ "$?" -ne 0 ]; then
    error "Failed to upload to FTP server."
else
    log "Backup uploaded successfully to ftp://$FTP_HOST/$FTP_DIR/$BACKUP_FILENAME"
fi

# --- Step 4: Cleanup ---
# Remove file from OpenWrt
sshpass -p "$ROUTER_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP" "rm -f $REMOTE_TEMP_PATH"
if [ "$?" -eq 0 ]; then
    log "Remote temp file removed."
fi

# Remove local file
rm -f "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
log "Local temp file removed. Process complete."
