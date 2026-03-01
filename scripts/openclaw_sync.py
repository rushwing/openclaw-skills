#!/usr/bin/env python3
"""
OpenClaw Sync Script

用于周期性同步树莓派 workspace 目录下的文件及文件夹到 everything_openclaw 的 personas/ 目录下。
支持通过 cronjob 调用。合并成功后通过 Telegram Bot 发送通知。

Usage:
    python scripts/openclaw_sync.py [--config CONFIG_PATH] [--dry-run] [--no-merge]

Requirements:
    - loguru  (logging)
    - pyyaml  (config parsing)
    - requests (Telegram notification)
    - gh CLI  (GitHub operations)
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

import requests
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
    """配置 loguru 日志，支持按自然月翻转日志文件。"""
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # 按月翻转：每月1日凌晨切换到新文件，保留6个月
    log_file = log_dir / "openclaw_sync_{time:YYYY-MM}.log"
    logger.add(
        str(log_file),
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="1 month",
        retention="6 months",
        encoding="utf-8",
    )

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
# Telegram Notification
# ─────────────────────────────────────────────────────────────────────────────

def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    """
    通过 Telegram Bot API 发送消息。
    失败时只记录日志，不中断主流程。
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Telegram notification sent.")
    except Exception as e:
        logger.warning(f"Telegram notification failed (non-fatal): {e}")


def notify_telegram(config: dict[str, Any], text: str) -> None:
    """根据配置决定是否发送 Telegram 通知。"""
    tg = config.get("telegram", {})
    if not tg.get("enabled", False):
        return
    bot_token = tg.get("bot_token", "").strip()
    chat_id = str(tg.get("chat_id", "")).strip()
    if not bot_token or not chat_id:
        logger.warning("Telegram enabled but bot_token/chat_id not set — skipping notification.")
        return
    send_telegram(bot_token, chat_id, text)


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

