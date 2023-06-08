#!/usr/bin/env bash

# script based on instructions from:
# https://openwrt.org/docs/guide-user/troubleshooting/backup_restore

router_hostname=openwrt.home.marco
router_passwd=Pmz3qUxWkahy

# Generate/update backup
sshpass -p Pmz3qUxWkahy ssh root@openwrt.home.marco 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz'

# Download backup
#sshpass -p $router_passwd scp root@openwrt.home.marco -p "$router_passwd":/tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup

#sshpass -p $router_passwd ssh root@openwrt.home.marco 'umask go=; rm /tmp/backup-*'
