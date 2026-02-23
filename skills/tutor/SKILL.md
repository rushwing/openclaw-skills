---
name: tutor
description: 一对一辅导老师，适用于学生粘贴题目图片时。自动分析题目、生成中文HTML讲解文档、智能归档到分类目录，并可选生成带配音的Manim动画教学视频。支持数学、物理、化学等各科目。图片从 OpenClaw inbound 目录自动读取。
license: MIT
compatibility: Raspberry Pi 5（Raspberry Pi OS Lite，需预装 linuxbrew 版 manim 和 ffmpeg）
metadata: {"openclaw": {"emoji": "🎓", "os": ["linux"], "requires": {"bins": ["ffmpeg", "manim"]}}}
---

# Tutor — 一对一辅导老师

> **`SKILL_DIR`** = 本 skill 所在目录（如 `~/.openclaw/skills/tutor`）。
> 下文所有脚本命令均以此为基准，使用时替换为实际路径。

---

## 依赖预检（每次执行 skill 前自动运行）

> **执行规则：先运行预检，若有任何项目失败，立即停止并读取 `{SKILL_DIR}/DEPENDENCIES.md` 告知用户如何安装，然后退出。不得跳过预检继续执行。**

```bash
echo "=== Tutor Skill 依赖预检 ==="
MISSING=()

command -v manim  >/dev/null 2>&1 || MISSING+=("manim（Linuxbrew）")
command -v ffmpeg >/dev/null 2>&1 || MISSING+=("ffmpeg（Linuxbrew）")
command -v ffprobe>/dev/null 2>&1 || MISSING+=("ffprobe（Linuxbrew）")
command -v latex  >/dev/null 2>&1 || MISSING+=("latex（系统 LaTeX/TeXLive）")
command -v dvipng >/dev/null 2>&1 || MISSING+=("dvipng（系统 LaTeX）")
fc-list 2>/dev/null | grep -q "Noto Sans CJK SC" || MISSING+=("Noto Sans CJK SC 字体")
~/.tutor-venv/bin/python -c "import edge_tts" 2>/dev/null  || MISSING+=("edge-tts（~/.tutor-venv）")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "❌ 以下依赖未就绪："
  printf '   - %s\n' "${MISSING[@]}"
  echo ""
  echo "请读取 DEPENDENCIES.md 获取安装指引后重试。"
  exit 1
fi

echo "✅ 所有依赖就绪，继续执行。"
```

**若预检失败**：使用 Read 工具读取 `{SKILL_DIR}/DEPENDENCIES.md`，将缺失项和对应安装命令告知用户，然后停止本次执行，等待用户完成安装后重试。

> 完整安装说明见 `{SKILL_DIR}/DEPENDENCIES.md`（仅在预检失败时加载，不占用正常执行的 token）。

---

## 工作流程总览

**0. 查重（必须最先执行）** → 1. 获取图片 → 2. 分析题目 → 3. 生成HTML讲解 → 4. 智能归档 + summary.md → 5. 更新CLAUDE.md索引 → 6. 询问视频 → (可选) 7. 分镜脚本 → 8. Manim动画 → 9. 配音音频 → 10. 合成视频

---

## 第零步：查重（收到题目后必须最先执行）

> **严格执行顺序：先查重，再解题。禁止跳过本步骤直接开始分析。**

### 0.1 定位工作区根目录的 CLAUDE.md

```bash
# 树莓派 OpenClaw 环境优先
WORKDIR="/home/openclaw/.openclaw/workspace/学习资料"
CLAUDE_MD="$WORKDIR/CLAUDE.md"

# 如果上述路径不存在，退回当前目录
if [ ! -f "$CLAUDE_MD" ]; then
  CLAUDE_MD="./学习资料/CLAUDE.md"
fi

if [ -f "$CLAUDE_MD" ]; then
  echo "=== CLAUDE.md 内容 ==="
  cat "$CLAUDE_MD"
else
  echo "CLAUDE.md 不存在，跳过查重，继续第一步。"
fi
```

### 0.2 一级匹配（扫描 CLAUDE.md 关键词）

读取 CLAUDE.md 后，根据题目图片的**科目**和**关键词**，快速扫描各分类下的条目（格式见第四步）。

- 若**没有**任何可能匹配的条目 → 直接进入第一步
- 若发现**可能匹配**的条目 → 进入 0.3 二级判断

