#!/usr/bin/env bash

# must install sshpass first "apt install sshpass"

# Generate/update backup
sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz'
if [ "$?" -ne 0 ]; then
    echo "backup failed."
    exit 1
fi

# Download backup
sshpass -p $router_passwd scp root@$router_hostname:/tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup
if [ "$?" -ne 0 ]; then
    echo "transfer to cloud failed."
    exit 1
fi

sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; rm /tmp/backup-*'
if [ "$?" -ne 0 ]; then
    echo "remove file failed."
    exit 1
fi
