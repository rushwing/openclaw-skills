---
name: tutor
description: 一对一辅导老师，适用于学生粘贴题目图片时。自动分析题目、生成中文HTML讲解文档、智能归档到分类目录，并可选生成带配音的Manim动画教学视频。支持数学、物理、化学等各科目。重要：当用户从 Telegram 上传图片时，OpenClaw 会通过 telegram-media-adapter hook 自动注入图片元数据到消息上下文中，可通过 context.metadata.telegram_media 读取。优先使用此方式获取文件信息。
license: MIT
compatibility: Raspberry Pi 5（Raspberry Pi OS Lite，需预装 linuxbrew 版 manim 和 ffmpeg）
metadata: {"openclaw": {"emoji": "🎓", "os": ["linux"], "requires": {"bins": ["ffmpeg", "manim"]}}}
---

# Tutor — 一对一辅导老师

> **`SKILL_DIR`** = 本 skill 所在目录（如 `~/.openclaw/skills/tutor`）。
> 下文所有脚本命令均以此为基准，使用时替换为实际路径。

---

## 环境依赖策略

本 skill 运行于 **Raspberry Pi 5（Raspberry Pi OS Lite，无桌面环境）**，依赖管理分两类：

### 已预装（通过 Linuxbrew）

以下工具已安装到 `/home/linuxbrew/.linuxbrew/bin/`，可直接调用，**无需重复安装**：

| 工具 | 路径 | 说明 |
|------|------|------|
| `manim` | `/home/linuxbrew/.linuxbrew/bin/manim` | 数学动画渲染（已内置 ffmpeg） |
| `ffmpeg` | `/home/linuxbrew/.linuxbrew/bin/ffmpeg` | 音视频处理 |

> **注意**：Raspberry Pi OS Lite 系统自带的 `/usr/bin/ffmpeg` 可能缺少 `libx264` 等编码器。务必使用 brew 版本。如果命令找不到，手动指定路径：
> ```bash
> export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
> ```

### 需运行时安装（Python venv）

`edge-tts` 不通过 brew 安装，需在固定 venv 中管理：

```bash
# 首次创建 venv（如果不存在）
VENV_DIR="$HOME/.tutor-venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip edge-tts
fi

# 后续直接激活使用
source "$VENV_DIR/bin/activate"
```

> **前提**：`python3-venv` 必须已安装。若未安装：`sudo apt-get install python3-venv`

---

## 工作流程总览

1. 分析题目图片 → 2. 生成HTML讲解 → 3. 智能归档（分类目录+题目文件夹） → 4. 更新CLAUDE.md索引 → 5. 询问视频 → (可选) 6. 分镜脚本 → 7. Manim动画 → 8. 配音音频 → 9. 合成视频

---

## 第一步：获取题目图片

### 方式 A：从 inbound 目录读取（推荐）

OpenClaw 会自动将收到的图片下载到 `/home/openclaw/.openclaw/media/inbound/` 目录。

**查找最新的图片文件：**

```bash
# 查找最新的图片文件
INBOUND_DIR="/home/openclaw/.openclaw/media/inbound"
IMAGE_PATH=$(ls -t "$INBOUND_DIR"/*.{jpg,jpeg,png,gif} 2>/dev/null | head -1)

if [ -z "$IMAGE_PATH" ]; then
  echo "ERROR: No image found in $INBOUND_DIR"
  exit 1
fi

echo "Using image: $IMAGE_PATH"
```

**读取图片数据：**

```bash
IMAGE_DATA=$(base64 "$IMAGE_PATH")
# 或直接传入文件路径给后续步骤
```

### 方式 B：直接读取本地图片

如果用户已提供本地图片路径，直接读取。

---

## 第二步：分析题目

收到图片时：

1. 仔细阅读图片内容，识别题目类型（数学/物理/化学/语文等）
2. 确定关键知识点和解题思路
3. 先输出一段简短的"我来帮你解答这道题"，然后给出完整分析
4. 判断题目是否含有**几何图形**（三角形、圆、多边形、坐标系等）：若有，记录图形的关键几何要素（形状、标注、尺寸、相对位置），后续在分镜中用 Manim 重绘；若无（纯文字/方程题），视频中不显示图形

