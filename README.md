# openclaw-skills

Custom skills for [OpenClaw](https://openclaw.ai), organized under `skills/`.

## Skills

| Skill | Description | Requires |
|-------|-------------|---------|
| 📚 `github-kb` | GitHub knowledge base manager — local repo index with one-line summaries in `CLAUDE.md`, offline-first exploration before live queries | `gh` CLI |
| 🎓 `tutor` | One-on-one tutoring for students (math/physics/chemistry etc.) — analyzes problem photos, generates Chinese HTML explanations with dedup, optionally produces narrated Manim animation videos | `manim`, `ffmpeg`, `edge-tts` |
| 💻 `kids-coding` | Children's programming coach — given a URL/text/image of a coding problem, generates a Mermaid flowchart + solution steps HTML, and optionally an algorithm animation video (binary tree, linked list, binary search, graph BFS/DFS/Dijkstra, sorting) | `manim`, `ffmpeg`, `edge-tts` |

## Structure

```
skills/
├── github-kb/
│   ├── SKILL.md
│   └── references/gh-commands.md
├── tutor/
│   ├── SKILL.md
│   ├── DEPENDENCIES.md
│   ├── assets/
│   │   ├── narration_template.json   # Enhanced 7-segment storyboard format
│   │   ├── TutorScene_template.py    # Manim skeleton (geometry problems)
│   │   └── LLM_PROMPT_GUIDE.md      # 3-step workflow for weak LLMs
│   └── scripts/
│       ├── generate_manim.py
│       ├── generate_audio.py
│       └── synthesize_video.py
└── kids-coding/
    ├── SKILL.md
    ├── DEPENDENCIES.md
    ├── assets/
    │   ├── narration_template.json   # Generic 7-segment template
    │   ├── TutorScene_template.py    # Manim skeleton (algorithm animations)
    │   ├── LLM_PROMPT_GUIDE.md      # 3-step workflow for weak LLMs
    │   └── algorithms/
    │       ├── binary_tree.json      # Binary tree traversal / BST
    │       ├── linked_list.json      # Linked list reverse / insert / delete
    │       ├── binary_search.json    # Binary search with range masks
    │       ├── graph.json            # BFS / DFS / Dijkstra
    │       └── sorting.json          # Bubble / selection / insertion sort
    └── scripts/                      # Shared: symlink or reference tutor/scripts
```
