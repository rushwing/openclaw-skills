#!/bin/bash
# openclaw_sync_cronjob.sh
# 用于创建每周五晚上7点(北京时间)运行的 OpenClaw 同步 cronjob

set -euo pipefail

# 配置
CRON_SCHEDULE="0 19 * * 5"  # 每周五 19:00 (北京时间)
SCRIPT_NAME="openclaw_sync.py"
PROJECT_DIR="/home/openclaw/.openclaw/workspace/everything_openclaw"
VENV_DIR="$PROJECT_DIR/.tutor-venv"
PYTHON_CMD="$VENV_DIR/bin/python"
SYNC_SCRIPT="$PROJECT_DIR/scripts/$SCRIPT_NAME"
CRON_COMMENT="# OpenClaw Persona Sync - runs every Friday at 7PM CST"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查目录和文件是否存在
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    if [[ ! -d "$VENV_DIR" ]]; then
        log_error "Virtual environment not found: $VENV_DIR"
        log_info "Please run setup_env.sh first to create the virtual environment."
        exit 1
    fi
    
    if [[ ! -f "$SYNC_SCRIPT" ]]; then
        log_error "Sync script not found: $SYNC_SCRIPT"
        exit 1
    fi
    
    # 检查 Python 脚本是否可执行
    if [[ ! -x "$PYTHON_CMD" ]]; then
        log_error "Python interpreter not executable: $PYTHON_CMD"
        exit 1
    fi
    
    log_info "All prerequisites met!"
}

# 检查是否安装了 gh CLI
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_info "Please install gh CLI: https://cli.github.com/"
        exit 1
    fi
    
    # 检查 gh 是否已登录
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated"
        log_info "Please run: gh auth login"
        exit 1
    fi
    
    log_info "GitHub CLI is installed and authenticated"
}

# 生成 cron 命令
generate_cron_command() {
    # 需要设置时区为北京时间，并激活虚拟环境后执行脚本
    local cron_cmd="$CRON_SCHEDULE cd $PROJECT_DIR && TZ=Asia/Shanghai $PYTHON_CMD $SYNC_SCRIPT >> $PROJECT_DIR/logs/cron.log 2>&1"
    echo "$cron_cmd"
}

# 安装 cronjob
install_cronjob() {
    log_info "Installing cronjob..."
    
    local cron_cmd
    cron_cmd=$(generate_cron_command)
    local full_entry="$CRON_COMMENT
$cron_cmd"
    
    # 获取当前用户的 crontab
    local current_crontab
    current_crontab=$(crontab -l 2>/dev/null || true)
    
    # 检查是否已存在相同的 cronjob
    if echo "$current_crontab" | grep -q "$SCRIPT_NAME"; then
        log_warn "Cronjob for $SCRIPT_NAME already exists"
        
        # 询问是否更新
        read -rp "Do you want to update it? (y/N): " answer
        if [[ ! "$answer" =~ ^[Yy]$ ]]; then
            log_info "Skipping cronjob installation"
            return 0
        fi
        
        # 删除旧的 cronjob条目
        current_crontab=$(echo "$current_crontab" | grep -v "$SCRIPT_NAME" | grep -v "$CRON_COMMENT")
    fi
    
    # 添加新的 cronjob
    local new_crontab
    if [[ -z "$current_crontab" ]]; then
        new_crontab="$full_entry"
    else
        new_crontab="$current_crontab
$full_entry"
    fi
    
    # 安装新的 crontab
    echo "$new_crontab" | crontab -
    
    log_info "Cronjob installed successfully!"
    log_info "Schedule: Every Friday at 7:00 PM (Beijing Time)"
    log_info "Command: $cron_cmd"
}

# 卸载 cronjob
uninstall_cronjob() {
    log_info "Uninstalling cronjob..."
    
    local current_crontab
    current_crontab=$(crontab -l 2>/dev/null || true)
    
    if ! echo "$current_crontab" | grep -q "$SCRIPT_NAME"; then
        log_warn "No cronjob found for $SCRIPT_NAME"
        return 0
    fi
    
    # 删除 cronjob条目
    local new_crontab
    new_crontab=$(echo "$current_crontab" | grep -v "$SCRIPT_NAME" | grep -v "$CRON_COMMENT")
    
    # 安装新的 crontab
    if [[ -z "$new_crontab" ]]; then
        echo "" | crontab -
    else
        echo "$new_crontab" | crontab -
    fi
    
    log_info "Cronjob uninstalled successfully!"
}

# 列出当前的 cronjob
list_cronjob() {
    log_info "Current crontab entries:"
    echo "---"
    crontab -l 2>/dev/null || echo "(empty)"
    echo "---"
}

# 运行一次同步（用于测试）
run_sync_now() {
    log_info "Running sync script now..."
    cd "$PROJECT_DIR"
    "$PYTHON_CMD" "$SYNC_SCRIPT"
}

# 显示帮助信息
show_help() {
    cat << EOF
OpenClaw Sync Cronjob Manager

Usage: $0 [COMMAND]

Commands:
    install     Install the cronjob (default)
    uninstall   Remove the cronjob
    list        List current crontab entries
    run         Run the sync script once (for testing)
    help        Show this help message

Description:
    This script manages a cronjob that runs every Friday at 7:00 PM (Beijing Time)
    to sync OpenClaw persona files from the Raspberry Pi workspace to the
    everything_openclaw repository.

Configuration:
    Project Directory: $PROJECT_DIR
    Virtual Environment: $VENV_DIR
    Sync Script: $SYNC_SCRIPT
    Schedule: $CRON_SCHEDULE (Fridays at 19:00 CST)

Requirements:
    - Python virtual environment (.tutor-venv) must exist
    - GitHub CLI (gh) must be installed and authenticated
    - Cron service must be running

EOF
}

# 主函数
main() {
    local command="${1:-install}"
    
    case "$command" in
        install)
            check_prerequisites
            check_gh_cli
            install_cronjob
            list_cronjob
            log_info "Done! The sync job will run every Friday at 7:00 PM (Beijing Time)"
            ;;
        uninstall)
            uninstall_cronjob
            list_cronjob
            ;;
        list)
            list_cronjob
            ;;
        run)
            check_prerequisites
            check_gh_cli
            run_sync_now
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