---

## 第二步：生成HTML讲解文档

使用 `{SKILL_DIR}/assets/template.html` 作为基础，填充以下占位符后保存为独立文件：

| 占位符 | 说明 |
|--------|------|
| `{{科目}}` | 数学/物理/化学等 |
| `{{难度}}` | 基础/中等/拔高 |
| `{{题目标题}}` | 简洁的题目名称 |
| `{{日期}}` | YYYYMMDD格式 |
| `{{知识点标签}}` | 逗号分隔 |
| `{{题目内容}}` | 原题文字还原 |
| `{{知识点列表}}` | `<li>` 列表项 |
| `{{解答步骤}}` | `<div class="step">` 块 |
| `{{关键思路}}` | `<div class="insight">` 块 |
| `{{练习题目}}` | `<li>` 列表项（可选，可留空） |

**文件命名规则：**
```
{题目类型}_{YYYYMMDD}_{简要描述}.html
```
示例：`几何_20260220_正方形面积问题.html`、`代数_20260220_方程求解.html`

**解答步骤 HTML 模板（每步）：**
```html
<div class="step">
  <div class="step-number"></div>
  <div class="step-content">
    <div class="step-title">步骤标题</div>
    <div class="step-body">步骤说明文字，支持 $行内公式$ 和 $$块级公式$$</div>
    <div class="step-formula">关键公式或计算过程</div>
  </div>
</div>
```

**关键思路 HTML 模板：**
```html
<div class="insight">
  <span class="insight-icon">🎯</span>
  <span>核心思路描述。</span>
</div>
```

---

## 第三步：智能归档（分类目录 + 题目文件夹）

### 3.1 确定工作区根目录

```bash
ls -la
```

| 发现 | 判断 | 行动 |
|------|------|------|
| `学习/`、`notes/`、`study/`、`学习资料/` 等 | 学生有良好习惯 | 使用该目录作为工作区根目录 |
| `.git`、代码文件、`node_modules/` 等 | 项目目录 | 在当前目录创建 `学习笔记/` 作为工作区根目录 |
| `/tmp`、`/var`、`/System` 等 | 临时/系统目录 | 询问学生希望保存在哪里 |
| 文件杂乱、无明显结构 | 混乱目录 | 建议创建 `学习资料/` 并让学生确认 |

**混乱目录时的提示模板：**
> 我注意到当前目录比较杂乱。建议你可以：
> 1. 创建一个专门的 `学习资料/` 文件夹，再按科目建立子文件夹（`数学/`、`物理/` 等）
> 2. 或者保持现状，我直接保存到当前目录
>
> 你希望怎么做？

### 3.2 创建分类目录和题目文件夹

根据题目类型，在工作区根目录下创建对应的**分类目录**（若已存在则跳过），再在分类目录下创建**题目文件夹**（与HTML文件同名，去掉 `.html` 后缀）：

```bash
# 分类目录示例：几何、代数、物理、化学、编程、语文、英语、生物、历史、地理
mkdir -p {工作区根目录}/{分类目录}/{题目文件夹名}
```

示例：
```bash
mkdir -p 学习资料/几何/几何_20260220_正方形面积问题
```

### 3.3 保存文件到题目文件夹

- 将 HTML 文件保存到题目文件夹内
- 后续所有工作文件（`storyboard.json`、`narration.json`、`TutorScene.py`、`audio/`、`media/`）均保存在此题目文件夹内

完整路径示例：
```
学习资料/几何/几何_20260220_正方形面积问题/几何_20260220_正方形面积问题.html
```

---

## 第四步：创建/更新 CLAUDE.md 索引

在**工作区根目录**下维护一个 `CLAUDE.md` 文件，作为所有题目的索引。

### 首次创建（工作区根目录下不存在 CLAUDE.md 时）

