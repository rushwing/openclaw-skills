# Tutor Skill — 依赖安装指南

> 本文件仅在依赖预检失败时加载。按以下顺序逐项安装缺失的依赖，完成后重试。

---

## 1. Linuxbrew 工具（manim / ffmpeg）

以下工具应已通过 `brew install manim` 预装到 `/home/linuxbrew/.linuxbrew/bin/`：

```bash
# 验证
which manim   # 应为 /home/linuxbrew/.linuxbrew/bin/manim
which ffmpeg  # 应为 /home/linuxbrew/.linuxbrew/bin/ffmpeg
```

如果找不到命令，先修复 PATH：

```bash
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
# 永久生效请写入 ~/.bashrc 或 ~/.profile
echo 'export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

如果 manim 本身未安装：

```bash
brew install manim
```

> **注意**：Raspberry Pi OS Lite 自带的 `/usr/bin/ffmpeg` 通常缺少 `libx264` 编码器，**必须使用 brew 版本**。

---

## 2. 系统 LaTeX（Manim 公式渲染强依赖）

> **⚠ KaTeX ≠ 系统 LaTeX，两者完全不同，不可互相替代：**
> - **KaTeX**（CDN）：浏览器端 JS 库，仅用于 HTML 文件在浏览器中渲染公式，无需系统安装。
> - **系统 LaTeX**（TeXLive）：Manim 的 `MathTex()` 类依赖它将 LaTeX 编译为 SVG。**缺失时动画中所有数学公式消失**，Manim 会降级为纯文字/幻灯片方式。

安装（约 150 MB）：

```bash
sudo apt-get install -y texlive-latex-base texlive-fonts-recommended dvipng cm-super
```

验证：

```bash
latex --version   # 应输出 pdfTeX 版本信息
dvipng --version  # 应输出 dvipng 版本信息
which latex       # 应为 /usr/bin/latex
```

---

## 3. 中文字体（Noto Sans CJK SC）

Raspberry Pi OS Lite 默认不含中文字体，Manim 渲染中文时会显示方块字。

> **不要** 使用 `sudo apt-get install fonts-noto-cjk`：该包将日文字形设为更高优先级，导致部分中文字符显示错误。

手动安装简体中文专用包：

```bash
# 1. 如果已安装 apt 版本，先卸载
sudo apt-get remove -y fonts-noto-cjk

# 2. 下载简体中文专用包（约 60 MB）
wget https://noto-website.storage.googleapis.com/pkgs/NotoSansCJKsc-hinted.zip

# 3. 解压并安装
unzip NotoSansCJKsc-hinted.zip
sudo mkdir -p /usr/share/fonts/opentype/noto
sudo cp NotoSansCJK*.otf /usr/share/fonts/opentype/noto/
sudo chmod 644 /usr/share/fonts/opentype/noto/NotoSansCJK*.otf

# 4. 刷新缓存
sudo fc-cache -fv

# 5. 验证（应输出含 "Noto Sans CJK SC" 的行）
fc-list | grep "Noto Sans CJK SC"
```

---

## 4. edge-tts（Python venv）

`edge-tts` 运行在固定 venv 中，`generate_audio.py` 脚本会**自动创建和复用**，通常无需手动操作。

**前提**：系统需已安装 `python3-venv`：

```bash
sudo apt-get install -y python3-venv
```

如果 venv 损坏需要重建：

```bash
rm -rf ~/.tutor-venv
python3 -m venv ~/.tutor-venv
~/.tutor-venv/bin/pip install --upgrade pip edge-tts
```

验证：

```bash
~/.tutor-venv/bin/python -c "import edge_tts; print('edge-tts OK')"
```

---

## 全量验证脚本

安装完成后，运行以下脚本确认所有依赖就绪：

```bash
echo "=== Tutor Skill 依赖检查 ==="
PASS=true

check() {
  if eval "$2" >/dev/null 2>&1; then
    echo "✅ $1"
  else
    echo "❌ $1 — 未就绪，请参考 DEPENDENCIES.md 第 $3 节"
    PASS=false
  fi
}

check "manim"          "command -v manim"                           1
check "ffmpeg (brew)"  "command -v ffmpeg"                          1
check "ffprobe"        "command -v ffprobe"                         1
check "latex"          "command -v latex"                           2
check "dvipng"         "command -v dvipng"                          2
check "中文字体"        "fc-list | grep -q 'Noto Sans CJK SC'"      3
check "edge-tts venv"  "~/.tutor-venv/bin/python -c 'import edge_tts'" 4

$PASS && echo "" && echo "✅ 所有依赖就绪，可以开始使用 tutor skill。"
$PASS || echo "" && echo "❌ 存在未就绪的依赖，请按上方提示安装后重试。"
```