### 0.3 二级匹配（读取 summary.md）

进入 CLAUDE.md 中匹配条目指向的目录，读取 `summary.md`：

```bash
cat "$WORKDIR/{分类}/{题目文件夹}/summary.md"
```

对比 summary.md 中的**题目描述**和**关键数据**与当前题目图片：

**若确认是同一题目** → 直接回复，**不再重新解题**：

> 这道题我已经讲解过了！
> - 📄 HTML 讲解：`{完整路径}/xxx.html`
> - 🎬 教学视频：`{完整路径}/最终讲解视频.mp4`（如已生成）
>
> 需要我重新讲解或补充什么吗？

**若数据不同（相似但非同一题）** → 说明区别，继续正常流程。

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

生成以下结构的 HTML 文件，填充对应占位符后保存为独立文件：

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

#### 前提：Raspberry Pi OS 优先检测

**首先**执行以下检测（仅在 Raspberry Pi OS 上生效）：

```bash
OPENCLAW_WORKSPACE="/home/openclaw/.openclaw/workspace"
if [ -d "$OPENCLAW_WORKSPACE" ]; then
  # 树莓派 OpenClaw 环境：优先使用此目录
  mkdir -p "$OPENCLAW_WORKSPACE/学习资料"
  WORKDIR="$OPENCLAW_WORKSPACE/学习资料"
  echo "✓ 使用 OpenClaw 工作目录：$WORKDIR"
  # 直接使用此目录，跳过下方常规判断逻辑
fi
```

如果 `/home/openclaw/.openclaw/workspace` **存在**，则 `学习资料/` 目录已确定，**跳过下方常规判断，直接进入 3.2**。

#### 常规判断（非树莓派 / workspace 目录不存在时）

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
# 同时创建题目文件夹和中间文件子目录 _work/
mkdir -p {工作区根目录}/{分类目录}/{题目文件夹名}/_work
```

示例：
```bash
mkdir -p 学习资料/几何/几何_20260220_正方形面积问题/_work
```

> `_work/` 是所有视频生成中间文件的专属子目录。视频成功后整个删除；失败时原样保留便于排查。

### 3.3 文件归属规则（永久文件 vs 中间文件）

**题目文件夹根**（永久保留）：

| 文件 | 说明 |
|------|------|
| `{题目名}.html` | HTML 讲解文档 |
| `storyboard.json` | 分镜脚本（视频成功后唯一保留的中间产物） |
| `summary.md` | 题目摘要（查重用） |
| `最终讲解视频.mp4` | 最终视频（如已生成） |

**`_work/` 子目录**（生成视频用，成功后整体删除）：

| 文件/目录 | 说明 |
|-----------|------|
| `narration.json` | 配音文本列表 |
| `TutorScene.py` | 自动生成的 Manim 脚本 |
| `audio/` | 配音音频（各段 mp3 + combined.mp3） |
| `media/` | Manim 渲染输出 |

HTML 文件完整路径示例：
```
学习资料/几何/几何_20260220_正方形面积问题/几何_20260220_正方形面积问题.html
```

### 3.4 生成题目摘要（summary.md）

**归档完成后立即生成**，保存在题目文件夹内。此文件用于第零步的二级查重判断。

```markdown
# 题目摘要

- **科目**：数学/几何
- **题型**：已知面积求边长和周长
- **关键数据**：正方形面积 = 64 cm²
- **问题描述**：已知正方形面积为 64 cm²，求其边长和周长
- **核心公式**：a² = S → a = √S；C = 4a
- **答案**：边长 8 cm，周长 32 cm
- **关键词**：正方形, 面积, 边长, 周长, 开方
- **输出文件**：
  - HTML：`几何_20260220_正方形面积问题.html`
  - 视频：（如已生成，填写 `最终讲解视频.mp4`）
```

> **视频生成后**，回来更新此文件的"视频"字段。

---

## 第四步：创建/更新 CLAUDE.md 索引

在**工作区根目录**下维护一个 `CLAUDE.md` 文件，作为所有题目的索引。

每条索引记录格式为：**一行内**包含题目名称、关键词标签（用于第零步一级匹配）、目录路径、日期。

### 首次创建（工作区根目录下不存在 CLAUDE.md 时）

```markdown
# 学习资料索引

