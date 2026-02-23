"""
TutorScene_template.py
======================
小学数学解题教学视频 —— Manim动画模板

使用说明：
1. 搜索所有 CUSTOMIZE: 注释，填入本题的具体参数
2. 搜索所有 FILL_IN 占位符，替换为实际文字/坐标
3. 每个 segment 方法对应 narration.json 中的一个 id
4. self.wait() 的秒数 = 对应音频时长 - 本段动画时长
"""

from manim import *
import numpy as np

# ══════════════════════════════════════════════════════
# CUSTOMIZE: 全局字体
# ══════════════════════════════════════════════════════
FONT = "PingFang SC"   # macOS：PingFang SC | Windows：Microsoft YaHei

# ══════════════════════════════════════════════════════
# CUSTOMIZE: 颜色方案（保持不变即可，已调好可读性）
# ══════════════════════════════════════════════════════
C_BG          = "#0f172a"   # 背景深蓝黑
C_TEXT        = "#e2e8f0"   # 正文白
C_MUTED       = "#94a3b8"   # 淡灰（副标题/小标签）
C_BLUE        = "#3b82f6"   # 主蓝（边框/主图形）
C_BLUE_LIGHT  = "#60a5fa"   # 浅蓝（辅助线）
C_BLUE_FILL   = "#93c5fd"   # 更浅蓝（面积标注）
C_SHADE_FILL  = "#3b82f6"   # 阴影区域填充色
C_AMBER       = "#f59e0b"   # 琥珀（外部三角形）
C_AMBER_STK   = "#fbbf24"
C_RED         = "#ef4444"   # 红（内部三角形）
C_RED_STK     = "#f87171"
C_GREEN       = "#34d399"   # 绿（最终答案）
C_GREEN_DARK  = "#064e3b"
C_PURPLE      = "#c4b5fd"   # 紫（中间结果）
C_PURPLE_DARK = "#4c1d95"
C_TEAL        = "#10b981"   # 青绿（化整为零标题）
C_ORANGE_DARK = "#451a03"

# ══════════════════════════════════════════════════════
# CUSTOMIZE: 几何坐标
#   - 图形整体向左偏移 GS，为右侧公式留出空间
#   - 推荐：正方形边长 = 2.5 Manim 单位
#   - 推荐：GS = (-2.0, 0, 0)
# ══════════════════════════════════════════════════════
GS = np.array([-2.0, 0.0, 0.0])   # 图形全局偏移

# --- 以下坐标全部加上 GS ---
# FILL_IN: 根据题目图形修改各顶点坐标
# 示例：正方形 ABCD，边长 2.5，中心在 GS
HALF = 1.25   # 正方形边长的一半 = 2.5 / 2

A_PT = np.array([-HALF,  HALF, 0]) + GS   # FILL_IN: 顶点A（建议：左上）
B_PT = np.array([-HALF, -HALF, 0]) + GS   # FILL_IN: 顶点B（建议：左下）
C_PT = np.array([ HALF, -HALF, 0]) + GS   # FILL_IN: 顶点C（建议：右下）
D_PT = np.array([ HALF,  HALF, 0]) + GS   # FILL_IN: 顶点D（建议：右上）

# FILL_IN: 中点/特殊点
M_PT = np.array([0.00,  HALF, 0]) + GS    # FILL_IN: 中点M（AD中点示例）
N_PT = np.array([HALF,  0.00, 0]) + GS    # FILL_IN: 中点N（DC中点示例）

# FILL_IN: 外部图形顶点（如三角形顶点）
F_PT = np.array([-HALF,  2 * HALF, 0]) + GS   # FILL_IN: 外部顶点F
E_PT = np.array([ 2 * HALF, -HALF, 0]) + GS   # FILL_IN: 外部顶点E


