#!/usr/bin/env bash

# must install sshpass first "apt install sshpass"

LOGFILE="/home/backups/backup_openwrt.log"

# Generate/update backup
sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%Y%m%d%H%M%S).tar.gz'
if [ "$?" -ne 0 ]; then
    echo "backup failed." >> ${LOGFILE}
    exit 1
fi
echo "backup done." >> ${LOGFILE}

# Download backup
sshpass -p $router_passwd sftp root@$router_hostname << EOF
get /tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup
EOF
if [ "$?" -ne 0 ]; then
    echo "transfer to cloud failed." >> ${LOGFILE}
    exit 1
fi
echo "transfer done." >> ${LOGFILE}

sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; rm /tmp/backup-*'
if [ "$?" -ne 0 ]; then
    echo "remove file failed." >> ${LOGFILE}
    exit 1
fi
echo "remove done." >> ${LOGFILE}
