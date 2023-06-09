#!/usr/bin/env bash

# must install sshpass first "apt install sshpass"

LOGFILE="/home/backups/backup_openwrt.log"

log() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S")" "$1" >> ${LOGFILE}
}

# Generate/update backup
sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%Y%m%d%H%M%S).tar.gz'
if [ "$?" -ne 0 ]; then
    log "backup failed."
    exit 1
fi
log "backup done."

# Download backup
sshpass -p $router_passwd sftp root@$router_hostname << EOF
get /tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup
EOF
if [ "$?" -ne 0 ]; then
    log "transfer to cloud failed."
    exit 1
fi
log "transfer done."

sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; rm /tmp/backup-*'
if [ "$?" -ne 0 ]; then
    log "remove file failed."
    exit 1
fi
log "remove done."