> 此文件由辅导老师技能自动维护，记录所有题目的分类索引。
> 格式：题目名称 `[关键词, ...]` → `路径/` (日期)

## 几何

- 正方形面积问题 `[正方形, 面积, 边长, 周长, 开方]` → `几何/几何_20260220_正方形面积问题/` (2026-02-20)

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
- {题目简要描述} `[关键词1, 关键词2, ...]` → `{分类}/{题目文件夹名}/` ({YYYY-MM-DD})
```

**关键词选取原则：** 题型、核心对象、关键数据单位、涉及公式名（如"勾股", "圆面积", "二次方程"），约 3-6 个词，便于扫描时快速判断是否相关。

若该分类标题尚不存在，在文件末尾追加新的分类标题和条目。

---

## 第五步：询问视频讲解

HTML 保存完成后，必须向学生询问：

> 我已经为你生成了HTML讲解文档，保存在 `{完整路径}`。
> 是否需要我制作一个**带配音的动画视频**来讲解这道题？视频可以更直观地展示解题过程，还会有语音讲解。

---

## 第六步：设计视频分镜脚本（内部设计文档）

> **注意：分镜脚本是 AI 内部规划文档，不展示给学生。所有文件保存到题目文件夹内。**
>
> **格式参考**：`{SKILL_DIR}/assets/narration_template.json`（完整带注释的样本，含每段 `type` / `duration_hint_s` / `visual` 字段说明，可直接给 Kimi 2.5 等弱 LLM 参考）。

### 分镜脚本结构

在题目文件夹内保存 `storyboard.json`。必须包含 **7 个固定 segment**，每个 segment 含 `type`、`duration_hint_s`、`narration`、`visual` 四个核心字段：

```json
{
  "title": "题目名称",
  "subject": "数学",
  "method_name": "解题方法名（2-5字）",
  "segments": [
    {
      "id": "intro",
      "segment_no": 1,
      "type": "title_card",
      "duration_hint_s": "4~6",
      "narration": "同学，我们来看这道XXX题，学习「方法名」的解题方法。",
      "visual": {
        "layout": "居中铺满",
        "elements": [
          {"role": "主标题", "text": "方法名称", "style": "font_size=58, BOLD, WHITE"},
          {"role": "副标题", "text": "题目类型描述", "style": "font_size=24, C_MUTED"}
        ],
        "animation_sequence": ["FadeIn(主标题, shift=UP)", "FadeIn(副标题)", "wait", "FadeOut"]
      }
    },
    {
      "id": "problem",
      "segment_no": 2,
      "type": "text_card",
      "duration_hint_s": "12~18",
      "narration": "题目描述...",
      "visual": {
        "layout": "居中带圆角深蓝卡片 fill=#1e3a5f stroke=#3b82f6",
        "elements": [
          {"role": "角标签", "text": "题  目", "style": "左上角灰色小字"},
          {"role": "题目文本", "lines": ["第一行：图形关系", "第二行：已知条件", "第三行：求什么？"], "style": "font_size=26, 白色, 行间距0.35"}
        ],
        "animation_sequence": ["FadeIn(角标签)", "DrawBorderThenFill(卡片)", "FadeIn(文字, shift=UP)", "wait", "FadeOut"]
      }
    },
    {
      "id": "figure",
      "segment_no": 3,
      "type": "geometry_drawing",
      "duration_hint_s": "9~13",
      "narration": "描述图形结构...",
      "visual": {
        "layout": "图形居中偏左 x≈-2.0，右侧留空给公式",
        "coordinate_system": "Manim坐标系，正方形边长=2.5单位，GS=[-2.0,0,0]",
        "elements": [
          {"role": "阴影区域", "shape": "Polygon", "vertices": "根据题目填写", "style": "fill=#3b82f6, opacity=0.30"},
          {"role": "主图形轮廓", "shape": "Polygon", "style": "stroke=WHITE, width=2.5"},
          {"role": "顶点标签A/B/C/D", "style": "font_size=22, 白色, 偏移0.25避遮挡"},
          {"role": "特殊点（中点等）", "shape": "Dot(radius=0.08, YELLOW) + Text标签", "style": "黄色小圆点"},
          {"role": "面积标注", "text": "XX cm²", "style": "font_size=22, color=#93c5fd"}
        ],
        "animation_sequence": ["FadeIn(阴影)", "Create(主图形)", "FadeIn(顶点标签)", "FadeIn(特殊点+标签)", "FadeIn(面积标注)", "wait≈7秒"],
        "note": "此段几何对象全部存入 self._fig，供后续segment使用"
      }
    },
    {
      "id": "triangles",
      "segment_no": 4,
      "type": "highlight_geometry",
      "duration_hint_s": "18~24",
      "narration": "关键发现！...",
      "visual": {
        "layout": "在segment 3图形基础上叠加高亮",
        "elements": [
          {"role": "关键图形1（外部）", "style": "fill=#f59e0b, opacity=0.55, stroke=#fbbf24"},
          {"role": "关键图形2（内部）", "style": "fill=#ef4444, opacity=0.55, stroke=#f87171"},
          {"role": "关键图形3（外部）", "style": "fill=#f59e0b, opacity=0.55"},
          {"role": "各图形标签", "style": "font_size=17, 放在重心位置"},
          {"role": "底部说明文字", "text": "三个全等的XXX！", "style": "font_size=26, #fbbf24, BOLD, to_edge(DOWN)"}
        ],
        "animation_sequence": ["FadeIn(图形1+标签)", "wait(0.5)", "FadeIn(图形2+标签)", "wait(0.5)", "FadeIn(图形3+标签)", "Indicate(全部, scale=1.15)", "FadeIn(底部说明)", "wait≈16秒", "FadeOut(底部说明)"],
        "note": "此段对象存入 self._tris"
      }
    },
    {
      "id": "calculate",
      "segment_no": 5,
      "type": "equation_steps",
      "duration_hint_s": "15~20",
      "narration": "推导计算过程...",
      "visual": {
        "layout": "图形保留左侧，右上区域显示推导步骤",
        "elements": [
          {"role": "小节标题", "text": "如「求小三角形的面积」", "style": "font_size=22, #f59e0b, BOLD, to_corner(UR)"},
          {"role": "推导步骤1", "text": "关系式", "style": "font_size=19, #e2e8f0"},
          {"role": "推导步骤2", "text": "化简", "style": "font_size=19, #e2e8f0"},
          {"role": "结果高亮框", "text": "中间结果", "style": "font_size=21, #c4b5fd, BOLD; 圆角框 fill=#4c1d95"}
        ],
        "animation_sequence": ["FadeIn(标题)", "FadeIn(步骤1)", "FadeIn(步骤2)", "wait(1)", "DrawBorderThenFill(结果框)", "FadeIn(结果)", "Indicate(对应图形)", "wait≈13秒"],
        "note": "此段对象存入 self._calc_grp"
      }
    },
    {
      "id": "assemble",
      "segment_no": 6,
      "type": "final_equation",
      "duration_hint_s": "9~13",
      "narration": "化整为零！把各部分加起来...",
      "visual": {
        "layout": "替换右侧计算区，图形保留",
        "elements": [
          {"role": "小节标题", "text": "化整为零！", "style": "font_size=22, #10b981, BOLD"},
          {"role": "拼合公式", "text": "大图形 = 部分1+部分2+...", "style": "font_size=18, #e2e8f0"},
          {"role": "代入数值", "text": "= XX + XX + XX", "style": "font_size=21, #e2e8f0"},
          {"role": "最终答案（重点高亮）", "text": "= XX cm²", "style": "font_size=30, #34d399, BOLD; 圆角框 fill=#064e3b"}
        ],
        "animation_sequence": ["FadeOut(self._calc_grp)", "FadeIn(标题)", "FadeIn(拼合公式)", "FadeIn(代入数值)", "Indicate(相关图形)", "DrawBorderThenFill(答案框)+FadeIn(答案)", "wait≈8秒", "FadeOut(图形+高亮+本段所有)"]
      }
    },
    {
      "id": "summary",
      "segment_no": 7,
      "type": "answer_reveal",
      "duration_hint_s": "12~16",
      "narration": "总结答案和解题关键...",
      "visual": {
        "layout": "居中铺满，图形已清空",
        "elements": [
          {"role": "问题回顾文字", "text": "XXX 的面积 =", "style": "font_size=34, #94a3b8, 居中偏上"},
          {"role": "大号最终答案", "text": "XX cm²", "style": "font_size=64, #34d399, BOLD; 绿色圆角框"},
          {"role": "解题关键提示框", "text": "💡 关键：一句话总结", "style": "font_size=22, #fbbf24; 橙色圆角框 fill=#451a03"}
        ],
        "animation_sequence": ["FadeIn(问题回顾, shift=UP)", "DrawBorderThenFill(答案框)", "FadeIn(大号答案)", "DrawBorderThenFill(提示框)", "FadeIn(提示文字)", "wait≈12秒"]
      }
    }
  ]
}
```

### 分镜设计原则

- **必须包含 7 个固定 segment**（id 依次：intro / problem / figure / triangles / calculate / assemble / summary），不得增减
- **每个 segment 对应一段音频**，`narration` 字段即为该段配音读白
- **`visual` 字段中不得出现 MathTex**：Manim 中文字体不支持 MathTex，所有文字用 `Text(font=FONT)` 渲染
- **narration 字符数 × 0.12 秒 ≈ 音频时长**，据此控制 `duration_hint_s` 范围
- 颜色常量统一使用 `TutorScene_template.py` 顶部定义的名称（C_AMBER / C_RED / C_GREEN 等），不要硬编码十六进制
- `geometry_drawing` segment 的所有几何对象必须存入 `self._fig`；`highlight_geometry` 存入 `self._tris`；`equation_steps` 存入 `self._calc_grp`
- 每段 narration 约 10–60 字，各 segment 字数参考 `{SKILL_DIR}/assets/narration_template.json` 中的说明

### 生成 narration 音频列表

从 storyboard.json 各 segment 提取 `narration` 字段，构建 `_work/narration.json`（供 generate_audio.py 使用，只需 `id` + `text` 两个字段）：

```json
[
  {"id": "intro",     "text": "同学，我们来看这道XXX题，学习「方法名」的解题方法。"},
  {"id": "problem",   "text": "题目描述..."},
  {"id": "figure",    "text": "描述图形结构..."},
  {"id": "triangles", "text": "关键发现！..."},
  {"id": "calculate", "text": "推导计算..."},
  {"id": "assemble",  "text": "化整为零！..."},
  {"id": "summary",   "text": "总结答案..."}
]
```

---

## 第七步：用 Manim 生成动画

> **注意：** Manim 应已通过 `brew install manim` 预装在系统中，无需在此步骤安装。

### 7.1 生成 Manim 脚本

> **模板文件**：
> - `{SKILL_DIR}/assets/TutorScene_template.py` — 含 7 个 segment 方法骨架、颜色常量、坐标系注释、FILL_IN 占位符
> - `{SKILL_DIR}/assets/LLM_PROMPT_GUIDE.md` — 完整三步工作流（理解题目 → 生成分镜 → 填写模板），适用于 Kimi 2.5 等弱 LLM

**方式 A（推荐）：自动生成**

在题目文件夹内运行（输出到 `_work/`）：

```bash
python {SKILL_DIR}/scripts/generate_manim.py storyboard.json _work/TutorScene.py
```

脚本会根据分镜 JSON 生成完整的 `_work/TutorScene.py`，包含：
- **标题页**：题目名称 + 一句话思路
- **题目展示**：蓝色背景卡片
- **几何图形页**：按 `visual.elements` 描述逐步 Create 图形
- **关键发现页**：高亮全等图形，底部结论文字
- **推导计算页**：右侧公式步骤 + 紫色中间结果框
- **化整为零页**：拼合公式 + 绿色最终答案框
- **总结页**：大号答案 + 金色关键提示框

**方式 B（手动/弱 LLM）：填写模板**

当方式 A 输出质量不满意时，使用 LLM（如 Kimi 2.5）按以下步骤生成：

1. **读取模板**：`{SKILL_DIR}/assets/TutorScene_template.py`（骨架代码，含 FILL_IN 占位符）
2. **按 LLM_PROMPT_GUIDE 三步调用**（见 `{SKILL_DIR}/assets/LLM_PROMPT_GUIDE.md`）：
   - **步骤1**：提取题目结构化信息（坐标、关键量、解题步骤）→ 输出 JSON
   - **步骤2**：基于步骤1 JSON 生成 narration.json（7 段固定结构）
   - **步骤3**：将步骤1+2 的输出贴入步骤3 System Prompt，填写 TutorScene_template.py 中所有 FILL_IN 占位符
3. **保存结果**至 `_work/TutorScene.py`

> **关键约束（抄自 LLM_PROMPT_GUIDE.md）**：
> - 不得使用 `MathTex`（中文字体不兼容），全部用 `Text(font=FONT)`
> - 不得使用 `Transform()`，用 `FadeOut + FadeIn` 替代
> - `self.wait()` = 音频时长 − 本段所有 run_time 之和（字符数 × 0.12 秒估算音频时长）
> - 颜色常量只用模板顶部定义的 C_AMBER / C_GREEN / C_PURPLE 等，禁止硬编码十六进制

### 7.2 渲染动画

> **Raspberry Pi OS Lite（无桌面环境）注意**：不能使用 `-p`（渲染后自动预览）flag，否则会报错找不到显示器。统一去掉 `-p`，使用纯渲染模式。

所有渲染命令统一在**题目文件夹**内执行（即 `_work/TutorScene.py` 所在的父级），使用 `--media_dir` 将输出重定向到 `_work/media/`：

```bash
# 快速渲染（480p，适合 Pi 性能验证）
manim -ql --media_dir _work/media _work/TutorScene.py TutorScene

