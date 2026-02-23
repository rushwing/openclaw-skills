# 小学数学解题视频生成指南
> 给 LLM 的完整工作流 & System Prompt 模板

---

## 一、整体 Pipeline 概览

```
题目图片/HTML
    │
    ▼
[步骤1] 理解题目 → 提取：图形结构、已知条件、问题、解题思路
    │
    ▼
[步骤2] 生成 narration.json（分镜脚本）
    │    ↳ 7个固定segment，每个含：旁白文字 + 视觉描述
    ▼
[步骤3] 生成 TutorScene.py（Manim动画代码）
    │    ↳ 对照 narration.json 逐段实现动画
    ▼
[步骤4] TTS生成音频（每个segment单独一个mp3）
    │    ↳ 文件名：{segment_id}.mp3
    ▼
[步骤5] 渲染视频 & 合并音视频
         manim -qm TutorScene.py TutorScene
         + ffmpeg 合并音频轨
```

---

## 二、步骤1 → System Prompt：理解题目

```
你是一位小学数学老师。请仔细分析以下题目图片，提取：

1. 图形类型（如：正方形+等腰直角三角形）
2. 顶点名称（如：A/B/C/D/M/N/F/E）
3. 已知数值（如：阴影面积=14cm²）
4. 关键中间量（如：M是AD中点，N是DC中点）
5. 解题核心方法（一句话，如：找到三个全等小三角形，利用7:1面积比）
6. 最终答案（如：18 cm²）
7. 几何坐标（用Manim坐标系，正方形边长=2.5单位，中心偏左x=-2.0）

请以JSON格式输出，字段：
{
  "method_name": "解题方法名（2-5字，如：化整为零法）",
  "problem_description": "题目一句话描述",
  "shapes": [{"name":"正方形ABCD","vertices":["A","B","C","D"]},...],
  "known_values": ["M是AD中点","阴影面积=14cm²",...],
  "key_insight": "关键发现（一句话）",
  "solving_steps": ["步骤1","步骤2","步骤3"],
  "answer": "最终答案（含单位）",
  "coords": {
    "GS": [-2.0, 0.0, 0.0],
    "HALF": 1.25,
    "A_PT": [-1.25, 1.25, 0],
    ...所有关键顶点坐标（相对于GS的偏移）
  }
}
```

---

## 三、步骤2 → System Prompt：生成 narration.json

```
你是教学视频脚本作家。请根据以下题目信息，生成 narration.json 分镜脚本。

## 题目信息
{粘贴步骤1的JSON输出}

## 格式要求
必须严格按照以下7个segment结构输出JSON数组，不得增减segment数量：

[
  {"id":"intro",     "text":"..."},
  {"id":"problem",   "text":"..."},
  {"id":"figure",    "text":"..."},
  {"id":"triangles", "text":"..."},
  {"id":"calculate", "text":"..."},
  {"id":"assemble",  "text":"..."},
  {"id":"summary",   "text":"..."}
]

## 各段旁白要求

| id         | 内容要求                                               | 时长参考 |
|------------|-------------------------------------------------------|---------|
| intro      | 一句引入语，说明方法名。不超过25字。                      | 4~6秒   |
| problem    | 完整朗读题目：图形、中点、已知面积、求什么。不超过60字。    | 12~18秒 |
| figure     | 描述图形结构，点出阴影区域，说明FE经过中点。不超过50字。    | 9~13秒  |
| triangles  | 宣布关键发现！三个全等三角形，说明直角边等于边长一半。不超过80字。 | 18~24秒 |
| calculate  | 推导小三角形面积：阴影=正方形-△MDN=7×△MDN，所以△MDN=14÷7=2。不超过60字。 | 15~20秒 |
| assemble   | 化整为零！△BEF=阴影+△AMF+△CNE=14+2+2=18。不超过45字。    | 9~13秒  |
| summary    | 报出最终答案，总结关键步骤（全等小三角形+面积比）。不超过55字。 | 12~16秒 |

## 语言风格
- 口语化、亲切，像老师对学生说话
- 每段开头可用"关键发现！"、"现在"、"化整为零！"等起伏词
- 避免"首先/其次/最后"等书面语
```

