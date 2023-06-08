#!/usr/bin/env bash

# script based on instructions from:
# https://openwrt.org/docs/guide-user/troubleshooting/backup_restore

router_hostname=openwrt.home.marco

# Generate/update backup
ssh "$router_hostname" 'umask go=; sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz'


# Download backup
scp root@"$router_hostname":/tmp/backup-*.tar.gz /mnt/h99_home/ftp/OpenwrtBackup

ssh "$router_hostname" 'umask go=; rm /tmp/backup-*'