# 正式渲染（720p，Pi 5 上性能与画质平衡）
manim -qm --media_dir _work/media _work/TutorScene.py TutorScene

# 高清渲染（1080p60，耗时较长，约数分钟）
manim -qh --media_dir _work/media _work/TutorScene.py TutorScene
```

输出目录（均在 `_work/media/` 内）：
- 480p：`_work/media/videos/TutorScene/480p15/`
- 720p：`_work/media/videos/TutorScene/720p30/`
- 1080p：`_work/media/videos/TutorScene/1080p60/`

> **ffmpeg 编码器说明**：Manim 内部使用 brew 版 ffmpeg（随 manim 一同安装），渲染时会自动选用 `libx264` 编码，无需额外配置。若渲染报 codec 错误，检查 PATH 是否包含 `/home/linuxbrew/.linuxbrew/bin`。

### 7.3 高亮策略

每个步骤使用专属颜色，方式：
- **公式框**：`BackgroundRectangle` 半透明填充，颜色与步骤一致
- **边框**：`SurroundingRectangle` Create 动画，同色描边
- **闪烁引导**：关键公式使用 `Indicate(formula_tex, color=step_color)`

### 7.4 渲染完成验证（**必须执行，禁止跳过**）

渲染完成后，立即执行以下验证。**若验证失败，停止后续步骤，排查错误后重新渲染。**

```bash
# 自动查找 _work/media/ 中的 Manim 输出文件
MANIM_VIDEO=$(find _work/media/videos/TutorScene -name "TutorScene.mp4" 2>/dev/null | sort | tail -1)