def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """运行 git 命令。"""
    cmd = ["git"] + args
    logger.debug(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def run_gh(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """运行 gh CLI 命令。"""
    cmd = ["gh"] + args
    logger.debug(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def has_uncommitted_changes(repo_path: Path) -> bool:
    """返回 True 如果工作区有未提交的更改。"""
    result = run_git(["status", "--porcelain"], cwd=repo_path, check=False)
    return bool(result.stdout.strip())


def create_sync_branch(repo_path: Path, base_branch: str) -> str:
    """切到 base_branch、拉取最新、再创建时间戳同步分支，返回分支名。"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"sync/persona-update-{timestamp}"

    run_git(["checkout", base_branch], cwd=repo_path)
    run_git(["pull", "origin", base_branch], cwd=repo_path)
    run_git(["checkout", "-b", branch_name], cwd=repo_path)
    logger.info(f"Created branch: {branch_name}")
    return branch_name


def commit_changes(repo_path: Path, commit_message: str, items: list[str]) -> bool:
    """
    提交工作区所有更改。
    返回 True 表示成功提交；False 表示没有可提交的内容。
    """
    if not has_uncommitted_changes(repo_path):
        logger.info("No changes to commit.")
        return False

    run_git(["add", "-A"], cwd=repo_path)
    full_message = (
        f"{commit_message}\n\nSynced items:\n"
        + "\n".join(f"- {item}" for item in items)
    )
    run_git(["commit", "-m", full_message], cwd=repo_path)
    logger.info(f"Committed: {commit_message}")
    return True


def push_branch(repo_path: Path, branch_name: str) -> None:
    """推送分支到 origin。"""
    run_git(["push", "-u", "origin", branch_name], cwd=repo_path)
    logger.info(f"Pushed branch: {branch_name}")


def create_pr(repo_path: Path, branch_name: str, title: str, body: str, base: str) -> str:
    """创建 Pull Request，返回 PR URL。"""
    result = run_gh(
        ["pr", "create", "--title", title, "--body", body, "--base", base, "--head", branch_name],
        cwd=repo_path,
    )
    pr_url = result.stdout.strip()
    logger.info(f"Created PR: {pr_url}")
    return pr_url


def merge_pr(repo_path: Path, branch_name: str) -> bool:
    """合并 PR 并删除远端分支。返回 True 表示成功。"""
    try:
        run_gh(["pr", "merge", branch_name, "--merge", "--delete-branch"], cwd=repo_path)
        logger.info(f"Merged PR and deleted remote branch: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to merge PR: {e.stderr}")
        return False


def cleanup_local_branch(repo_path: Path, branch_name: str, default_branch: str) -> None:
    """切回默认分支并删除本地临时分支。"""
    run_git(["checkout", default_branch], cwd=repo_path)
    run_git(["branch", "-D", branch_name], cwd=repo_path, check=False)


# ─────────────────────────────────────────────────────────────────────────────
# Main Sync Logic
# ─────────────────────────────────────────────────────────────────────────────

def sync_items(config: dict[str, Any], dry_run: bool = False) -> list[str]:
    """
    执行文件同步，返回实际发生变化的项目列表。
    未变化的项目直接跳过（不产生 PR）。
    """
    source_dir = Path(config["source_dir"]).expanduser().resolve()
    target_subdir = config["target_subdir"]
    items_cfg = config["sync_items"]

    target_dir = PROJECT_ROOT / "personas" / target_subdir
    synced: list[str] = []

    for item in items_cfg:
        src_path = source_dir / item
        dst_path = target_dir / item

        if not src_path.exists():
            logger.warning(f"Source item does not exist, skipping: {src_path}")
            continue

        src_hash = get_item_hash(src_path)
        dst_hash = get_item_hash(dst_path) if dst_path.exists() else ""

        if src_hash == dst_hash and dst_hash:
            logger.debug(f"Unchanged, skipping: {item}")
            continue

        if copy_item(src_path, dst_path, dry_run=dry_run):
            synced.append(item)
            if not dry_run:
                logger.info(f"Synced: {item}")

    return synced


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OpenClaw persona files to GitHub")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / DEFAULT_CONFIG_FILE,
        help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--no-merge", action="store_true", help="Create PR but don't auto-merge")
    args = parser.parse_args()

    # ── Load config ───────────────────────────────────────────────────────────
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # ── Logging ───────────────────────────────────────────────────────────────
    log_cfg = config.get("logging", {})
    log_dir = PROJECT_ROOT / log_cfg.get("log_dir", "log")
    setup_logging(
        log_dir=log_dir,
        level=log_cfg.get("level", "INFO"),
        console_output=log_cfg.get("console_output", True),
    )

    logger.info("=" * 60)
    logger.info("OpenClaw Sync started")
    logger.info(f"Config : {args.config}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)

    # ── Sync files ────────────────────────────────────────────────────────────
    synced_items = sync_items(config, dry_run=args.dry_run)

    if not synced_items:
        logger.info("No changes detected — nothing to sync. Exiting.")
        return 0

    logger.info(f"Synced {len(synced_items)} item(s): {', '.join(synced_items)}")

    if args.dry_run:
        logger.info("[DRY RUN] Would create branch, commit, push, and open PR.")
        return 0

    # ── Git / GitHub operations ───────────────────────────────────────────────
    git_cfg = config.get("git", {})
    default_branch  = git_cfg.get("default_branch", "main")
    commit_prefix   = git_cfg.get("commit_prefix", "[sync]")
    pr_title        = git_cfg.get("pr_title_template", "Sync: Update persona files from workspace")
    pr_body_tpl     = git_cfg.get(
        "pr_body_template",
        "Automated sync of persona files from Raspberry Pi workspace.\n\nSynced items:\n{synced_items}\n\n---\n*Created automatically by openclaw_sync.py*",
    )

    branch_name: str | None = None
    pr_url: str | None = None
    merged = False

    try:
        run_git(["rev-parse", "--git-dir"], cwd=PROJECT_ROOT)  # sanity check

        branch_name = create_sync_branch(PROJECT_ROOT, default_branch)

        commit_msg = (
            f"{commit_prefix} Update persona files from workspace "
            f"({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        )

        if not commit_changes(PROJECT_ROOT, commit_msg, synced_items):
            # Files were copied but git sees no diff (e.g. identical content)
            logger.info("No git diff after copy — already up to date.")
            cleanup_local_branch(PROJECT_ROOT, branch_name, default_branch)
            return 0

        push_branch(PROJECT_ROOT, branch_name)

        pr_body = pr_body_tpl.format(
            synced_items="\n".join(f"- `{i}`" for i in synced_items)
        )
        pr_url = create_pr(PROJECT_ROOT, branch_name, pr_title, pr_body, default_branch)

        if args.no_merge:
            logger.info(f"PR created (auto-merge skipped): {pr_url}")
        else:
            import time
            time.sleep(2)  # brief wait for GitHub to register the PR
            merged = merge_pr(PROJECT_ROOT, branch_name)

            if merged:
                logger.info("Sync completed and PR merged successfully.")
                # Pull merged changes back
                run_git(["checkout", default_branch], cwd=PROJECT_ROOT)
                run_git(["pull", "origin", default_branch], cwd=PROJECT_ROOT)

                # ── Telegram notification ─────────────────────────────────────
                items_text = "\n".join(f"  • {i}" for i in synced_items)
                tg_msg = (
                    f"✅ <b>OpenClaw Sync — PR Merged</b>\n\n"
                    f"<b>Repository:</b> everything_openclaw\n"
                    f"<b>PR:</b> <a href=\"{pr_url}\">{pr_title}</a>\n\n"
                    f"<b>Synced files ({len(synced_items)}):</b>\n{items_text}"
                )
                notify_telegram(config, tg_msg)
            else:
                logger.warning(f"PR created but auto-merge failed: {pr_url}")
                logger.warning("Please merge manually.")
                # Still notify — merge needs manual action
                notify_telegram(
                    config,
                    f"⚠️ <b>OpenClaw Sync — Manual Merge Required</b>\n\n"
                    f"PR created but auto-merge failed.\n"
                    f"<b>PR:</b> {pr_url}",
                )

    except subprocess.CalledProcessError as e:
        logger.error(f"Git/GitHub operation failed: {e.stderr or e}")
        if branch_name:
            cleanup_local_branch(PROJECT_ROOT, branch_name, default_branch)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if branch_name:
            cleanup_local_branch(PROJECT_ROOT, branch_name, default_branch)
        return 1

    logger.info("=" * 60)
    logger.info("OpenClaw Sync finished.")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