```markdown
# 学习资料索引

> 此文件由辅导老师技能自动维护，记录所有题目的分类索引。

## 几何

- 正方形面积问题 → `几何/几何_20260220_正方形面积问题/` (2026-02-20)

## 代数

（暂无）

## 物理

（暂无）

## 化学

（暂无）

## 编程

（暂无）
```

### 已有 CLAUDE.md 时

读取现有文件，在对应分类的末尾追加新条目：

```markdown
- {题目简要描述} → `{分类}/{题目文件夹名}/` ({YYYY-MM-DD})
```

若该分类标题尚不存在，在文件末尾追加新的分类标题和条目。

---

## 第五步：询问视频讲解

HTML 保存完成后，必须向学生询问：

> 我已经为你生成了HTML讲解文档，保存在 `{完整路径}`。
> 是否需要我制作一个**带配音的动画视频**来讲解这道题？视频可以更直观地展示解题过程，还会有语音讲解。

---

## 第六步：设计视频分镜脚本（内部设计文档）

> **注意：分镜脚本是 AI 内部规划文档，不展示给学生。所有文件保存到题目文件夹内。**

### 分镜脚本结构

在题目文件夹内保存 `storyboard.json`：

```json
{
  "title": "题目名称",
  "subject": "数学",
  "segments": [
    {
      "id": "intro",
      "type": "title",
      "title": "题目名称",
      "subtitle": "核心解题思路一句话",
      "narration": "同学，我们来看这道题。"
    },
    {
      "id": "problem",
      "type": "problem_statement",
      "lines": ["题目第一行", "题目第二行"],
      "manim_figure_code": [
        "sq = Square(side_length=2.5, color=BLUE_C, fill_opacity=0.15)",
        "lbl = MathTex('a', color=YELLOW).next_to(sq, RIGHT, buff=0.2)",
        "figure = VGroup(sq, lbl)"
      ],
      "narration": "题目问的是..."
    },
    {
      "id": "step1",
      "type": "solution_step",
      "step_number": 1,
      "step_title": "步骤名称",
      "content_lines": ["说明文字"],
      "formula": "$公式$",
      "highlight_color": "#7c3aed",
      "narration": "第一步，我们..."
    },
    {
      "id": "summary",
      "type": "summary",
      "title": "解题总结",
      "points": ["结论1", "结论2"],
      "key_insight": "解题关键一句话",
      "narration": "总结..."
    }
  ]
}
```

### 几何图形重绘规则（`manim_figure_code`）

**有几何图形时**，在 `problem_statement` 的 `manim_figure_code` 字段中填写若干行 Manim Python 代码（JSON 数组，每项一行）。代码约定：

- 使用标准 Manim 几何原语：`Square`、`Circle`、`Triangle`、`Polygon`、`Line`、`Arc`、`Angle`、`Arrow`、坐标轴 `Axes` 等
- 用 `MathTex` / `Text` 添加标注（边长、角度、变量名等）
- 颜色风格：图形主体用 `BLUE_C`（fill_opacity 0.15–0.3），标注用 `YELLOW` 或 `WHITE`
- **最后一行必须将所有对象合并**：`figure = VGroup(obj1, obj2, ...)`
- 生成器会自动对 `figure` 做 `scale_to_fit_height(3.0)` 缩放，无需手动设尺寸

**常见示例：**

```python
# 正方形 + 边长标注
sq = Square(side_length=2.5, color=BLUE_C, fill_opacity=0.15)
lbl = MathTex('a', color=YELLOW).next_to(sq, RIGHT, buff=0.2)
figure = VGroup(sq, lbl)

# 直角三角形 + 三边标注
tri = Polygon(ORIGIN, RIGHT*3, RIGHT*3+UP*2, color=BLUE_C, fill_opacity=0.15)
la = MathTex('3').next_to(tri, DOWN, buff=0.15)
lb = MathTex('2').next_to(tri, RIGHT, buff=0.15)
lc = MathTex('c').move_to(tri.get_center() + UL*0.5)
figure = VGroup(tri, la, lb, lc)

# 圆 + 半径
circ = Circle(radius=1.5, color=BLUE_C, fill_opacity=0.15)
radius_line = Line(ORIGIN, RIGHT*1.5, color=WHITE)
r_lbl = MathTex('r', color=YELLOW).next_to(radius_line, UP, buff=0.1)
figure = VGroup(circ, radius_line, r_lbl)
```

