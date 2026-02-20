# openclaw-skills

A collection of custom skills for [OpenClaw](https://openclaw.ai), organized under `skills/`.

## Skills

### 📚 github-kb

**Path:** `skills/github-kb/`

A GitHub knowledge base manager. Maintains a local directory of cloned repositories with one-line summaries indexed in `CLAUDE.md`. Enables fast, offline repo exploration before falling back to live GitHub queries.

**Triggers on:** `repo`, `repository`, `仓库`, `clone`, `GitHub`, `issue`, `PR`, `pull request`

**Requires:** [`gh`](https://cli.github.com/) (GitHub CLI)

---

### 🎓 tutor

**Path:** `skills/tutor/`

A one-on-one tutoring assistant for students. When a student pastes a photo of a problem, the skill analyzes it, generates a Chinese HTML explanation document, intelligently archives it into a categorized directory, and optionally produces a narrated Manim animation video.

**Triggers on:** problem screenshots, requests for step-by-step explanations or animated video walkthroughs

**Supports:** Math, Physics, Chemistry, and other subjects

**Requires:** `manim`, `ffmpeg` (macOS / `brew install manim ffmpeg`)

## Structure

```
skills/
├── github-kb/
│   ├── SKILL.md                  # Skill definition and workflows
│   └── references/
│       └── gh-commands.md        # gh CLI quick reference
└── tutor/
    ├── SKILL.md                  # Skill definition and workflows
    ├── assets/
    │   └── template.html         # HTML explanation document template
    └── scripts/
        ├── generate_manim.py     # Generates Manim animation script from storyboard
        ├── generate_audio.py     # Generates narration audio via edge-tts
        └── synthesize_video.py   # Merges animation and audio into final video
```
