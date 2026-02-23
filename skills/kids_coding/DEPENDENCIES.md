# Kids Coding Skill — 依赖安装指南

> 本文件仅在依赖预检失败时加载。按以下顺序逐项安装缺失的依赖，完成后重试。
> **大部分依赖与 tutor skill 共享，若已安装 tutor skill 则仅需检查第 5 项。**

---

## 1. Linuxbrew 工具（manim / ffmpeg）

与 tutor skill 完全相同，参照 `{TUTOR_DIR}/DEPENDENCIES.md` 第 1 节安装。

```bash
# 验证
which manim   # 应为 /home/linuxbrew/.linuxbrew/bin/manim
which ffmpeg  # 应为 /home/linuxbrew/.linuxbrew/bin/ffmpeg
```

---

## 2. 系统 LaTeX（可选）

本 skill 的 Manim 脚本全部使用 `Text()` 而非 `MathTex()`，**通常不需要系统 LaTeX**。
若手动修改脚本中引入了 `MathTex()`，则需安装：

```bash
sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvipng cm-super
```

---

## 3. 中文字体（Noto Sans CJK SC）

与 tutor skill 完全相同，参照 `{TUTOR_DIR}/DEPENDENCIES.md` 第 3 节安装。

```bash
# 验证
fc-list | grep "Noto Sans CJK SC"
```

---

## 4. edge-tts（Python venv）

与 tutor skill **共享** `~/.tutor-venv`，无需重复安装。

```bash
# 验证
~/.tutor-venv/bin/python -c "import edge_tts; print('edge-tts OK')"
```

若 venv 不存在（tutor skill 未安装时），执行：

```bash
sudo apt-get install -y python3-venv
python3 -m venv ~/.tutor-venv
~/.tutor-venv/bin/pip install --upgrade pip edge-tts
```

---

## 5. URL 抓取依赖（requests + beautifulsoup4）

用于从 LeetCode/洛谷等 OJ 网页抓取题目内容。安装到共享 venv：

```bash
~/.tutor-venv/bin/pip install requests beautifulsoup4
```

**验证：**

```bash
~/.tutor-venv/bin/python -c "import requests, bs4; print('URL fetch OK')"
```

---

## 全量验证脚本

```bash
echo "=== Kids Coding Skill 依赖检查 ==="
PASS=true

check() {
  if eval "$2" >/dev/null 2>&1; then
    echo "✅ $1"
  else
    echo "❌ $1 — 未就绪，请参考 DEPENDENCIES.md 第 $3 节"
    PASS=false
  fi
}

check "manim"          "command -v manim"                                  1
check "ffmpeg (brew)"  "command -v ffmpeg"                                 1
check "ffprobe"        "command -v ffprobe"                                1
check "中文字体"        "fc-list | grep -q 'Noto Sans CJK SC'"             3
check "edge-tts venv"  "~/.tutor-venv/bin/python -c 'import edge_tts'"    4
check "requests+bs4"   "~/.tutor-venv/bin/python -c 'import requests,bs4'" 5

$PASS && echo "" && echo "✅ 所有依赖就绪，可以开始使用 kids_coding skill。"
$PASS || echo "" && echo "❌ 存在未就绪的依赖，请按上方提示安装后重试。"
```