if [ -z "$MANIM_VIDEO" ]; then
  echo "❌ 错误：_work/media/ 中未找到 Manim 输出视频！渲染可能失败。"
  echo "检查渲染日志，常见原因：LaTeX 未安装、字体缺失、Python 语法错误"
  exit 1
fi

# 检查文件大小（小于 10KB 视为无效）
SIZE=$(du -k "$MANIM_VIDEO" | cut -f1)
if [ "$SIZE" -lt 10 ]; then
  echo "❌ 错误：视频文件过小（${SIZE}KB），可能是空文件或渲染失败"
  exit 1
fi

echo "✅ Manim 视频验证通过：$MANIM_VIDEO（${SIZE}KB）"
# 将路径保存为环境变量，供第九步使用
export MANIM_VIDEO_PATH="$MANIM_VIDEO"
```

> **注意：** 若渲染输出了"幻灯片"而非 Manim 动画（通常是因为 LaTeX 缺失），应安装 LaTeX（见依赖清单）后重新渲染，而不是接受降级版本。

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
python3 {SKILL_DIR}/scripts/generate_audio.py _work/narration.json _work/audio/
```

输出（均在 `_work/audio/`）：
- `_work/audio/intro.mp3`、`_work/audio/step1.mp3`… （各段独立音频）
- `_work/audio/combined.mp3`（合并音频）

