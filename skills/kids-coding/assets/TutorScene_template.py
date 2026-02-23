"""
TutorScene_template.py  (kids_coding skill)
============================================
少儿编程算法教学视频 —— Manim 动画模板

使用说明：
1. 搜索所有 CUSTOMIZE: 注释，填入本题的具体参数
2. 搜索所有 FILL_IN 占位符，替换为实际文字/坐标/节点
3. 7 个 segment 方法对应 narration.json 中的 7 个固定 id
4. self.wait() = 对应音频时长 - 本段所有 run_time 之和（字数×0.12秒估算）
5. 按算法类型，只填写对应的 _draw/_operation_1/_operation_2/_result 方法
"""

from manim import *
import numpy as np

# ══════════════════════════════════════════════════════
# CUSTOMIZE: 字体（Linux/树莓派用 Noto Sans CJK SC）
# ══════════════════════════════════════════════════════
FONT = "Noto Sans CJK SC"   # macOS 改为 "PingFang SC"

# ══════════════════════════════════════════════════════
# 颜色常量（保持不变，所有算法通用）
# ══════════════════════════════════════════════════════
C_BG           = "#0f172a"   # 背景深蓝黑
C_TEXT         = "#e2e8f0"   # 正文白
C_MUTED        = "#94a3b8"   # 淡灰（副标题/小标签）
C_NODE_DEFAULT = "#1e3a5f"   # 默认节点（深蓝）
C_NODE_CURRENT = "#f59e0b"   # 当前处理节点（琥珀）
C_NODE_VISITED = "#3b82f6"   # 已访问节点（亮蓝）
C_NODE_RESULT  = "#10b981"   # 结果节点（绿）
C_NODE_BORDER  = "#e2e8f0"   # 节点边框（白）
C_EDGE_DEFAULT = "#64748b"   # 默认边/连接线（灰）
C_EDGE_ACTIVE  = "#f59e0b"   # 当前活跃边/指针（琥珀）
C_RANGE_L      = "#818cf8"   # 二分：左侧已排除（紫）
C_RANGE_R      = "#f87171"   # 二分：右侧已排除（红）
C_RANGE_MID    = "#34d399"   # 二分：当前中间元素（绿）
C_SORT_CMP     = "#f59e0b"   # 排序：正在比较（琥珀）
C_SORT_SWAP    = "#ef4444"   # 排序：被交换元素（红）
C_SORT_DONE    = "#10b981"   # 排序：已排好序（绿）
C_AMBER_STK    = "#fbbf24"   # 高亮边框色
C_GREEN_DARK   = "#064e3b"   # 绿色深底
C_ORANGE_DARK  = "#451a03"   # 橙色深底
C_BLUE_DARK    = "#1e3a5f"   # 深蓝底（卡片）
C_POINTER      = "#fbbf24"   # 指针颜色


