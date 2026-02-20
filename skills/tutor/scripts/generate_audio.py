#!/usr/bin/env python3
"""
Generate Chinese narration audio using edge-tts.

Usage:
    python generate_audio.py <narration_json> <output_dir>

narration_json format:
    [
        {"id": "intro", "text": "同学，让我来帮你解答这道题。"},
        {"id": "step1", "text": "第一步，我们先..."},
        ...
        {"id": "summary", "text": "总结一下这道题的关键思路..."}
    ]

Output:
    output_dir/intro.mp3
    output_dir/step1.mp3
    ...
    output_dir/combined.mp3   (all segments merged in order)

Dependencies:
    edge-tts is auto-installed into ~/.tutor-venv on first run.
    brew install ffmpeg  (for merging)
"""

import os
import sys
import subprocess
from pathlib import Path

VOICE = "zh-CN-XiaoxiaoNeural"   # Natural female Chinese voice
RATE  = "+0%"                     # Speed adjustment, e.g. "+10%" to speed up

VENV_DIR = Path.home() / ".tutor-venv"


def ensure_venv():
    """
    Ensure edge-tts is available in ~/.tutor-venv.
    On first run: creates the venv, installs edge-tts, then re-execs this
    script inside the venv so imports work correctly.
    On subsequent runs: detects we're already inside the venv and proceeds.
    """
    venv_python = VENV_DIR / "bin" / "python"

    # Already running inside our venv — nothing to do
    if str(VENV_DIR) in sys.executable:
        return

    # Create venv if it doesn't exist yet
    if not venv_python.exists():
        print(f"[tutor] Creating virtual environment at {VENV_DIR} …")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print("[tutor] Installing edge-tts …")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--quiet", "edge-tts"],
            check=True,
        )
        print("[tutor] edge-tts installed successfully.\n")

    # Re-exec this script with the venv's Python
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)


# Run venv bootstrap before any edge-tts imports
ensure_venv()

import json
import asyncio


async def synthesize_segment(text: str, output_path: Path, voice: str, rate: str):
    """Synthesize one narration segment using edge-tts."""
    try:
        import edge_tts
    except ImportError:
        print("edge-tts not found even inside venv — try deleting ~/.tutor-venv and re-running.", file=sys.stderr)
        sys.exit(1)

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(output_path))


def merge_audio_files(audio_files: list, output_path: Path):
    """Merge audio segments in order using ffmpeg."""
    if not audio_files:
        return

    if len(audio_files) == 1:
        import shutil
        shutil.copy(audio_files[0], output_path)
        return

    # Build ffmpeg concat list
    list_file = output_path.parent / "_concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in audio_files:
            f.write(f"file '{p.resolve()}'\n")

    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-acodec", "libmp3lame", "-q:a", "2", str(output_path)],
        capture_output=True, text=True
    )
    list_file.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"ffmpeg merge failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)


async def main():
    if len(sys.argv) < 3:
        print("Usage: generate_audio.py <narration_json> <output_dir>")
        sys.exit(1)

    narration_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(narration_path, encoding="utf-8") as f:
        segments = json.load(f)

    print(f"Generating {len(segments)} audio segment(s) with voice '{VOICE}'...")
    audio_files = []

    for seg in segments:
        seg_id = seg["id"]
        text   = seg["text"]
        out_path = output_dir / f"{seg_id}.mp3"

        print(f"  [{seg_id}] {text[:40]}{'...' if len(text) > 40 else ''}")
        await synthesize_segment(text, out_path, VOICE, RATE)
        audio_files.append(out_path)

    combined = output_dir / "combined.mp3"
    print(f"\nMerging segments → {combined}")
    merge_audio_files(audio_files, combined)

    print("Done. Audio files saved to:", output_dir)
    # Print durations so the video synthesizer can time slides
    for p in audio_files:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True
        )
        dur = result.stdout.strip()
        print(f"  {p.name}: {dur}s")


if __name__ == "__main__":
    asyncio.run(main())