---

## 四、步骤3 → System Prompt：生成 TutorScene.py

```
你是 Manim 动画专家。请根据以下信息，填写 TutorScene_template.py 中所有的 FILL_IN 占位符，生成完整可运行的 TutorScene.py。

## 题目信息（步骤1输出）
{粘贴JSON}

## narration.json（步骤2输出）
{粘贴JSON}

## 关键规则

### 坐标系
- Manim 坐标：x轴向右，y轴向上，z=0
- 图形整体偏左，GS = np.array([-2.0, 0.0, 0.0])，所有顶点坐标 + GS
- 正方形边长=2.5，HALF=1.25
- 右侧 x>1.5 区域留给文字公式

### self.wait() 计算
每个 segment 的 self.wait() = 对应音频时长(秒) - 本段所有 run_time 之和
音频时长估算：text字符数 × 0.12 秒（普通语速）

### 动画顺序（必须遵守）
1. _intro()：FadeIn标题 → FadeIn副标题 → wait → FadeOut
2. _problem()：FadeIn角标 → DrawBorderThenFill背景卡 → FadeIn文字 → wait → FadeOut
3. _draw_figure()：按层次逐步Create图形，结果存入 self._fig
4. _three_triangles()：逐个FadeIn三角形+标签 → Indicate全部 → FadeIn说明 → wait → FadeOut说明，结果存入 self._tris
5. _calculate()：FadeIn标题→步骤→框 → Indicate(self._tris[1]) → wait，存入 self._calc_grp
6. _assemble()：FadeOut(self._calc_grp) → FadeIn公式 → Indicate外部三角形 → 答案框，清空 self._fig/_tris/_asm_grp
7. _summary()：大号答案 + 关键提示框 → wait

### 禁止事项
- 不得使用 MathTex（中文字体不兼容），全部用 Text()
- 不得使用 Transform()（容易报错），用 FadeOut+FadeIn 替代
- 不得修改颜色常量命名
- self._fig / self._tris / self._calc_grp 必须在对应 segment 结束前赋值

## 输出格式
直接输出完整 Python 代码，无需解释。
```

---

## 五、常见错误 & 修复

| 错误现象 | 原因 | 修复方法 |
|---------|------|---------|
| 字体报错 KeyError | FONT 名称在系统不存在 | macOS 改 "PingFang SC"，Windows 改 "Microsoft YaHei" |
| 三角形标签跑到屏幕外 | centroid 坐标计算正确但图形太小 | 增大 font_size 或调整偏移量 |
| wait() 负数 | 动画 run_time 之和超过音频时长 | 减少 run_time，或接受视频比音频稍长 |
| FadeOut 报错找不到对象 | 对象未加入 VGroup 就 FadeOut | 检查 self._fig / self._tris 是否包含所有对象 |
| 视频画面空白 | construct() 里忘记调用某个 _segment() | 检查 construct() 调用顺序 |

---

## 六、文件命名规范

```
题目文件夹/
├── narration.json          ← 分镜脚本
├── TutorScene.py           ← Manim动画代码
├── audio/
│   ├── intro.mp3           ← 对应 narration.json 的 id
│   ├── problem.mp3
│   ├── figure.mp3
│   ├── triangles.mp3
│   ├── calculate.mp3
│   ├── assemble.mp3
│   ├── summary.mp3
│   └── combined.mp3        ← 拼接后的完整音频
└── media/
    └── videos/             ← manim 输出目录
```

---

## 七、快速验证清单

生成 TutorScene.py 后，LLM 或人工检查以下项目：

- [ ] 所有 FILL_IN 占位符已替换
- [ ] 坐标列表中没有 z≠0 的情况
- [ ] self._fig 包含了 _draw_figure 中所有对象
- [ ] self._tris 包含了 3 个三角形 + 3 个标签
- [ ] self._calc_grp 在 _assemble 中被 FadeOut
- [ ] _assemble 末尾清空了 self._fig, self._tris, self._asm_grp
- [ ] 每段 self.wait() > 0
- [ ] construct() 按顺序调用了全部 7 个 segment 方法
