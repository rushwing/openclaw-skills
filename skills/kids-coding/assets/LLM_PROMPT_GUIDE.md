# 少儿编程算法视频生成指南
> 给 LLM 的完整工作流 & System Prompt 模板（适用于 Kimi 2.5 等弱 LLM）

---

## 一、整体 Pipeline 概览

```
题目（URL / 文字 / 图片）
    │
    ▼
[步骤1] 理解题目 → 提取：算法类型、数据结构、操作步骤、坐标信息
    │
    ▼
[步骤2] 生成 narration.json（7段固定分镜脚本）
    │    ↳ 固定 id：intro/problem/draw/operation_1/operation_2/result/summary
    ▼
[步骤3] 生成 TutorScene.py（填写 TutorScene_template.py 的 FILL_IN 占位符）
    │    ↳ 对照 narration.json 逐段实现动画
    ▼
[步骤4] TTS 生成音频（每个 segment 单独一个 mp3）
    │    ↳ 文件名：{segment_id}.mp3
    ▼
[步骤5] 渲染视频 & 合并音视频
         manim -qm _work/TutorScene.py TutorScene
         + ffmpeg 合并音频轨
```

---

## 二、步骤1 → System Prompt：理解题目

```
你是一位少儿编程老师。请仔细分析以下编程题，提取关键信息：

1. 算法类型（binary_tree / linked_list / binary_search / graph / sorting / array_basic）
2. 数据结构描述（节点数、结构特点）
3. 操作类型（traversal / insert / delete / search / sort）
4. 题目关键步骤（3~5个，每步一句话）
5. 示例输入和输出
6. 时间复杂度 / 空间复杂度
7. Manim 坐标（用 Manim 坐标系，节点间距约 1.2~1.5 单位）

请以 JSON 格式输出，字段：
{
  "algorithm_type": "binary_tree",
  "title": "题目名称（10字内）",
  "difficulty": "入门/基础/进阶",
  "problem_description": "一句话描述",
  "operation": "inorder_traversal",
  "data_structure": {
    "type": "binary_tree",
    "node_count": 5,
    "node_ids": ["A", "B", "C", "D", "E"],
    "node_values": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5},
    "edges": [["A","B"],["A","C"],["B","D"],["B","E"]],
    "root": "A"
  },
  "key_steps": ["步骤1", "步骤2", "步骤3"],
  "input_example": "输入描述",
  "output_example": "输出描述",
  "time_complexity": "O(n)",
  "space_complexity": "O(h)",
  "coords": {
    "A": [0, 2, 0],
    "B": [-1.5, 0.5, 0],
    "C": [1.5, 0.5, 0],
    "D": [-2.5, -1, 0],
    "E": [-0.5, -1, 0]
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
必须严格按照以下7个segment结构输出JSON数组，id固定，不得增减：

[
  {"id": "intro",       "text": "..."},
  {"id": "problem",     "text": "..."},
  {"id": "draw",        "text": "..."},
  {"id": "operation_1", "text": "..."},
  {"id": "operation_2", "text": "..."},
  {"id": "result",      "text": "..."},
  {"id": "summary",     "text": "..."}
]

## 各段旁白要求

| id          | 内容要求                                              | 字数上限 | 时长参考 |
|-------------|------------------------------------------------------|---------|---------|
| intro       | 说出算法名称和口诀。不超过25字。                         | 25      | 4~6秒   |
| problem     | 完整朗读题目：数据结构、已知条件、求什么。不超过60字。     | 60      | 10~16秒 |
| draw        | 描述画出数据结构的过程，介绍各节点/元素。不超过40字。      | 40      | 7~10秒  |
| operation_1 | 描述算法起始操作：从哪里开始、初始化什么。不超过40字。     | 40      | 7~10秒  |
| operation_2 | 逐步描述算法执行过程，突出关键状态变化。不超过80字。       | 80      | 14~20秒 |
| result      | 描述最终结果（遍历顺序/找到位置/排序完成等）。不超过40字。 | 40      | 7~10秒  |
| summary     | 报出答案，总结关键规则和复杂度。不超过50字。              | 50      | 10~14秒 |

## 语言风格
- 口语化、亲切，像老师对小学生说话
- 使用"我们"而非"我"
- operation_2 段可以说具体的节点名称（如"先去节点D，再返回节点B"）
- 避免"首先/其次/最后"等书面语，改用"先/然后/接着"
```

