#!/bin/bash
#
# 小苏网站 - 定时任务脚本
# git pull 自动更新 + 统计解析 + 故障恢复
#

# 配置
BASE_DIR="/home/node/xiaosu-website"
REPO_DIR="/home/node/clawd"
LOG_DIR="$BASE_DIR/logs"
ERROR_LOG="$LOG_DIR/cron_errors.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录开始时间
START_TIME=$(date +'%Y-%m-%d %H:%M:%S')
echo "=== Cron Job Started: $START_TIME ===" >> "$LOG_DIR/cron.log"

# 函数：记录错误
log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo "$msg" >> "$ERROR_LOG"
    echo "$msg" >&2
}

# 函数：记录成功
log_success() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1"
    echo "$msg" >> "$LOG_DIR/cron.log"
    echo "$msg"
}

# 切换到工作目录
cd "$REPO_DIR" || {
    log_error "无法切换到目录: $REPO_DIR"
    exit 1
}

# 1. Git拉取更新
echo "[1/3] 检查代码更新..." >> "$LOG_DIR/cron.log"
if git fetch origin 2>> "$ERROR_LOG"; then
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "检测到新commit，开始更新..." >> "$LOG_DIR/cron.log"
        if git pull origin main >> "$LOG_DIR/cron.log" 2>&1; then
            log_success "代码更新成功"
            UPDATE_DONE=1
        else
            log_error "git pull 失败"
        fi
    else
        echo "无更新，代码已是最新" >> "$LOG_DIR/cron.log"
    fi
else
    log_error "git fetch 失败"
fi

# 2. 统计解析
echo "[2/3] 运行统计解析..." >> "$LOG_DIR/cron.log"
cd "$BASE_DIR" || {
    log_error "无法切换到目录: $BASE_DIR"
    exit 1
}

if python3 scripts/analytics.py >> "$LOG_DIR/analytics.log" 2>&1; then
    log_success "统计解析完成"
else
    log_error "统计解析失败"
fi

# 3. 检查服务状态
echo "[3/3] 检查服务状态..." >> "$LOG_DIR/cron.log"
cd "$BASE_DIR" || exit 1

# 检查Flask进程
if pgrep -f "python.*api/app.py" > /dev/null; then
    echo "Flask服务运行正常" >> "$LOG_DIR/cron.log"
else
    log_error "Flask服务未运行，尝试重启..."
    # 尝试重启
    nohup python3 -u api/app.py >> "$LOG_DIR/flask.log" 2>&1 &
    sleep 2

    if pgrep -f "python.*api/app.py" > /dev/null; then
        log_success "Flask服务重启成功"
    else
        log_error "Flask服务重启失败"
    fi
fi

# 4. 恢复保护脚本（防止analytics被reset）
if [ -f "$LOG_DIR/analytics_last_size" ]; then
    LAST_SIZE=$(cat "$LOG_DIR/analytics_last_size")
    CURRENT_SIZE=$(stat -f%z "$LOG_DIR/analytics.jsonl" 2>/dev/null || stat -c%s "$LOG_DIR/analytics.jsonl" 2>/dev/null || echo "0")

    # 如果文件大小减小超过50%，可能被reset
    if [ "$CURRENT_SIZE" -lt "$((LAST_SIZE / 2))" ]; then
        log_error "警告: analytics.jsonl可能被reset (从 $LAST_SIZE 到 $CURRENT_SIZE)"
        # 触发保护措施...
        echo "保护触发" >> "$LOG_DIR/protection.log"
    fi
fi

# 记录文件大小
if [ -f "$LOG_DIR/analytics.jsonl" ]; then
    stat -f%z "$LOG_DIR/analytics.jsonl" 2>/dev/null || stat -c%s "$LOG_DIR/analytics.jsonl" 2>/dev/null > "$LOG_DIR/analytics_last_size"
fi

# 记录完成
END_TIME=$(date +'%Y-%m-%d %H:%M:%S')
echo "=== Cron Job Ended: $END_TIME ===" >> "$LOG_DIR/cron.log"
echo "" >> "$LOG_DIR/cron.log"

exit 0
