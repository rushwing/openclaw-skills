#!/usr/bin/env python3
"""
OpenClaw Sync Script

用于周期性同步树莓派 workspace 目录下的文件及文件夹到 everything_openclaw 的 personas/ 目录下。
支持通过 cronjob 调用。

Usage:
    python scripts/openclaw_sync.py [--config CONFIG_PATH] [--dry-run]

Requirements:
    - loguru (logging)
    - pyyaml (config parsing)
    - gh CLI (GitHub operations)
    - git
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG_FILE = "openclaw_sync.yaml"
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()


# ─────────────────────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(log_dir: Path, level: str = "INFO", console_output: bool = True) -> None:
    """
    配置 loguru 日志，支持按月翻转日志文件。
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 移除默认处理器
    logger.remove()
    
    # 添加文件处理器 - 按月翻转
    # 使用 {time:YYYY-MM} 作为文件名的一部分来实现按月翻转
    log_file = log_dir / "openclaw_sync_{time:YYYY-MM}.log"
    logger.add(
        str(log_file),
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="1 month",  # 每月翻转
        retention="6 months",  # 保留6个月
        encoding="utf-8",
    )
    
    # 添加控制台处理器
    if console_output:
        logger.add(
            sys.stdout,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

def load_config(config_path: Path) -> dict[str, Any]:
    """加载 YAML 配置文件。"""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────────────────────
# File Operations
# ─────────────────────────────────────────────────────────────────────────────

def calculate_file_hash(filepath: Path) -> str:
    """计算文件的 MD5 哈希值。"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_dir_hash(dirpath: Path) -> str:
    """计算目录下所有文件的组合哈希值。"""
    hashes: list[tuple[str, str]] = []
    
    for root, _, files in os.walk(dirpath):
        for filename in sorted(files):
            filepath = Path(root) / filename
            try:
                file_hash = calculate_file_hash(filepath)
                rel_path = filepath.relative_to(dirpath)
                hashes.append((str(rel_path), file_hash))
            except (OSError, IOError):
                continue
    
    # 组合所有哈希值
    combined = "".join(f"{path}:{hash_val}" for path, hash_val in sorted(hashes))
    return hashlib.md5(combined.encode()).hexdigest()


def get_item_hash(item_path: Path) -> str:
    """获取文件或目录的哈希值。"""
    if item_path.is_file():
        return calculate_file_hash(item_path)
    elif item_path.is_dir():
        return calculate_dir_hash(item_path)
    return ""


def copy_item(src: Path, dst: Path, dry_run: bool = False) -> bool:
    """
    复制文件或目录到目标位置。
    返回是否发生了实际复制操作。
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would copy: {src} -> {dst}")
        return True
    
    try:
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            logger.debug(f"Copied file: {src} -> {dst}")
        elif src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            logger.debug(f"Copied directory: {src} -> {dst}")
        else:
            logger.warning(f"Source does not exist or is not a file/dir: {src}")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Git Operations
# ─────────────────────────────────────────────────────────────────────────────

def run_git_command(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """运行 git 命令。"""
    cmd = ["git"] + args
    logger.debug(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def run_gh_command(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """运行 gh CLI 命令。"""
    cmd = ["gh"] + args
    logger.debug(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def check_git_status(repo_path: Path) -> bool:
    """
    检查仓库是否有未提交的更改。
    返回 True 如果有更改，False 如果没有。
    """
    result = run_git_command(["status", "--porcelain"], cwd=repo_path, check=False)
    return bool(result.stdout.strip())


def get_current_branch(repo_path: Path) -> str:
    """获取当前分支名称。"""
    result = run_git_command(["branch", "--show-current"], cwd=repo_path)
    return result.stdout.strip()


def create_sync_branch(repo_path: Path, base_branch: str) -> str:
    """
    创建一个新的同步分支。
    返回分支名称。
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"sync/persona-update-{timestamp}"
    
    # 确保在默认分支上
    run_git_command(["checkout", base_branch], cwd=repo_path)
    
    # 拉取最新代码
    run_git_command(["pull", "origin", base_branch], cwd=repo_path)
    
    # 创建新分支
    run_git_command(["checkout", "-b", branch_name], cwd=repo_path)
    logger.info(f"Created and switched to branch: {branch_name}")
    
    return branch_name


def commit_changes(repo_path: Path, commit_message: str, items: list[str]) -> bool:
    """
    提交更改到当前分支。
    返回 True 如果成功提交了更改，False 如果没有更改可提交。
    """
    # 检查是否有更改
    if not check_git_status(repo_path):
        logger.info("No changes to commit")
        return False
    
    # 添加更改的文件
    run_git_command(["add", "-A"], cwd=repo_path)
    
    # 提交
    full_message = f"{commit_message}\n\nSynced items:\n" + "\n".join(f"- {item}" for item in items)
    run_git_command(["commit", "-m", full_message], cwd=repo_path)
    logger.info(f"Committed changes: {commit_message}")
    
    return True


def push_branch(repo_path: Path, branch_name: str) -> None:
    """推送分支到 origin。"""
    run_git_command(["push", "-u", "origin", branch_name], cwd=repo_path)
    logger.info(f"Pushed branch: {branch_name}")


def create_pr(repo_path: Path, branch_name: str, title: str, body: str, base: str) -> str:
    """
    创建 Pull Request。
    返回 PR URL。
    """
    result = run_gh_command(
        [
            "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base,
            "--head", branch_name,
        ],
        cwd=repo_path,
    )
    
    # 从输出中提取 PR URL
    pr_url = result.stdout.strip()
    logger.info(f"Created PR: {pr_url}")
    return pr_url


def merge_pr(repo_path: Path, branch_name: str) -> bool:
    """
    合并 PR。
    返回 True 如果成功合并。
    """
    try:
        # 使用 gh pr merge 合并
        run_gh_command(
            ["pr", "merge", branch_name, "--merge", "--delete-branch"],
            cwd=repo_path,
        )
        logger.info(f"Merged PR and deleted branch: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to merge PR: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Main Sync Logic
# ─────────────────────────────────────────────────────────────────────────────

def sync_items(config: dict[str, Any], dry_run: bool = False) -> list[str]:
    """
    执行文件同步操作。
    返回实际同步的项目列表。
    """
    source_dir = Path(config["source_dir"]).expanduser().resolve()
    target_subdir = config["target_subdir"]
    sync_items_config = config["sync_items"]
    
    target_dir = PROJECT_ROOT / "personas" / target_subdir
    
    synced: list[str] = []
    
    for item in sync_items_config:
        src_path = source_dir / item
        dst_path = target_dir / item
        
        if not src_path.exists():
            logger.warning(f"Source item does not exist, skipping: {src_path}")
            continue
        
        # 计算源和目标的哈希值来检测变化
        src_hash = get_item_hash(src_path)
        dst_hash = get_item_hash(dst_path) if dst_path.exists() else ""
        
        if src_hash == dst_hash and dst_hash:
            logger.debug(f"Item unchanged, skipping: {item}")
            continue
        
        # 执行复制
        if copy_item(src_path, dst_path, dry_run=dry_run):
            synced.append(item)
            if not dry_run:
                logger.info(f"Synced: {item}")
    
    return synced


def main() -> int:
    """主函数。"""
    parser = argparse.ArgumentParser(description="Sync OpenClaw persona files")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / DEFAULT_CONFIG_FILE,
        help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Create PR but don't auto-merge",
    )
    args = parser.parse_args()
    
    # 加载配置
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # 设置日志
    log_config = config.get("logging", {})
    log_dir = PROJECT_ROOT / log_config.get("log_dir", "logs")
    setup_logging(
        log_dir=log_dir,
        level=log_config.get("level", "INFO"),
        console_output=log_config.get("console_output", True),
    )
    
    logger.info("=" * 60)
    logger.info("OpenClaw Sync started")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)
    
    # 执行同步
    synced_items = sync_items(config, dry_run=args.dry_run)
    
    if not synced_items:
        logger.info("No items needed syncing. Exiting.")
        return 0
    
    logger.info(f"Synced {len(synced_items)} item(s): {', '.join(synced_items)}")
    
    if args.dry_run:
        logger.info("[DRY RUN] Would create branch, commit, push, and create PR")
        return 0
    
    # Git 操作
    git_config = config.get("git", {})
    default_branch = git_config.get("default_branch", "main")
    commit_prefix = git_config.get("commit_prefix", "[sync]")
    pr_title_template = git_config.get("pr_title_template", "Sync: Update persona files")
    
    try:
        # 检查是否在 git 仓库中
        run_git_command(["rev-parse", "--git-dir"], cwd=PROJECT_ROOT)
        
        # 创建同步分支
        branch_name = create_sync_branch(PROJECT_ROOT, default_branch)
        
        # 提交更改
        commit_msg = f"{commit_prefix} Update persona files from workspace ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        if not commit_changes(PROJECT_ROOT, commit_msg, synced_items):
            logger.info("No changes to commit after copy. This may indicate files were already up to date.")
            # 切换回默认分支并删除本地分支
            run_git_command(["checkout", default_branch], cwd=PROJECT_ROOT)
            run_git_command(["branch", "-D", branch_name], cwd=PROJECT_ROOT, check=False)
            return 0
        
        # 推送分支
        push_branch(PROJECT_ROOT, branch_name)
        
        # 创建 PR
        pr_title = pr_title_template
        pr_body_items = "\n".join(f"- `{item}`" for item in synced_items)
        pr_body = git_config.get("pr_body_template", "Synced items:\n{synced_items}").format(
            synced_items=pr_body_items
        )
        
        pr_url = create_pr(PROJECT_ROOT, branch_name, pr_title, pr_body, default_branch)
        
        # 合并 PR（除非指定 --no-merge）
        if not args.no_merge:
            # 等待一下确保 PR 可以被合并
            import time
            time.sleep(2)
            
            if merge_pr(PROJECT_ROOT, branch_name):
                logger.info("Successfully synced and merged!")
                
                # 切换回默认分支并拉取更新
                run_git_command(["checkout", default_branch], cwd=PROJECT_ROOT)
                run_git_command(["pull", "origin", default_branch], cwd=PROJECT_ROOT)
            else:
                logger.warning(f"PR created but not auto-merged: {pr_url}")
                logger.warning("Please merge manually.")
        else:
            logger.info(f"PR created (auto-merge skipped): {pr_url}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git/GitHub operation failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    logger.info("=" * 60)
    logger.info("OpenClaw Sync completed successfully")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
