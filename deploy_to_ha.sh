#!/usr/bin/env bash

# 终端遇到错误时立即退出
set -e

# 软路由 / Home Assistant 配置。公开仓库中保留为可覆盖的示例值。
ROUTER_IP="${ROUTER_IP:-<router-ip>}"
ROUTER_USER="${ROUTER_USER:-root}"
HA_CONFIG_DIR="${HA_CONFIG_DIR:-/path/to/homeassistant/config}"
CUSTOM_COMPONENTS_DIR="${HA_CONFIG_DIR}/custom_components"

# 本地代码路径
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOCAL_INTEGRATION_DIR="${REPO_ROOT}/homeassistant/custom_components/retro_monitor"

if [ "${ROUTER_IP}" = "<router-ip>" ] || [ "${HA_CONFIG_DIR}" = "/path/to/homeassistant/config" ]; then
  echo "Please set ROUTER_IP and HA_CONFIG_DIR before running this script." >&2
  echo "Example: ROUTER_IP=192.168.1.1 HA_CONFIG_DIR=/config ./deploy_to_ha.sh" >&2
  exit 1
fi

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