# ══════════════════════════════════════════════════════
class TutorScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        # 按顺序调用 7 个 segment（顺序固定，禁止改变）
        self._intro()
        self._problem()
        self._draw()
        self._operation_1()
        self._operation_2()
        self._result()
        self._summary()
        self.wait(1)

    # ─────────────────────────────────────────────────
    # 通用 Helper 方法
    # ─────────────────────────────────────────────────

    def tx(self, text, **kw):
        """创建 Text 对象，默认使用全局字体。禁止使用 MathTex。"""
        return Text(text, font=FONT, **kw)

    # ── 二叉树 / 图 节点 ──────────────────────────
    def make_node(self, val, pos, radius=0.35, fill=None, stroke=None):
        """创建圆形节点 VGroup(circle, label)。"""
        fill   = fill   or C_NODE_DEFAULT
        stroke = stroke or C_NODE_BORDER
        c = Circle(radius=radius, fill_color=fill, fill_opacity=1,
                   stroke_color=stroke, stroke_width=2)
        c.move_to(pos)
        lbl = self.tx(str(val), font_size=int(radius * 55), color=C_TEXT, weight=BOLD)
        lbl.move_to(c)
        return VGroup(c, lbl)

    def make_edge(self, p1, p2, color=None, width=2.0):
        """创建两点之间的连线（无方向）。"""
        return Line(p1, p2, color=color or C_EDGE_DEFAULT, stroke_width=width)

    def make_arrow_edge(self, p1, p2, color=None, weight_txt=None):
        """创建有向箭头边，可选权重标注。"""
        color = color or C_EDGE_DEFAULT
        arr   = Arrow(p1, p2, color=color, stroke_width=2,
                      max_tip_length_to_length_ratio=0.2, buff=0.4)
        if weight_txt is not None:
            mid  = (np.array(p1) + np.array(p2)) / 2
            off  = np.array([0.25, 0.25, 0])
            wlbl = self.tx(str(weight_txt), font_size=16, color=C_TEXT)
            wlbl.move_to(mid + off)
            return VGroup(arr, wlbl)
        return arr

    def set_node_state(self, node_grp, state):
        """返回将节点切换到指定状态的 Animation（用于 self.play()）。"""
        colors = {
            "default": (C_NODE_DEFAULT, C_NODE_BORDER),
            "current": (C_NODE_CURRENT, C_EDGE_ACTIVE),
            "visited": (C_NODE_VISITED, C_NODE_VISITED),
            "result":  (C_NODE_RESULT,  C_NODE_RESULT),
        }
        fill, stroke = colors.get(state, colors["default"])
        return node_grp[0].animate.set_fill(fill).set_stroke(stroke)

    def visit_badge(self, order_num, pos):
        """创建访问顺序编号小徽章（①②③...），放在节点右上角。"""
        symbols = "①②③④⑤⑥⑦⑧⑨⑩"
        sym = symbols[order_num - 1] if order_num <= 10 else str(order_num)
        return self.tx(sym, font_size=16, color=C_AMBER_STK).move_to(
            np.array(pos) + np.array([0.32, 0.32, 0])
        )

    # ── 链表节点 ──────────────────────────────────
    def make_list_node(self, val, pos, w=0.8, h=0.6, fill=None):
        """创建链表节点 VGroup(rect, label)。"""
        fill = fill or C_NODE_DEFAULT
        r = RoundedRectangle(corner_radius=0.08, width=w, height=h,
                             fill_color=fill, fill_opacity=1,
                             stroke_color=C_NODE_BORDER, stroke_width=1.5)
        r.move_to(pos)
        lbl = self.tx(str(val), font_size=22, color=C_TEXT, weight=BOLD)
        lbl.move_to(r)
        return VGroup(r, lbl)

    def make_list_arrow(self, from_node, to_node):
        """创建链表节点之间的 next 指针箭头。"""
        start = from_node.get_right()
        end   = to_node.get_left()
        return Arrow(start, end, color=C_EDGE_DEFAULT, stroke_width=1.8,
                     max_tip_length_to_length_ratio=0.25, buff=0.05)

    def make_pointer_arrow(self, target_node, name, direction=UP, color=None):
        """创建指向节点的指针箭头（如 head↓、curr↓）。"""
        color = color or C_POINTER
        tip   = target_node.get_top() + direction * 0.1
        base  = tip + direction * 0.6
        arr   = Arrow(base, tip, color=color, stroke_width=2,
                      max_tip_length_to_length_ratio=0.35, buff=0)
        lbl   = self.tx(name, font_size=16, color=color)
        lbl.next_to(arr, direction, buff=0.08)
        return VGroup(arr, lbl)

    # ── 数组格 ────────────────────────────────────
    def make_cell(self, val, idx, pos, size=0.7, fill=None):
        """创建数组格 VGroup(square, val_label, idx_label)。"""
        fill = fill or C_NODE_DEFAULT
        sq   = Square(side_length=size, fill_color=fill, fill_opacity=1,
                      stroke_color=C_NODE_BORDER, stroke_width=1.5)
        sq.move_to(pos)
        vlbl = self.tx(str(val), font_size=20, color=C_TEXT, weight=BOLD)
        vlbl.move_to(sq)
        ilbl = self.tx(str(idx), font_size=13, color=C_MUTED)
        ilbl.next_to(sq, DOWN, buff=0.12)
        return VGroup(sq, vlbl, ilbl)

    def make_bisect_arrow(self, cell, name, color=None):
        """创建数组格下方指针箭头（left/right/mid）。"""
        color = color or C_POINTER
        tip   = cell[0].get_bottom() + DOWN * 0.05
        base  = tip + DOWN * 0.5
        arr   = Arrow(base, tip, color=color, stroke_width=2,
                      max_tip_length_to_length_ratio=0.4, buff=0)
        lbl   = self.tx(name, font_size=15, color=color)
        lbl.next_to(arr, DOWN, buff=0.06)
        return VGroup(arr, lbl)

    def make_range_mask(self, cells, start_idx, end_idx, color):
        """在数组格上叠加半透明遮罩，表示已排除范围。"""
        if start_idx > end_idx:
            return VGroup()
        left_pos  = cells[start_idx][0].get_left()
        right_pos = cells[end_idx][0].get_right()
        w = right_pos[0] - left_pos[0]
        h = cells[0][0].side_length
        mask = Rectangle(width=w, height=h,
                         fill_color=color, fill_opacity=0.45, stroke_width=0)
        mask.move_to((left_pos + right_pos) / 2)
        return mask

    # ── 通用 UI ──────────────────────────────────
    def right_panel_title(self, text, color=None):
        """右侧面板小节标题，统一位置。"""
        color = color or C_NODE_CURRENT
        t = self.tx(text, font_size=22, color=color, weight=BOLD)
        t.to_corner(UR, buff=0.6).shift(DOWN * 0.9)
        return t

    def result_box(self, text, font_size=30):
        """创建绿色结果高亮框。"""
        lbl = self.tx(text, font_size=font_size, color=C_NODE_RESULT, weight=BOLD)
        box = SurroundingRectangle(lbl, corner_radius=0.15, buff=0.25,
                                   fill_color=C_GREEN_DARK, fill_opacity=0.6,
                                   stroke_color=C_NODE_RESULT, stroke_width=2.5)
        return VGroup(box, lbl)

    def insight_box(self, text):
        """创建橙色关键提示框。"""
        lbl = self.tx(text, font_size=22, color=C_AMBER_STK)
        box = SurroundingRectangle(lbl, corner_radius=0.15, buff=0.2,
                                   fill_color=C_ORANGE_DARK, fill_opacity=0.6,
                                   stroke_color=C_NODE_CURRENT, stroke_width=2)
        return VGroup(box, lbl)

    # ══════════════════════════════════════════════
    # Segment 1: intro  (id="intro")
    # CUSTOMIZE: 替换标题和口诀；调整 self.wait()
    # ══════════════════════════════════════════════
    def _intro(self):
        # FILL_IN: 算法名称
        title = self.tx("FILL_IN_算法名称", font_size=52, weight=BOLD, color=WHITE)
        # FILL_IN: 口诀/副标题（如"左 → 根 → 右"）
        sub   = self.tx("FILL_IN_口诀", font_size=28, color=C_MUTED)
        sub.next_to(title, DOWN, buff=0.5)
        grp   = VGroup(title, sub).move_to(ORIGIN)

        self.play(FadeIn(title, shift=UP * 0.3), run_time=0.8)
        self.play(FadeIn(sub),                   run_time=0.5)
        self.wait(3.7)   # CUSTOMIZE: 总时长 ≈ 音频时长
        self.play(FadeOut(grp),                  run_time=0.5)

    # ══════════════════════════════════════════════
    # Segment 2: problem  (id="problem")
    # CUSTOMIZE: 填入题目文字，调整 self.wait()
    # ══════════════════════════════════════════════
    def _problem(self):
        lbl = self.tx("题  目", font_size=18, color=C_MUTED, weight=BOLD)
        lbl.to_corner(UL, buff=0.5)

        # FILL_IN: 题目拆成 3~4 行，每行不超过 22 字
        lines_txt = [
            "FILL_IN_第一行：数据结构描述",
            "FILL_IN_第二行：已知条件",
            "FILL_IN_第三行：求什么？",
        ]
        lines = [self.tx(t, font_size=26, color=C_TEXT) for t in lines_txt]
        prob  = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        prob.move_to(ORIGIN)
        bg = RoundedRectangle(
            corner_radius=0.2,
            width=prob.width + 1.0,
            height=prob.height + 0.8,
            fill_color=C_BLUE_DARK, fill_opacity=0.85,
            stroke_color=C_NODE_VISITED, stroke_width=2,
        ).move_to(prob)

        self.play(FadeIn(lbl),                      run_time=0.3)
        self.play(DrawBorderThenFill(bg),            run_time=0.6)
        self.play(FadeIn(prob, shift=UP * 0.1),      run_time=0.8)
        self.wait(10.3)   # CUSTOMIZE
        self.play(FadeOut(VGroup(lbl, bg, prob)),    run_time=0.5)

    # ══════════════════════════════════════════════
    # Segment 3: draw  (id="draw")
    # CUSTOMIZE: 根据算法类型填写绘制逻辑
    # 选择下方对应的模板块，删除其他
    # ══════════════════════════════════════════════
    def _draw(self):
        # ── 二叉树绘制模板（binary_tree 时使用）──────────────
        # FILL_IN: 各节点位置和值
        # 示例：根节点在上，子节点在下，水平间距1.5，垂直间距1.2

        # 创建所有节点
        # 格式：self._tree_nodes["NodeID"] = self.make_node(val, pos)
        self._tree_nodes = {}
        # FILL_IN: 按题目填写所有节点
        self._tree_nodes["A"] = self.make_node("FILL_IN_val", [0,  2,  0])   # 根节点
        self._tree_nodes["B"] = self.make_node("FILL_IN_val", [-1.5, 0.5, 0])  # 左子
        self._tree_nodes["C"] = self.make_node("FILL_IN_val", [ 1.5, 0.5, 0])  # 右子
        # FILL_IN: 继续添加叶子节点...

        # 创建所有边
        self._tree_edges = []
        # FILL_IN: 按父子关系添加边
        self._tree_edges.append(self.make_edge(
            self._tree_nodes["A"].get_center(),
            self._tree_nodes["B"].get_center()
        ))
        self._tree_edges.append(self.make_edge(
            self._tree_nodes["A"].get_center(),
            self._tree_nodes["C"].get_center()
        ))
        # FILL_IN: 继续添加边...

        # 动画：先画边，再画节点
        self.play(*[Create(e) for e in self._tree_edges], run_time=0.8)
        self.play(*[FadeIn(n) for n in self._tree_nodes.values()], run_time=0.8)
        self.wait(5.4)   # CUSTOMIZE

        # ──────────────────────────────────────────────────────
        # 链表绘制模板（linked_list 时使用）
        # ──────────────────────────────────────────────────────
        # FILL_IN: 节点个数和值
        # vals = [FILL_IN_val1, FILL_IN_val2, FILL_IN_val3, ...]
        # n = len(vals)
        # start_x = -(n - 1) * 0.7  # 居中计算
        #
        # self._list_nodes = []
        # self._list_arrows = []
        # for i, v in enumerate(vals):
        #     pos = np.array([start_x + i * 1.4, 0, 0])
        #     node = self.make_list_node(v, pos)
        #     self._list_nodes.append(node)
        #
        # for i in range(len(self._list_nodes) - 1):
        #     arr = self.make_list_arrow(self._list_nodes[i], self._list_nodes[i+1])
        #     self._list_arrows.append(arr)
        #
        # null_txt = self.tx("null", font_size=18, color=C_MUTED)
        # null_txt.next_to(self._list_nodes[-1], RIGHT, buff=0.5)
        # head_ptr = self.make_pointer_arrow(self._list_nodes[0], "head")
        #
        # self.play(*[FadeIn(n) for n in self._list_nodes], run_time=0.8)
        # self.play(*[Create(a) for a in self._list_arrows], run_time=0.6)
        # self.play(FadeIn(null_txt), FadeIn(head_ptr), run_time=0.5)
        # self.wait(5.0)   # CUSTOMIZE

        # ──────────────────────────────────────────────────────
        # 数组绘制模板（binary_search / sorting 时使用）
        # ──────────────────────────────────────────────────────
        # FILL_IN: 数组值
        # arr_vals = [FILL_IN_v0, FILL_IN_v1, FILL_IN_v2, ...]
        # n = len(arr_vals)
        # start_x = -(n - 1) * 0.35  # 居中
        #
        # self._cells = []
        # for i, v in enumerate(arr_vals):
        #     pos = np.array([start_x + i * 0.7, 0, 0])
        #     cell = self.make_cell(v, i, pos)
        #     self._cells.append(cell)
        #
        # self.play(LaggedStart(*[FadeIn(c) for c in self._cells], lag_ratio=0.15), run_time=1.0)
        # self.wait(5.0)   # CUSTOMIZE

        # ──────────────────────────────────────────────────────
        # 图绘制模板（graph 时使用）
        # ──────────────────────────────────────────────────────
        # FILL_IN: 节点位置（来自步骤1的 coords 字段）
        # FILL_IN: 边列表（有向/无向，是否有权重）
        #
        # self._graph_nodes = {}
        # self._graph_edges = []
        #
        # node_data = {
        #     "A": ([0, 2, 0], "FILL_IN_val"),
        #     "B": ([-1.5, 0, 0], "FILL_IN_val"),
        #     # FILL_IN: 继续添加节点...
        # }
        # for nid, (pos, val) in node_data.items():
        #     self._graph_nodes[nid] = self.make_node(val, pos, radius=0.4)
        #
        # edge_data = [
        #     ("A", "B", None),   # (from, to, weight or None)
        #     # FILL_IN: 继续添加边...
        # ]
        # for u, v, w in edge_data:
        #     p1 = self._graph_nodes[u].get_center()
        #     p2 = self._graph_nodes[v].get_center()
        #     # 有向图用 make_arrow_edge，无向图用 make_edge
        #     e = self.make_arrow_edge(p1, p2, weight_txt=w)
        #     self._graph_edges.append(e)
        #
        # self.play(*[Create(e) for e in self._graph_edges], run_time=0.8)
        # self.play(*[FadeIn(n) for n in self._graph_nodes.values()], run_time=0.8)
        # self.wait(5.0)   # CUSTOMIZE

    # ══════════════════════════════════════════════
    # Segment 4: operation_1  (id="operation_1")
    # CUSTOMIZE: 初始化操作（高亮起始节点/指针/范围）
    # ══════════════════════════════════════════════
    def _operation_1(self):
        # FILL_IN: 高亮起始节点（以二叉树为例）
        start_node = self._tree_nodes["A"]   # FILL_IN: 起始节点 id
        self.play(self.set_node_state(start_node, "current"), run_time=0.4)
        self.play(Indicate(start_node, scale_factor=1.3, color=C_NODE_CURRENT), run_time=0.6)

        # FILL_IN: 说明文字（如"从根节点1开始！"）
        caption = self.tx("FILL_IN_说明文字", font_size=26, color=C_AMBER_STK, weight=BOLD)
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption), run_time=0.4)
        self.wait(5.2)   # CUSTOMIZE
        self.play(FadeOut(caption), run_time=0.3)

    # ══════════════════════════════════════════════
    # Segment 5: operation_2  (id="operation_2")
    # CUSTOMIZE: 逐步展示算法执行过程
    # ══════════════════════════════════════════════
    def _operation_2(self):
        # FILL_IN: 按具体算法填写步骤动画
        # 下方为二叉树中序遍历示例结构，其他算法类似修改

        # 访问顺序徽章列表（最终存入 self._badges）
        self._badges = []

        # FILL_IN: 按遍历顺序依次执行以下模式（中序：D→B→E→A→C）
        # 模式：当前节点→高亮琥珀→访问→高亮蓝→放编号徽章
        visit_order = ["D", "B", "E", "A", "C"]   # FILL_IN

        for i, nid in enumerate(visit_order):
            node = self._tree_nodes[nid]
            # 1. 设为当前节点（琥珀）
            self.play(self.set_node_state(node, "current"),
                      Indicate(node, scale_factor=1.3, color=C_NODE_CURRENT),
                      run_time=0.5)
            self.wait(0.5)
            # 2. 访问：变蓝 + 放顺序徽章
            badge = self.visit_badge(i + 1, node.get_center())
            self._badges.append(badge)
            self.play(self.set_node_state(node, "visited"),
                      FadeIn(badge),
                      run_time=0.4)
            # 3. 回溯时显示虚线箭头（非叶子节点返回时）
            # FILL_IN: 若需要回溯效果，取消注释并填写父子位置
            # backtrack = DashedLine(node.get_center(), parent_node.get_center(),
            #                        color="#94a3b8", dash_length=0.12, stroke_width=1.5)
            # self.play(Create(backtrack, run_time=0.3))
            self.wait(0.3)

        self.wait(3.0)   # CUSTOMIZE: 旁白结束等待

    # ══════════════════════════════════════════════
    # Segment 6: result  (id="result")
    # CUSTOMIZE: 显示最终结果
    # ══════════════════════════════════════════════
    def _result(self):
        # 所有节点变绿色
        all_nodes = list(self._tree_nodes.values())   # FILL_IN: 替换为对应的节点列表
        self.play(
            AnimationGroup(
                *[self.set_node_state(n, "result") for n in all_nodes],
                lag_ratio=0.1
            ),
            run_time=0.8,
        )

        # FILL_IN: 结果文字（如"[4, 2, 5, 1, 3]"）
        res = self.result_box("FILL_IN_结果文字", font_size=28)
        res.to_edge(DOWN, buff=0.8)
        self.play(DrawBorderThenFill(res[0]), run_time=0.4)
        self.play(FadeIn(res[1]),             run_time=0.4)
        self.wait(5.0)   # CUSTOMIZE

        self._result_grp = VGroup(*all_nodes, *self._badges, res)

    # ══════════════════════════════════════════════
    # Segment 7: summary  (id="summary")
    # CUSTOMIZE: 修改最终答案和关键提示文字
    # ══════════════════════════════════════════════
    def _summary(self):
        # 清空上一段
        self.play(FadeOut(self._result_grp), run_time=0.5)

        # FILL_IN: 问题回顾（如"中序遍历结果 ="）
        q_txt = self.tx("FILL_IN_问题回顾", font_size=34, color=C_MUTED)
        q_txt.move_to(UP * 1.8)

        # FILL_IN: 大号最终答案（如"[4, 2, 5, 1, 3]"）
        ans = self.result_box("FILL_IN_最终答案", font_size=52)
        ans.next_to(q_txt, DOWN, buff=0.4)
        ans[1].move_to(ans[0])

        # FILL_IN: 关键提示（如"💡 左→根→右，O(n)"）
        hint = self.insight_box("💡 FILL_IN_关键规则和复杂度")
        hint.next_to(ans[0], DOWN, buff=0.5)
        hint[1].move_to(hint[0])

        self.play(FadeIn(q_txt, shift=UP * 0.3),    run_time=0.5)
        self.play(DrawBorderThenFill(ans[0]),        run_time=0.5)
        self.play(FadeIn(ans[1]),                    run_time=0.5)
        self.play(DrawBorderThenFill(hint[0]),       run_time=0.4)
        self.play(FadeIn(hint[1]),                   run_time=0.4)
        self.wait(8.0)   # CUSTOMIZE
