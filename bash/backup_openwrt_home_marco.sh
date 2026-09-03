#!/usr/bin/env bash
# ==============================================================================
# 脚本名称: backup_openwrt_home_marco.sh
# 脚本说明: OpenWrt 路由器配置自动备份脚本
# 执行流程: 
#   1. 通过 SSH 在 OpenWrt 路由器上调用 sysupgrade 生成配置备份归档
#   2. 通过 SCP 下载备份归档到本地临时目录
#   3. 通过 Curl 上传备份到远程 NAS FTP 服务器
#   4. 清理两端临时文件并清理 NAS FTP 超过 7 天的历史备份
# ==============================================================================

# 自动加载环境变量文件
if [ -f "/etc/env_addon" ]; then
    set -a
    . /etc/env_addon
    set +a
fi

# ------------------------------------------------------------------------------
# 配置区域 (Configuration)
# ------------------------------------------------------------------------------
# OpenWrt 路由器连接信息
ROUTER_IP="${router_ip:-openwrt.home.marco}"
ROUTER_USER="${router_user:-root}"
ROUTER_PASS="${router_passwd:-}"

# 远程 FTP 服务器连接信息
FTP_HOST="${ftp_host:-nas.home.marco}"
FTP_USER="${ftp_user:-marco}"
FTP_PASS="${ftp_passwd:-}"
FTP_DIR="nas-backup/OpenwrtBackup"
KEEP_DAYS=7

# 本地临时路径与日志设置
LOCAL_BACKUP_DIR="/tmp/openwrt_backups"          # 本地临时中转目录
LOGFILE="/home/backups/backup_openwrt.log"      # 执行日志输出路径
DATE_STR=$(date +%Y%m%d%H%M%S)                   # 时间戳标识
BACKUP_FILENAME="backup-openwrt-${DATE_STR}.tar.gz" # 备份文件名
REMOTE_TEMP_PATH="/tmp/${BACKUP_FILENAME}"       # 路由器端生成的临时备份路径

# 确保本地临时目录存在
mkdir -p "$LOCAL_BACKUP_DIR"
mkdir -p "$(dirname "$LOGFILE")"

# ------------------------------------------------------------------------------
# 日志记录辅助函数
# ------------------------------------------------------------------------------
log() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S") [INFO] $1" >> "${LOGFILE}"
    echo "[INFO] $1"
}

error() {
    echo -e "$(date "+%Y-%m-%d %H:%M:%S") [ERROR] $1" >> "${LOGFILE}"
    echo "[ERROR] $1" >&2
}

# ------------------------------------------------------------------------------
# 退出捕获与清理函数 (Exit Trap)
# 无论脚本正常结束、发生异常退出或被外部信号中断，均能保证删除两端临时文件
# ------------------------------------------------------------------------------
cleanup() {
    # 1. 尝试删除 OpenWrt 路由器上的临时备份文件
    if [ -n "$REMOTE_TEMP_PATH" ]; then
        sshpass -p "$ROUTER_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP" "rm -f $REMOTE_TEMP_PATH" >/dev/null 2>&1 || true
    fi
    # 2. 清理本次下载到本地的临时文件
    if [ -f "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME" ]; then
        rm -f "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME"
    fi
    # 3. 清理本地临时目录中可能遗留的超过 1 天的历史临时备份文件
    if [ -d "$LOCAL_BACKUP_DIR" ]; then
        find "$LOCAL_BACKUP_DIR" -maxdepth 1 -name "backup-openwrt-*.tar.gz" -type f -mtime +1 -delete >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# ------------------------------------------------------------------------------
# 步骤 1: 在 OpenWrt 路由器上生成配置备份
# (备份机制说明: sysupgrade -b 会自动打包系统核心配置 + /etc/sysupgrade.conf 中的自定义路径)
# ------------------------------------------------------------------------------
log "Starting OpenWrt backup process..."

# 确保 OpenWrt 端的 /etc/sysupgrade.conf 包含关键自定义路径 (/etc/v2ray/, /etc/ethers, /etc/firewall.user 等)
# 并在备份前动态导出当前已安装的软件包清单 (/etc/installed_packages.txt)，确保灾难恢复时可完整重装软件包
sshpass -p "$ROUTER_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP" \
    "for item in '/etc/v2ray/' '/etc/ethers' '/etc/firewall.user' '/etc/installed_packages.txt'; do grep -qxF \"\$item\" /etc/sysupgrade.conf 2>/dev/null || echo \"\$item\" >> /etc/sysupgrade.conf; done; opkg list-installed > /etc/installed_packages.txt 2>/dev/null || true; umask go=; sysupgrade -b $REMOTE_TEMP_PATH"

if [ "$?" -ne 0 ]; then
    error "Failed to generate backup on OpenWrt."
    exit 1
fi
log "Backup generated successfully on router: $REMOTE_TEMP_PATH"

# ------------------------------------------------------------------------------
# 步骤 2: 将备份从 OpenWrt 下载到本地机器
# ------------------------------------------------------------------------------
sshpass -p "$ROUTER_PASS" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$ROUTER_USER@$ROUTER_IP:$REMOTE_TEMP_PATH" "$LOCAL_BACKUP_DIR/"

if [ "$?" -ne 0 ]; then
    error "Failed to download backup from OpenWrt."
    exit 1
fi
log "Backup downloaded to: $LOCAL_BACKUP_DIR/$BACKUP_FILENAME"

# ------------------------------------------------------------------------------
# 步骤 3: 上传备份到远程 FTP 服务器
# ------------------------------------------------------------------------------
log "Uploading to FTP server..."
curl --silent --show-error --fail --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" \
    -T "$LOCAL_BACKUP_DIR/$BACKUP_FILENAME" \
    "ftp://$FTP_HOST/$FTP_DIR/"

if [ "$?" -ne 0 ]; then
    error "Failed to upload to FTP server."
    exit 1
else
    log "Backup uploaded successfully to ftp://$FTP_HOST/$FTP_DIR/$BACKUP_FILENAME"
fi

# ------------------------------------------------------------------------------
# 步骤 4: 清理 FTP 上超过保留天数的旧备份
# ------------------------------------------------------------------------------
log "Checking FTP for old OpenWrt backups (older than ${KEEP_DAYS} days)..."
ftp_files=$(curl --silent --list-only -u "$FTP_USER:$FTP_PASS" "ftp://$FTP_HOST/$FTP_DIR/" 2>/dev/null || true)
now_sec=$(date +%s)
for remote_file in $ftp_files; do
    if [[ "$remote_file" =~ backup-openwrt-([0-9]{8})[0-9]*\.tar\.gz ]]; then
        file_date="${BASH_REMATCH[1]}"
        file_sec=$(date -d "${file_date}" +%s 2>/dev/null || true)
        if [ -n "$file_sec" ]; then
            diff_days=$(( (now_sec - file_sec) / 86400 ))
            if [ $diff_days -gt $KEEP_DAYS ]; then
                log "Deleting old OpenWrt FTP file: $remote_file (Age: ${diff_days} days)"
                curl --silent -u "$FTP_USER:$FTP_PASS" "ftp://$FTP_HOST/$FTP_DIR/" -Q "DELE $remote_file" >/dev/null 2>&1 || true
            fi
        fi
    fi
done

log "OpenWrt backup process completed successfully."