**配音参数：**
- 声音：`zh-CN-XiaoxiaoNeural`（自然女声）
- 语速：`+0%`（如需加速改为 `+15%`）
- 可在 `scripts/generate_audio.py` 顶部修改 `VOICE` 和 `RATE`

### 8.2 音频生成验证（**必须执行，禁止跳过**）

```bash
# 验证各段音频和合并音频均已生成且有效
echo "=== 音频文件检查 ==="
ls -lh _work/audio/*.mp3 2>/dev/null || { echo "❌ 错误：_work/audio/ 目录下没有 mp3 文件！"; exit 1; }

# 重点检查 combined.mp3
if [ ! -s "_work/audio/combined.mp3" ]; then
  echo "❌ 错误：_work/audio/combined.mp3 不存在或为空文件！"
  exit 1
fi

AUDIO_SIZE=$(du -k _work/audio/combined.mp3 | cut -f1)
echo "✅ 合并音频验证通过：_work/audio/combined.mp3（${AUDIO_SIZE}KB）"

# 获取音频时长（用于第九步参考）
ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 _work/audio/combined.mp3
```

---

## 第九步：合成教学视频

### 9.1 自动探测视频与音频路径（**使用此命令，禁止手动猜测路径**）

在合成前，**必须先执行**以下命令，确认视频和音频文件均存在：