---

## 四、步骤3 → System Prompt：生成 TutorScene.py

```
你是 Manim 动画专家。请根据以下信息，填写 TutorScene_template.py 中所有的 FILL_IN 占位符，生成完整可运行的 TutorScene.py。

## 题目信息（步骤1输出）
{粘贴JSON}

## narration.json（步骤2输出）
{粘贴JSON}

## 算法类型模板（从 assets/algorithms/ 读取）
{粘贴对应算法的 JSON 模板内容}

## 关键规则

### 坐标系
- Manim 坐标：x轴向右，y轴向上，z=0
- 树结构：根节点在上方，子节点在下方，水平间距1.5，垂直间距1.2
- 链表：水平排列，节点间距1.4，整体居中 y=0
- 数组：水平排列，格子大小0.7，整体居中
- 图结构：参考步骤1的 coords 字段

### self.wait() 计算
每个 segment 的 self.wait() = 对应音频时长(秒) - 本段所有 run_time 之和
音频时长估算：text字符数 × 0.12 秒

### 禁止事项
- 不得使用 MathTex（中文字体不兼容），全部用 Text(font=FONT)
- 不得使用 Transform()，用 FadeOut + FadeIn 替代
- 不得硬编码颜色十六进制，使用模板顶部定义的颜色常量（C_NODE_CURRENT等）
- self._tree_nodes / self._list_nodes / self._cells 必须在对应 segment 结束前赋值

### 节点状态切换写法
```python
# 切换颜色（同时改填充和边框）
self.play(
    node_group[0].animate.set_fill(C_NODE_CURRENT).set_stroke(C_EDGE_ACTIVE),
    run_time=0.4,
)
# 脉冲效果
self.play(Indicate(node_group, scale_factor=1.3, color=C_NODE_CURRENT), run_time=0.5)
```

## 输出格式
直接输出完整 Python 代码，无需解释。代码应可直接用 `manim -qm TutorScene.py TutorScene` 渲染。
```

---

## 五、验证清单

生成 TutorScene.py 后，LLM 或人工检查以下项目：

- [ ] 所有 FILL_IN 占位符已替换
- [ ] `construct()` 按顺序调用了全部 7 个 segment 方法：`_intro → _problem → _draw → _operation_1 → _operation_2 → _result → _summary`
- [ ] 所有节点/元素对象已存入 `self._xxx` 属性（`self._tree_nodes`、`self._list_nodes`、`self._cells` 等）
- [ ] 后续 segment 中引用 `self._xxx` 时，确认该属性在之前 segment 已被赋值
- [ ] 每段 `self.wait()` > 0（若为负数，减少该段 run_time）
- [ ] 没有使用 `MathTex`（全部为 `Text(font=FONT, ...)`）
- [ ] 没有使用 `Transform()`
- [ ] 颜色全部使用常量（C_NODE_DEFAULT、C_NODE_CURRENT 等），没有硬编码十六进制

---

## 六、常见错误 & 修复

| 错误现象 | 原因 | 修复方法 |
|---------|------|---------|
| 字体 KeyError | FONT 名称不存在 | Linux: "Noto Sans CJK SC"，macOS: "PingFang SC" |
| AttributeError: self._tree_nodes | 在 _draw 前引用了 _tree_nodes | 检查 segment 调用顺序，确保 _draw 在前 |
| wait() 为负数 | run_time 之和超过音频时长 | 减少各动画 run_time，或增加 narration 字数 |
| 节点标签位置错误 | 偏移量计算不正确 | 检查 np.array 偏移方向，调整 buff 参数 |
| FadeOut 对象不存在 | 对象未加入 self._xxx 就 FadeOut | 检查 VGroup 是否包含所有对象 |
| 渲染后视频空白 | construct() 漏调某个 segment | 检查 construct() 中的 7 个方法调用 |
| 动画速度太快/太慢 | self.wait() 计算偏差 | 用 ffprobe 获取实际音频时长后重算 |
