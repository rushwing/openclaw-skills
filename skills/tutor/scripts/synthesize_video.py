#!/usr/bin/env python3
"""
Synthesize final educational video from Manim scene clips and audio segments.

Usage:
    python synthesize_video.py <manifest_json> <output_video>

manifest_json format:
    {
        "segments": [
            {
                "id": "intro",
                "video": "media/videos/TutorScene/1080p60/TutorScene_intro.mp4",
                "audio": "audio/intro.mp3"
            },
            {
                "id": "step1",
                "video": "media/videos/TutorScene/1080p60/TutorScene_step1.mp4",
                "audio": "audio/step1.mp3"
            }
        ],
        "background_music": null,   // optional path to soft background music
        "title_card": {             // optional title card at the start
            "text": "正方形面积问题",
            "duration": 2.5
        }
    }

Strategy:
    For each segment: pad/trim video to match audio duration, then concat all segments.

Dependencies:
    brew install ffmpeg
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path


def run(cmd: list, check=True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print("ffmpeg error:", result.stderr[-2000:], file=sys.stderr)
        sys.exit(1)
    return result


def get_duration(path: str) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(r.stdout.strip())


def sync_video_to_audio(video_path: str, audio_path: str, output_path: str):
    """
    Merge one video clip with its audio track.
    If audio is longer than video, freeze the last frame to fill the gap.
    If video is longer, trim it.
    """
    audio_dur = get_duration(audio_path)
    video_dur = get_duration(video_path)

    if video_dur >= audio_dur:
        # Trim video to audio length
        run(["ffmpeg", "-y",
             "-i", video_path,
             "-i", audio_path,
             "-map", "0:v:0", "-map", "1:a:0",
             "-t", str(audio_dur),
             "-c:v", "libx264", "-c:a", "aac",
             "-shortest", output_path])
    else:
        # Freeze last frame for the extra duration
        extra = audio_dur - video_dur
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        # Freeze last frame
        run(["ffmpeg", "-y",
             "-i", video_path,
             "-vf", f"tpad=stop_mode=clone:stop_duration={extra:.3f}",
             "-c:v", "libx264", tmp_path])
        # Attach audio
        run(["ffmpeg", "-y",
             "-i", tmp_path,
             "-i", audio_path,
             "-map", "0:v:0", "-map", "1:a:0",
             "-c:v", "libx264", "-c:a", "aac",
             "-shortest", output_path])
        Path(tmp_path).unlink(missing_ok=True)


def concat_clips(clip_paths: list[str], output_path: str):
    """Concatenate video clips using ffmpeg concat demuxer."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        list_path = f.name
        for p in clip_paths:
            f.write(f"file '{Path(p).resolve()}'\n")

    run(["ffmpeg", "-y",
         "-f", "concat", "-safe", "0",
         "-i", list_path,
         "-c:v", "libx264", "-c:a", "aac",
         output_path])
    Path(list_path).unlink(missing_ok=True)


def main():
    if len(sys.argv) < 3:
        print("Usage: synthesize_video.py <manifest_json> <output_video>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1])
    output_video  = sys.argv[2]

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    segments = manifest["segments"]
    workdir  = manifest_path.parent / "_synth_tmp"
    workdir.mkdir(exist_ok=True)

    synced_clips = []
    for i, seg in enumerate(segments):
        seg_id    = seg["id"]
        video     = seg["video"]
        audio     = seg["audio"]
        out_clip  = str(workdir / f"{i:02d}_{seg_id}.mp4")

        print(f"[{i+1}/{len(segments)}] Syncing '{seg_id}'...")
        sync_video_to_audio(video, audio, out_clip)
        synced_clips.append(out_clip)

    print(f"\nConcatenating {len(synced_clips)} clips → {output_video}")
    concat_clips(synced_clips, output_video)

    # Optional: mix in soft background music
    bg_music = manifest.get("background_music")
    if bg_music and Path(bg_music).exists():
        final_with_bg = str(Path(output_video).with_stem(Path(output_video).stem + "_final"))
        total_dur = get_duration(output_video)
        print(f"Mixing background music → {final_with_bg}")
        run(["ffmpeg", "-y",
             "-i", output_video,
             "-stream_loop", "-1", "-i", bg_music,
             "-filter_complex",
             f"[1:a]volume=0.08,atrim=duration={total_dur}[bg];"
             f"[0:a][bg]amix=inputs=2:duration=first[aout]",
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac",
             final_with_bg])
        print(f"Final video with music: {final_with_bg}")
    else:
        print(f"Final video: {output_video}")


if __name__ == "__main__":
    main()