```bash
# 自动找到 _work/media/ 中的 Manim 渲染视频
MANIM_VIDEO=$(find _work/media/videos/TutorScene -name "TutorScene.mp4" 2>/dev/null | sort | tail -1)
COMBINED_AUDIO="_work/audio/combined.mp3"

echo "--- 合成前检查 ---"
echo "视频来源：$MANIM_VIDEO"
echo "音频来源：$COMBINED_AUDIO"

# 验证两个文件均存在且非空
[ -s "$MANIM_VIDEO" ]    || { echo "❌ Manim 视频不存在！请先完成第七步渲染。"; exit 1; }
[ -s "$COMBINED_AUDIO" ] || { echo "❌ 合并音频不存在！请先完成第八步配音。"; exit 1; }

# 打印时长，便于判断
echo "视频时长：$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MANIM_VIDEO")秒"
echo "音频时长：$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$COMBINED_AUDIO")秒"
```

**单文件合成（默认方案，Manim 通常输出单一文件）：**

```bash
# 使用上方探测到的 $MANIM_VIDEO 和 $COMBINED_AUDIO
# Raspberry Pi：显式指定 libx264 + aac，避免系统默认编码器缺失问题
ffmpeg -y \
       -i "$MANIM_VIDEO" \
       -i "$COMBINED_AUDIO" \
       -map 0:v -map 1:a \
       -c:v libx264 -preset fast -crf 23 \
       -c:a aac -b:a 128k \
       -shortest \
       最终讲解视频.mp4
```

> **编码说明**：
> - `-c:v libx264 -preset fast`：软件编码，brew 版 ffmpeg 已内置，树莓派 Pi 5 支持
> - `-crf 23`：质量与文件大小平衡（越小质量越高，18-28 为常用范围）
> - `-shortest`：视频和音频取较短的一个结束
> - 不要使用 `-c:v copy`（原视频若为 yuv420p 以外的格式会报错），也不要依赖 `h264_omx`（Pi 5 已废弃）

### 9.2 多段合成（完整流程）

```bash
python {SKILL_DIR}/scripts/synthesize_video.py manifest.json 最终讲解视频.mp4
```

脚本会：
1. 逐段同步视频时长与音频时长（冻结最后一帧或裁剪）
2. 拼接所有段落
3. （可选）混入轻柔背景音乐（音量8%）

### 9.3 合成结果验证与收尾（**必须执行，禁止跳过**）

```bash
# 验证最终视频文件有效
FINAL_OK=true

if [ ! -s "最终讲解视频.mp4" ]; then
  echo "❌ 错误：最终讲解视频.mp4 不存在或为空！ffmpeg 合成可能失败。"
  FINAL_OK=false
fi

if $FINAL_OK; then
  # 确认视频同时含有视频流和音频流
  HAS_VIDEO=$(ffprobe -v error -select_streams v -show_entries stream=codec_type -of csv=p=0 "最终讲解视频.mp4")
  HAS_AUDIO=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "最终讲解视频.mp4")
  [ "$HAS_VIDEO" = "video" ] || { echo "⚠ 警告：视频流缺失！"; FINAL_OK=false; }
  [ "$HAS_AUDIO" = "audio" ] || { echo "⚠ 警告：音频流缺失！"; FINAL_OK=false; }
fi
```

#### 若验证通过（成功路径）