# ══════════════════════════════════════════════════════
class TutorScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        # 按顺序调用 7 个 segment
        self._intro()
        self._problem()
        self._draw_figure()
        self._three_triangles()    # CUSTOMIZE: 根据题目改名，如 _key_insight()
        self._calculate()
        self._assemble()
        self._summary()
        self.wait(1)

    # ── 通用 helper ──────────────────────────────────
    def tx(self, text, **kw):
        """创建 Text 对象，默认使用全局字体"""
        return Text(text, font=FONT, **kw)

    def centroid(self, *pts):
        """计算多个点的重心，用于放置三角形标签"""
        return sum(pts) / len(pts)

    def right_panel_title(self, text, color=C_AMBER):
        """右侧面板小节标题，统一位置"""
        t = self.tx(text, font_size=22, color=color, weight=BOLD)
        t.to_corner(UR, buff=0.6).shift(DOWN * 0.8)
        return t

    # ══════════════════════════════════════════════════
    # Segment 1: intro  (对应 narration.json id="intro")
    # CUSTOMIZE: 替换文字；self.wait() 参数 = 音频时长 - 动画时长
    # ══════════════════════════════════════════════════
    def _intro(self):
        # FILL_IN: 主标题（方法名称）
        title = self.tx("FILL_IN_方法名称", font_size=58, weight=BOLD, color=WHITE)
        # FILL_IN: 副标题（题目类型描述）
        sub = self.tx("FILL_IN_题目类型描述", font_size=24, color=C_MUTED)
        sub.next_to(title, DOWN, buff=0.5)
        grp = VGroup(title, sub)

        self.play(FadeIn(title, shift=UP * 0.3), run_time=0.8)
        self.play(FadeIn(sub), run_time=0.5)
        self.wait(3.7)   # CUSTOMIZE: 总时长 ≈ 音频时长（秒）
        self.play(FadeOut(grp), run_time=0.5)

    # ══════════════════════════════════════════════════
    # Segment 2: problem  (对应 id="problem")
    # CUSTOMIZE: 填入题目文字，调整 self.wait()
    # ══════════════════════════════════════════════════
    def _problem(self):
        lbl = self.tx("题  目", font_size=18, color=C_MUTED, weight=BOLD)
        lbl.to_corner(UL, buff=0.5)

        # FILL_IN: 题目拆成 3~5 行，每行不超过 22 字
        lines_txt = [
            "FILL_IN_第一行：图形关系",
            "FILL_IN_第二行：已知条件",
            "FILL_IN_第三行：已知条件",
            "FILL_IN_第四行：求什么？",
        ]
        lines = [self.tx(t, font_size=26, color=C_TEXT) for t in lines_txt]
        prob = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        prob.move_to(ORIGIN)
        bg = RoundedRectangle(
            corner_radius=0.2,
            width=prob.width + 1.0,
            height=prob.height + 0.8,
            fill_color="#1e3a5f", fill_opacity=0.85,
            stroke_color=C_BLUE, stroke_width=2,
        ).move_to(prob)

        self.play(FadeIn(lbl), run_time=0.3)
        self.play(DrawBorderThenFill(bg), run_time=0.6)
        self.play(FadeIn(prob, shift=UP * 0.1), run_time=0.8)
        self.wait(13.3)  # CUSTOMIZE
        self.play(FadeOut(VGroup(lbl, bg, prob)), run_time=0.5)

    # ══════════════════════════════════════════════════
    # Segment 3: draw_figure  (对应 id="figure")
    # CUSTOMIZE: 根据题目图形修改所有几何对象
    # ══════════════════════════════════════════════════
    def _draw_figure(self):
        # ── 阴影区域 (FILL_IN: 修改顶点) ──
        shaded = Polygon(
            A_PT, B_PT, C_PT, N_PT, M_PT,   # FILL_IN: 阴影多边形顶点
            fill_color=C_SHADE_FILL, fill_opacity=0.30, stroke_width=0,
        )

        # ── 主图形轮廓（如正方形）──
        main_shape = Polygon(
            A_PT, B_PT, C_PT, D_PT,         # FILL_IN: 主图形顶点
            fill_opacity=0, stroke_color=WHITE, stroke_width=2.5,
        )

        # ── 辅助线（FILL_IN: 根据题目添加或删除）──
        aux_line_1 = Line(A_PT, F_PT, color=C_BLUE_LIGHT, stroke_width=2)
        aux_line_2 = Line(C_PT, E_PT, color=C_BLUE_LIGHT, stroke_width=2)

        # ── 斜线/斜边（虚线 + 实线，FILL_IN）──
        hyp_dashed_1 = DashedLine(F_PT, M_PT, dash_length=0.14,
                                  dashed_ratio=0.5, color=C_BLUE_LIGHT, stroke_width=1.8)
        hyp_solid    = Line(M_PT, N_PT, color=C_BLUE_LIGHT, stroke_width=2.5)
        hyp_dashed_2 = DashedLine(N_PT, E_PT, dash_length=0.14,
                                  dashed_ratio=0.5, color=C_BLUE_LIGHT, stroke_width=1.8)

        # ── 顶点标签 helper ──
        def vt(text, pos, color=C_TEXT):
            return self.tx(text, font_size=22, color=color).move_to(pos)

        # FILL_IN: 每个标签的偏移方向（避免遮挡图形）
        lbl_A = vt("A", A_PT + np.array([-0.25,  0.22, 0]))
        lbl_B = vt("B", B_PT + np.array([-0.25, -0.22, 0]))
        lbl_C = vt("C", C_PT + np.array([ 0.25, -0.22, 0]))
        lbl_D = vt("D", D_PT + np.array([ 0.25,  0.22, 0]))
        lbl_M = vt("M", M_PT + np.array([ 0.00,  0.28, 0]))
        lbl_N = vt("N", N_PT + np.array([ 0.30,  0.00, 0]))
        lbl_F = vt("F", F_PT + np.array([-0.25,  0.22, 0]), color=C_BLUE_LIGHT)
        lbl_E = vt("E", E_PT + np.array([ 0.25, -0.22, 0]), color=C_BLUE_LIGHT)

        dot_M = Dot(M_PT, radius=0.08, color=YELLOW)
        dot_N = Dot(N_PT, radius=0.08, color=YELLOW)

        # FILL_IN: 阴影面积标注文字和位置
        shade_num = self.tx("14 cm²", font_size=22, color=C_BLUE_FILL)
        shade_num.move_to(np.array([-2.8, -0.5, 0]))   # FILL_IN: 调整位置

        # ── 动画序列 ──
        self.play(FadeIn(shaded), run_time=0.6)
        self.play(Create(main_shape), run_time=0.8)
        self.play(FadeIn(lbl_A, lbl_B, lbl_C, lbl_D), run_time=0.5)
        self.play(
            Create(aux_line_1), Create(aux_line_2),
            Create(hyp_dashed_1), Create(hyp_solid), Create(hyp_dashed_2),
            run_time=0.8,
        )
        self.play(FadeIn(lbl_F, lbl_E), run_time=0.4)
        self.play(FadeIn(dot_M, dot_N, lbl_M, lbl_N), run_time=0.5)
        self.play(FadeIn(shade_num), run_time=0.4)

        # 存储供后续 segment 使用
        self._fig = VGroup(
            shaded, main_shape,
            aux_line_1, aux_line_2,
            hyp_dashed_1, hyp_solid, hyp_dashed_2,
            lbl_A, lbl_B, lbl_C, lbl_D,
            lbl_M, lbl_N, lbl_F, lbl_E,
            dot_M, dot_N, shade_num,
        )
        self.wait(7.0)   # CUSTOMIZE

    # ══════════════════════════════════════════════════
    # Segment 4: key_insight / three_triangles  (对应 id="triangles")
    # CUSTOMIZE: 修改三角形顶点、颜色、标签、说明文字
    # ══════════════════════════════════════════════════
    def _three_triangles(self):
        # FILL_IN: 三个关键三角形（颜色规律：外部=琥珀，内部=红色）
        tri_1 = Polygon(
            A_PT, M_PT, F_PT,   # FILL_IN: 第1个三角形顶点（图形外部）
            fill_color=C_AMBER, fill_opacity=0.55,
            stroke_color=C_AMBER_STK, stroke_width=2,
        )
        tri_2 = Polygon(
            M_PT, D_PT, N_PT,   # FILL_IN: 第2个三角形顶点（图形内部）
            fill_color=C_RED, fill_opacity=0.55,
            stroke_color=C_RED_STK, stroke_width=2,
        )
        tri_3 = Polygon(
            C_PT, N_PT, E_PT,   # FILL_IN: 第3个三角形顶点（图形外部）
            fill_color=C_AMBER, fill_opacity=0.55,
            stroke_color=C_AMBER_STK, stroke_width=2,
        )

        # FILL_IN: 标签文字（三角形名称）
        lbl_1 = self.tx("△AMF", font_size=17, color=C_AMBER_STK)
        lbl_1.move_to(self.centroid(A_PT, M_PT, F_PT))

        lbl_2 = self.tx("△MDN", font_size=17, color=C_RED_STK)
        lbl_2.move_to(self.centroid(M_PT, D_PT, N_PT))

        lbl_3 = self.tx("△CNE", font_size=17, color=C_AMBER_STK)
        lbl_3.move_to(self.centroid(C_PT, N_PT, E_PT))

        # FILL_IN: 底部关键结论文字
        note = self.tx(
            "三个全等的等腰直角小三角形！",   # FILL_IN
            font_size=26, color=C_AMBER_STK, weight=BOLD,
        )
        note.to_edge(DOWN, buff=0.8)

        self.play(FadeIn(tri_1, lbl_1), run_time=0.7)
        self.wait(0.5)
        self.play(FadeIn(tri_2, lbl_2), run_time=0.7)
        self.wait(0.5)
        self.play(FadeIn(tri_3, lbl_3), run_time=0.7)
        self.wait(0.5)
        self.play(
            Indicate(tri_1, color=C_AMBER_STK, scale_factor=1.15),
            Indicate(tri_2, color=C_RED_STK,   scale_factor=1.15),
            Indicate(tri_3, color=C_AMBER_STK, scale_factor=1.15),
            run_time=1.0,
        )
        self.play(FadeIn(note), run_time=0.5)
        self.wait(15.9)   # CUSTOMIZE
        self.play(FadeOut(note), run_time=0.3)

        # 存储供后续使用（注意顺序：tri_1=idx0, tri_2=idx1, tri_3=idx2）
        self._tris = VGroup(tri_1, tri_2, tri_3, lbl_1, lbl_2, lbl_3)

    # ══════════════════════════════════════════════════
    # Segment 5: calculate  (对应 id="calculate")
    # CUSTOMIZE: 修改推导文字和最终小结果
    # ══════════════════════════════════════════════════
    def _calculate(self):
        title = self.right_panel_title("FILL_IN_小节标题（如：求小三角形的面积）")

        # FILL_IN: 两行推导步骤
        eq1 = self.tx("FILL_IN_推导步骤1", font_size=19, color=C_TEXT)
        eq1.next_to(title, DOWN, buff=0.4).align_to(title, LEFT)

        eq2 = self.tx("FILL_IN_推导步骤2", font_size=19, color=C_TEXT)
        eq2.next_to(eq1, DOWN, buff=0.25).align_to(eq1, LEFT)

        # FILL_IN: 中间结果（如「△MDN = 14÷7 = 2 cm²」）
        result_txt = self.tx(
            "FILL_IN_中间结果",
            font_size=21, color=C_PURPLE, weight=BOLD,
        )
        result_txt.next_to(eq2, DOWN, buff=0.4).align_to(eq2, LEFT)
        result_box = SurroundingRectangle(
            result_txt, corner_radius=0.12, buff=0.18,
            fill_color=C_PURPLE_DARK, fill_opacity=0.4,
            stroke_color=C_PURPLE, stroke_width=2,
        )

        self.play(FadeIn(title), run_time=0.4)
        self.play(FadeIn(eq1), run_time=0.5)
        self.play(FadeIn(eq2), run_time=0.5)
        self.wait(1.0)
        self.play(DrawBorderThenFill(result_box), run_time=0.4)
        self.play(FadeIn(result_txt), run_time=0.4)
        # CUSTOMIZE: 高亮对应三角形（self._tris[1] = 内部三角形）
        self.play(Indicate(self._tris[1], color=C_RED, scale_factor=1.2), run_time=0.8)
        self.wait(13.4)   # CUSTOMIZE

        self._calc_grp = VGroup(title, eq1, eq2, result_box, result_txt)

    # ══════════════════════════════════════════════════
    # Segment 6: assemble  (对应 id="assemble")
    # CUSTOMIZE: 修改拼合公式和最终答案
    # ══════════════════════════════════════════════════
    def _assemble(self):
        title = self.right_panel_title("化整为零！", color=C_TEAL)   # FILL_IN

        # FILL_IN: 拼合公式（面积 = 各部分之和）
        eq1 = self.tx("FILL_IN_拼合公式（如△BEF = 阴影+△AMF+△CNE）",
                      font_size=18, color=C_TEXT)
        eq1.next_to(title, DOWN, buff=0.4).align_to(title, LEFT)

        # FILL_IN: 代入数值
        eq2 = self.tx("FILL_IN_代入数值（如= 14 + 2 + 2）",
                      font_size=21, color=C_TEXT)
        eq2.next_to(eq1, DOWN, buff=0.3).align_to(eq1, LEFT)

        # FILL_IN: 最终答案
        ans_txt = self.tx("FILL_IN_最终答案（如= 18 cm²）",
                          font_size=30, color=C_GREEN, weight=BOLD)
        ans_txt.next_to(eq2, DOWN, buff=0.35).align_to(eq2, LEFT)
        ans_box = SurroundingRectangle(
            ans_txt, corner_radius=0.15, buff=0.2,
            fill_color=C_GREEN_DARK, fill_opacity=0.5,
            stroke_color=C_GREEN, stroke_width=2.5,
        )

        self.play(FadeOut(self._calc_grp), run_time=0.4)
        self.play(FadeIn(title), run_time=0.4)
        self.play(FadeIn(eq1), run_time=0.5)
        self.play(FadeIn(eq2), run_time=0.5)
        # CUSTOMIZE: 高亮外部两个三角形
        self.play(
            Indicate(self._tris[0], color=C_AMBER_STK),
            Indicate(self._tris[2], color=C_AMBER_STK),
            run_time=0.8,
        )
        self.play(DrawBorderThenFill(ans_box), FadeIn(ans_txt), run_time=0.6)
        self.wait(7.7)   # CUSTOMIZE

        self._asm_grp = VGroup(title, eq1, eq2, ans_box, ans_txt)
        self.play(
            FadeOut(self._fig),
            FadeOut(self._tris),
            FadeOut(self._asm_grp),
            run_time=0.6,
        )

    # ══════════════════════════════════════════════════
    # Segment 7: summary  (对应 id="summary")
    # CUSTOMIZE: 修改最终答案数字和关键提示文字
    # ══════════════════════════════════════════════════
    def _summary(self):
        # FILL_IN: 问题回顾（如「三角形 BEF 的面积 =」）
        q_txt = self.tx("FILL_IN_问题回顾", font_size=34, color=C_MUTED)
        q_txt.move_to(UP * 1.8)

        # FILL_IN: 大号最终答案（如「18 cm²」）
        ans_num = self.tx("FILL_IN_最终答案", font_size=64, color=C_GREEN, weight=BOLD)
        ans_num.next_to(q_txt, DOWN, buff=0.4)
        ans_box = SurroundingRectangle(
            ans_num, corner_radius=0.2, buff=0.35,
            fill_color=C_GREEN_DARK, fill_opacity=0.6,
            stroke_color=C_GREEN, stroke_width=3,
        )

        # FILL_IN: 解题关键提示（一行，不超过25字）
        insight_txt = self.tx(
            "💡 FILL_IN_解题关键提示",
            font_size=22, color=C_AMBER_STK,
        )
        insight_box = SurroundingRectangle(
            insight_txt, corner_radius=0.15, buff=0.2,
            fill_color=C_ORANGE_DARK, fill_opacity=0.6,
            stroke_color=C_AMBER, stroke_width=2,
        )
        insight_box.next_to(ans_num, DOWN, buff=0.7)
        insight_txt.move_to(insight_box)

        self.play(FadeIn(q_txt, shift=UP * 0.3), run_time=0.5)
        self.play(DrawBorderThenFill(ans_box), run_time=0.5)
        self.play(FadeIn(ans_num), run_time=0.6)
        self.play(DrawBorderThenFill(insight_box), run_time=0.4)
        self.play(FadeIn(insight_txt), run_time=0.4)
        self.wait(12.0)   # CUSTOMIZE