**纯文字/方程题**：省略 `manim_figure_code` 字段（或设为 `null`），视频题目页只显示文字。

### 分镜设计原则

- **每个 segment 对应一段音频**，`narration` 字段即为该段配音读白
- **步骤颜色循环使用**（按步骤编号自动分配）：
  - 步骤1：`#7c3aed`（紫）
  - 步骤2：`#2563eb`（蓝）
  - 步骤3：`#059669`（绿）
  - 步骤4：`#d97706`（琥珀）
  - 步骤5：`#dc2626`（红）
- 公式写成 LaTeX 格式（不含外层 `$`，脚本会自动加）
- 每段 narration 约 10–25 字，语速自然

### 生成 narration 音频列表

为每个 segment 提取 narration，构建 `narration.json`（保存到题目文件夹）：

```json
[
  {"id": "intro",   "text": "同学，我们来看这道题。"},
  {"id": "problem", "text": "题目问的是..."},
  {"id": "step1",   "text": "第一步，我们..."},
  {"id": "summary", "text": "总结..."}
]
```

---

## 第七步：用 Manim 生成动画

> **注意：** Manim 应已通过 `brew install manim` 预装在系统中，无需在此步骤安装。

### 7.1 生成 Manim 脚本

在题目文件夹内运行：

```bash
python {SKILL_DIR}/scripts/generate_manim.py storyboard.json TutorScene.py
```

脚本会根据分镜 JSON 生成完整的 `TutorScene.py`，包含：
- **标题页**：题目名称 + 一句话思路
- **题目展示**：蓝色背景卡片，若有原题图片则左侧显示图片、右侧显示题目文字；无图片则仅显示文字
- **每个解题步骤**：
  - 左上角彩色数字徽章 + 步骤标题
  - 步骤说明文字淡入
  - **关键公式高亮框**（颜色与步骤一致），Create 动画绘制边框
  - `Indicate` 闪烁效果引导注意力
- **总结页**：绿色✓清单 + 金色关键思路框

### 7.2 渲染动画

> **Raspberry Pi OS Lite（无桌面环境）注意**：不能使用 `-p`（渲染后自动预览）flag，否则会报错找不到显示器。统一去掉 `-p`，使用纯渲染模式。

```bash
# 快速渲染（480p，适合 Pi 性能验证）
manim -ql TutorScene.py TutorScene

# 正式渲染（720p，Pi 5 上性能与画质平衡）
manim -qm TutorScene.py TutorScene

# 高清渲染（1080p60，耗时较长，约数分钟）
manim -qh TutorScene.py TutorScene
```

输出目录：
- 480p：`media/videos/TutorScene/480p15/`
- 720p：`media/videos/TutorScene/720p30/`
- 1080p：`media/videos/TutorScene/1080p60/`

> **ffmpeg 编码器说明**：Manim 内部使用 brew 版 ffmpeg（随 manim 一同安装），渲染时会自动选用 `libx264` 编码，无需额外配置。若渲染报 codec 错误，检查 PATH 是否包含 `/home/linuxbrew/.linuxbrew/bin`。

### 7.3 高亮策略

每个步骤使用专属颜色，方式：
- **公式框**：`BackgroundRectangle` 半透明填充，颜色与步骤一致
- **边框**：`SurroundingRectangle` Create 动画，同色描边
- **闪烁引导**：关键公式使用 `Indicate(formula_tex, color=step_color)`

---

## 第八步：用 edge-tts 生成配音音频

### 8.1 虚拟环境管理（首次自动创建，后续复用）

`generate_audio.py` 脚本内置虚拟环境管理逻辑：
- 固定 venv 路径：`~/.tutor-venv`
- **首次运行**：自动创建 venv 并安装 `edge-tts`，然后在 venv 内重新执行自身
- **后续运行**：检测到已在 venv 内则直接跳过安装，复用现有环境