```bash
if $FINAL_OK; then
  FINAL_SIZE=$(du -m "最终讲解视频.mp4" | cut -f1)
  FINAL_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "最终讲解视频.mp4" 2>/dev/null)
  echo "✅ 视频合成成功！大小：${FINAL_SIZE}MB，时长：${FINAL_DUR}秒"

  # 清理 _work/ 目录（删除所有中间文件）
  rm -rf _work/
  echo "🗑 中间文件目录 _work/ 已清理"

  # 更新 summary.md 视频字段
  # 手动将下方一行追加到 summary.md 的"输出文件"部分：
  #   - 视频：`最终讲解视频.mp4`
fi
```

**成功后告知学生：**

> ✅ 视频已生成：`最终讲解视频.mp4`（{FINAL_SIZE}MB，{FINAL_DUR}秒）
> 可用任意播放器观看，也可以拖入微信/钉钉发送。
>
> 题目文件夹中保留的文件：
> - `{题目名}.html`（HTML 讲解）
> - `storyboard.json`（分镜脚本）
> - `summary.md`（题目摘要）
> - `最终讲解视频.mp4`

#### 若验证失败（失败路径）

**所有 `_work/` 中间文件原样保留，不得删除。**

**必须向学生发出以下通知（禁止跳过）：**

> ⚠️ 视频合成未成功，请检查上方错误信息。
>
> 所有中间文件已保留在：
> `{题目文件夹完整路径}/_work/`
> 目录内容：`_work/TutorScene.py`、`_work/audio/`、`_work/media/`
>
> **请问需要删除这道题的文件夹并从索引中移除吗？**
> - 输入 **"是"**：删除题目文件夹 + 从 CLAUDE.md 中移除该条目
> - 输入 **"否"** 或不回复：保留所有文件，等待手动修复后重新尝试

**若学生选择删除，执行：**

```bash
# 1. 删除整个题目文件夹（含 _work/ 和所有内容）
TOPIC_DIR="{题目文件夹完整路径}"
rm -rf "$TOPIC_DIR"
echo "已删除：$TOPIC_DIR"

# 2. 从 CLAUDE.md 中移除对应条目
# （手动编辑 CLAUDE.md，删除该题目所在的那一行）
echo "请手动从 CLAUDE.md 中删除以下条目："
echo "  {题目名} [{关键词}] → {路径} ({日期})"
```

---

## 依赖速查

> 详细安装说明见 `{SKILL_DIR}/DEPENDENCIES.md`。

| 工具 | 预检命令 | 用途 |
|------|----------|------|
| `manim` | `command -v manim` | 数学动画渲染 |
| `ffmpeg` / `ffprobe` | `command -v ffmpeg` | 音视频处理（需 brew 版，含 libx264） |
| `latex` + `dvipng` | `command -v latex` | Manim `MathTex()` 公式渲染；缺失时公式消失 |
| `edge-tts` | `~/.tutor-venv/bin/python -c "import edge_tts"` | 中文配音合成 |
| Noto Sans CJK SC | `fc-list \| grep "Noto Sans CJK SC"` | Manim 中文字体；勿用 apt 版（日文优先级问题） |
| KaTeX CDN | 无（浏览器自动加载） | **仅用于 HTML 文件**渲染公式，≠ 系统 LaTeX |

## 文件结构参考

```
{工作区根目录}/                               # 如 学习资料/
├── CLAUDE.md                                 # 题目分类索引（自动维护）
├── 几何/
│   └── 几何_20260220_正方形面积问题/         # 题目文件夹
│       │
│       │  ── 永久保留文件 ──
│       ├── 几何_20260220_正方形面积问题.html  # HTML 讲解
│       ├── storyboard.json                   # 分镜脚本（视频成功后唯一保留的中间产物）
│       ├── summary.md                        # 题目摘要（查重用）
│       ├── 最终讲解视频.mp4                  # 最终视频（如已生成）
│       │
│       │  ── 中间文件（视频成功后整体删除，失败时保留）──
│       └── _work/
│           ├── narration.json               # 配音文本列表
│           ├── TutorScene.py                # 自动生成的 Manim 脚本
│           ├── audio/                       # 配音音频
│           │   ├── intro.mp3
│           │   ├── step1.mp3
│           │   └── combined.mp3
│           └── media/videos/TutorScene/     # Manim 渲染输出
│
├── 代数/
│   └── 代数_20260221_方程求解/
│       └── ...
└── 物理/
    └── ...
```
