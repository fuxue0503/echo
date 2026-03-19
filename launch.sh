#!/bin/bash
# ── Echo Sentinel Launcher ─────────────────────────────────────────────────────
# 双击此脚本，或在终端运行: bash launch.sh
# 会同时启动 Python 后端 + Electron 桌面悬浮球

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌌 Echo Sentinel - The Orb"
echo "================================"

# 1. 检查 Python 虚拟环境
if [ ! -d "venv" ]; then
  echo "🔧 首次启动：创建虚拟环境..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt -q
else
  source venv/bin/activate
fi

# 2. 检查 Electron 依赖
if [ ! -d "electron/node_modules" ]; then
  echo "🔧 首次启动：安装 Electron..."
  cd electron && npm install && cd "$SCRIPT_DIR"
fi

# 3. Kill any existing server on port 8888
echo "🔍 检查端口 8888..."
lsof -ti :8888 | xargs kill -9 2>/dev/null && echo "   停止旧服务器" || echo "   端口空闲"
sleep 1

# 4. Start fresh backend server (background)
echo "🚀 启动后端服务器 (port 8888)..."
python3 server.py &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"

# 5. 等待服务器就绪
echo "⏳ 等待服务器启动..."
for i in $(seq 1 10); do
  if curl -s http://localhost:8888/health > /dev/null 2>&1; then
    echo "✅ 服务器已就绪"
    break
  fi
  sleep 0.5
done

# 5. 打开 Electron 桌面悬浮球
echo "🪐 启动桌面悬浮球..."
cd electron && npx electron . 

# 6. 清理：Electron 关闭后，停止服务器
echo "🛑 关闭服务器..."
kill $SERVER_PID 2>/dev/null
echo "👋 再见！"
