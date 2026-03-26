#!/usr/bin/env bash

# 终端遇到错误时立即退出
set -e

# 软路由配置
ROUTER_IP="192.168.50.1"
ROUTER_USER="root"
# 根据你的映射，提取出宿主机的实际路径
HA_CONFIG_DIR="/mnt/nvme0n1-5/Configs/HomeAssistant"
CUSTOM_COMPONENTS_DIR="${HA_CONFIG_DIR}/custom_components"

# 本地代码路径
LOCAL_INTEGRATION_DIR="/Users/ian/retro-monitor/homeassistant/custom_components/retro_monitor"

echo "=================================================="
echo "🚀 开始部署 Retro Monitor 集成到 ${ROUTER_IP}"
echo "=================================================="

# 1. 确保远程 custom_components 目录存在
echo "📁 检查 / 创建远程 custom_components 目录..."
ssh "${ROUTER_USER}@${ROUTER_IP}" "mkdir -p '${CUSTOM_COMPONENTS_DIR}'"

# 2. 使用 rsync 同步代码
# -a: 归档模式，保留权限等
# -v: 显示详细输出
# -z: 压缩传输
# --delete: 删除远程目标目录中多余的文件，保持严格一致
echo "🔄 同步代码文件..."
scp -r "${LOCAL_INTEGRATION_DIR}" "${ROUTER_USER}@${ROUTER_IP}:${CUSTOM_COMPONENTS_DIR}/"

# 3. 尝试重启 Home Assistant Docker 容器
# 假设你的容器名字叫 homeassistant，如果是其他名字，可能会提示找不到容器，需要手动重启
echo "♻️ 正在重启 Home Assistant 容器..."
ssh "${ROUTER_USER}@${ROUTER_IP}" "docker restart homeassistant || docker restart hass || docker restart home-assistant || echo '⚠️ 未能自动找到 HA 容器，请手动在软路由上重启 HA!'"

echo "=================================================="
echo "✅ 部署完成！"
echo "=================================================="
echo "现在你可以打开软路由的 Home Assistant 页面添加或重新加载该集成了。"
