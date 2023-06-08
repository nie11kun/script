#!/usr/bin/env bash

# script based on instructions from:
# https://openwrt.org/docs/guide-user/troubleshooting/backup_restore

router_hostname=openwrt.home.marco
router_passwd=Pmz3qUxWkahy

# Generate/update backup
sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz'

# Download backup
sshpass -p $router_passwd scp root@$router_hostname:/tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup

sshpass -p $router_passwd ssh root@$router_hostname 'umask go=; rm /tmp/backup-*'