> **前提**：系统需已安装 `python3-venv`。若报错，先执行：
> ```bash
> sudo apt-get install -y python3-venv
> ```

无需手动安装，直接运行即可：

```bash
python3 {SKILL_DIR}/scripts/generate_audio.py narration.json audio/
```

输出：
- `audio/intro.mp3`、`audio/step1.mp3`… （各段独立音频）
- `audio/combined.mp3`（合并音频）

**配音参数：**
- 声音：`zh-CN-XiaoxiaoNeural`（自然女声）
- 语速：`+0%`（如需加速改为 `+15%`）
- 可在 `scripts/generate_audio.py` 顶部修改 `VOICE` 和 `RATE`

---

## 第九步：合成教学视频

### 9.1 准备 manifest.json

```json
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
  "background_music": null
}
```

**单文件简化方案（推荐）：**
当 Manim 输出为单一文件时，直接合并音频：

```bash
# Raspberry Pi：显式指定 libx264 + aac，避免系统默认编码器缺失问题
ffmpeg -i media/videos/TutorScene/720p30/TutorScene.mp4 \
       -i audio/combined.mp3 \
       -map 0:v -map 1:a \
       -c:v libx264 -preset fast -crf 23 \
       -c:a aac -b:a 128k \
       -shortest \
       最终讲解视频.mp4
```

> **编码说明**：
> - `-c:v libx264 -preset fast`：软件编码，brew 版 ffmpeg 已内置，树莓派 Pi 5 支持
> - `-crf 23`：质量与文件大小平衡（越小质量越高，18-28 为常用范围）
> - 不要使用 `-c:v copy`（原视频若为 yuv420p 以外的格式会报错），也不要依赖 `h264_omx`（Pi 5 已废弃）

### 9.2 多段合成（完整流程）

```bash
python {SKILL_DIR}/scripts/synthesize_video.py manifest.json 最终讲解视频.mp4
```

脚本会：
1. 逐段同步视频时长与音频时长（冻结最后一帧或裁剪）
2. 拼接所有段落
3. （可选）混入轻柔背景音乐（音量8%）

### 9.3 完成后告知学生

> 视频已生成：`最终讲解视频.mp4`
> 可用任意播放器观看，也可以拖入微信/钉钉发送。

---

## 依赖清单

| 工具 | 状态 | 路径 / 安装方式 | 用途 |
|------|------|----------------|------|
| `manim` | **预装（Linuxbrew）** | `/home/linuxbrew/.linuxbrew/bin/manim` | 数学动画渲染 |
| `ffmpeg` | **预装（Linuxbrew，manim 依赖自带）** | `/home/linuxbrew/.linuxbrew/bin/ffmpeg` | 音视频处理 |
| `edge-tts` | **运行时安装** | `~/.tutor-venv`（Python venv） | 中文配音合成 |
| `python3-venv` | 系统包（按需） | `sudo apt-get install python3-venv` | 创建 edge-tts venv 的前提 |
| KaTeX CDN | 自动加载 | HTML 内联 CDN | HTML 中的公式渲染 |

## 文件结构参考

```
{工作区根目录}/                          # 如 学习资料/
├── CLAUDE.md                            # 题目分类索引（自动维护）
├── 几何/
│   └── 几何_20260220_正方形面积问题/    # 题目文件夹
│       ├── 几何_20260220_正方形面积问题.html
│       ├── storyboard.json              # 分镜脚本（内部文档，含 manim_figure_code）
│       ├── narration.json               # 配音文本列表
│       ├── TutorScene.py                # 生成的 Manim 脚本
│       ├── manifest.json                # 视频合成清单
│       ├── audio/                       # 配音音频
│       │   ├── intro.mp3
│       │   ├── step1.mp3
│       │   └── combined.mp3
│       ├── media/videos/TutorScene/     # Manim 渲染输出
│       └── 最终讲解视频.mp4
├── 代数/
│   └── 代数_20260221_方程求解/
│       └── ...
└── 物理/
    └── ...
```
