#!/usr/bin/env bash

# must install sshpass first "apt install sshpass"

# Generate/update backup
sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz'
if [ "$?" -ne 0 ]; then
    echo "backup failed."
    exit 1
fi
echo "backup done."

# Download backup
sshpass -p $router_passwd sftp root@$router_hostname << EOF
get /tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup
EOF
if [ "$?" -ne 0 ]; then
    echo "transfer to cloud failed."
    exit 1
fi
echo "transfer done."

sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; rm /tmp/backup-*'
if [ "$?" -ne 0 ]; then
    echo "remove file failed."
    exit 1
fi
echo "remove done."
