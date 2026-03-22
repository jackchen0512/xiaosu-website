#!/bin/bash
#
# 小苏网站 - 一键启动脚本
#

set -e

BASE_DIR="/home/node/xiaosu-website"
PID_FILE="$BASE_DIR/logs/flask.pid"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 打印带颜色的消息
print_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查服务状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 停止服务
stop_service() {
    print_info "停止Flask服务..."
    if check_status; then
        kill $(cat "$PID_FILE")
        rm "$PID_FILE"
        print_ok "服务已停止"
    else
        print_info "服务未运行"
    fi
}

# 启动服务
start_service() {
    cd "$BASE_DIR"

    # 检查是否已运行
    if check_status; then
        print_info "服务已在运行 (PID: $(cat $PID_FILE))"
        return 0
    fi

    print_info "启动Flask服务..."

   确保日志目录
    mkdir -p logs

    # 启动Flask
    nohup python3 -u api/app.py > logs/flask.log 2>&1 &
    PID=$!

    # 保存PID
    echo $PID > "$PID_FILE"

    # 等待启动
    sleep 2

    if ps -p $PID > /dev/null; then
        print_ok "服务启动成功 (PID: $PID)"
        print_ok "访问: http://localhost:5000"
    else
        print_error "服务启动失败，查看日志:"
        tail -20 logs/flask.log
        exit 1
    fi
}

# 重启服务
restart_service() {
    print_info "重启Flask服务..."
    stop_service
    sleep 1
    start_service
}

# 显示状态
show_status() {
    if check_status; then
        PID=$(cat "$PID_FILE")
        print_ok "服务运行中 (PID: $PID)"
        echo ""
        print_info "最近日志:"
        tail -10 logs/flask.log
    else
        print_info "服务未运行"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
小苏网站 - 启动脚本

用法: $0 [start|stop|restart|status|logs]

命令:
  start    启动服务
  stop     停止服务
  restart  重启服务
  status   查看状态
  logs     查看日志

示例:
  $0 start     # 启动服务
  $0 restart   # 重启服务
  $0 logs      # 查看实时日志

EOF
}

# 主程序
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        if [ -f "$BASE_DIR/logs/flask.log" ]; then
            tail -f "$BASE_DIR/logs/flask.log"
        else
            print_error "日志文件不存在"
        fi
        ;;
    *)
        show_help
        ;;
esac
