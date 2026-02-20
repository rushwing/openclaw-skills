#!/usr/bin/env python3
"""
Generate a Manim animation script from a storyboard JSON.

Usage:
    python generate_manim.py <storyboard_json> <output_py>

The output Python file can then be rendered with:
    manim -pql <output_py> TutorScene         # low quality preview
    manim -pqh <output_py> TutorScene         # high quality

Storyboard JSON format:
{
    "title": "正方形面积问题",
    "subject": "数学",
    "segments": [
        {
            "id": "intro",
            "type": "title",
            "title": "正方形面积问题",
            "subtitle": "设边长，列方程，求解",
            "narration": "同学，我们来看这道题。"
        },
        {
            "id": "problem",
            "type": "problem_statement",
            "lines": [
                "已知正方形面积为 $64 \\\\text{ cm}^2$，",
                "求其边长和周长。"
            ],
            "highlight": null,
            "narration": "题目给出..."
        },
        {
            "id": "step1",
            "type": "solution_step",
            "step_number": 1,
            "step_title": "设定未知数",
            "content_lines": [
                "设正方形边长为 $x \\\\text{ cm}$"
            ],
            "formula": "$x > 0$",
            "highlight_color": "#7c3aed",
            "narration": "第一步，设边长为 x。"
        },
        {
            "id": "step2",
            "type": "solution_step",
            "step_number": 2,
            "step_title": "建立方程",
            "content_lines": [
                "由面积公式得："
            ],
            "formula": "$x^2 = 64$",
            "highlight_color": "#2563eb",
            "narration": "根据面积公式..."
        },
        {
            "id": "step3",
            "type": "solution_step",
            "step_number": 3,
            "step_title": "求解方程",
            "content_lines": [
                "两边开平方："
            ],
            "formula": "$x = \\\\sqrt{64} = 8$",
            "highlight_color": "#059669",
            "narration": "对两边开平方得 x 等于 8。"
        },
        {
            "id": "summary",
            "type": "summary",
            "title": "解题总结",
            "points": [
                "边长：$8 \\\\text{ cm}$",
                "周长：$4 \\\\times 8 = 32 \\\\text{ cm}$"
            ],
            "key_insight": "面积 → 开方 → 边长",
            "narration": "所以边长是 8 厘米，周长是 32 厘米。"
        }
    ]
}

Step highlight colors (suggested palette):
    Step 1: #7c3aed (purple)
    Step 2: #2563eb (blue)
    Step 3: #059669 (green)
    Step 4: #d97706 (amber)
    Step 5: #dc2626 (red)
    Step 6: #0891b2 (cyan)
"""

import sys
import json
from pathlib import Path
from textwrap import indent


STEP_COLORS = ["#7c3aed", "#2563eb", "#059669", "#d97706", "#dc2626", "#0891b2"]

MANIM_HEADER = '''\
from manim import *

# Chinese font support — set MANIM_FONT env var or edit below
CHINESE_FONT = "PingFang SC"   # macOS; try "Noto Sans CJK SC" on Linux


class TutorScene(Scene):
    """Auto-generated educational animation. Run with:
        manim -pql {output_name} TutorScene
    """

    def construct(self):
        config.background_color = "#0f172a"
        self._run_all_segments()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _tx(self, text, **kw):
        """Create a Text object with the project font."""
        return Text(text, font=CHINESE_FONT, **kw)

    def _panel(self, color="#1e293b", width=13, height=7.5):
        return RoundedRectangle(corner_radius=0.3, width=width, height=height,
                                fill_color=color, fill_opacity=1,
                                stroke_color=color, stroke_width=0)

    def _highlight_box(self, mobject, color, padding=0.2):
        return SurroundingRectangle(mobject, color=color,
                                    corner_radius=0.1,
                                    buff=padding,
                                    stroke_width=3)

    def _step_badge(self, number, color):
        circle = Circle(radius=0.28, fill_color=color,
                        fill_opacity=1, stroke_width=0)
        label  = self._tx(str(number), font_size=18, color=WHITE, weight=BOLD)
        label.move_to(circle)
        return VGroup(circle, label)

    def _run_all_segments(self):
'''


def escape_latex(s: str) -> str:
    """Escape backslashes already escaped in JSON."""
    return s


def segment_intro(seg: dict) -> str:
    title    = seg.get("title", "")
    subtitle = seg.get("subtitle", "")
    return f'''\
        # ── INTRO ──────────────────────────────────────────────────
        title_txt = self._tx("{title}", font_size=52, weight=BOLD, color=WHITE)
        sub_txt   = self._tx("{subtitle}", font_size=28, color="#94a3b8")
        sub_txt.next_to(title_txt, DOWN, buff=0.4)
        group = VGroup(title_txt, sub_txt).move_to(ORIGIN)

        self.play(FadeIn(title_txt, shift=UP*0.3), run_time=0.8)
        self.play(FadeIn(sub_txt),                 run_time=0.5)
        self.wait(2)
        self.play(FadeOut(group),                  run_time=0.5)
'''


def segment_problem(seg: dict) -> str:
    lines = seg.get("lines", [])
    figure_code_lines = seg.get("manim_figure_code") or []
    has_figure = bool(figure_code_lines)

    line_code = "\n".join(
        f'        line{i} = self._tx("{l}", font_size=30, color="#e2e8f0")'
        for i, l in enumerate(lines)
    )
    vgroup_items = ", ".join(f"line{i}" for i in range(len(lines)))

    if has_figure:
        # Indent each line of the caller-supplied Manim figure code.
        # Convention: last line must be  figure = VGroup(...)
        indented_figure = "\n".join(f"        {l}" for l in figure_code_lines)
        return f'''\
        # ── PROBLEM STATEMENT (Manim figure + text) ────────────────
        label = self._tx("题目", font_size=22, color="#64748b", weight=BOLD)
        label.to_corner(UL, buff=0.5)

{line_code}
        prob_text = VGroup({vgroup_items}).arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        # --- Manim-redrawn geometric figure ---
{indented_figure}
        figure.scale_to_fit_height(3.0)

        content = VGroup(figure, prob_text).arrange(RIGHT, buff=0.6)
        content.move_to(ORIGIN)

        box = RoundedRectangle(corner_radius=0.2,
                               width=content.width + 0.8,
                               height=content.height + 0.6,
                               fill_color="#1e3a5f", fill_opacity=0.8,
                               stroke_color="#3b82f6", stroke_width=2)
        box.move_to(content)

        self.play(FadeIn(label),                           run_time=0.4)
        self.play(DrawBorderThenFill(box),                 run_time=0.5)
        self.play(Create(figure),
                  FadeIn(prob_text, shift=UP*0.1),         run_time=0.9)
        self.wait(2.5)
        self.play(FadeOut(VGroup(label, box, figure, prob_text)), run_time=0.5)
'''
    else:
        return f'''\
        # ── PROBLEM STATEMENT (text only) ──────────────────────────
        label = self._tx("题目", font_size=22, color="#64748b", weight=BOLD)
        label.to_corner(UL, buff=0.5)

{line_code}
        prob_group = VGroup({vgroup_items}).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        prob_group.move_to(ORIGIN)

        box = RoundedRectangle(corner_radius=0.2,
                               width=prob_group.width + 0.8,
                               height=prob_group.height + 0.6,
                               fill_color="#1e3a5f", fill_opacity=0.8,
                               stroke_color="#3b82f6", stroke_width=2)
        box.move_to(prob_group)

        self.play(FadeIn(label),                    run_time=0.4)
        self.play(DrawBorderThenFill(box),          run_time=0.5)
        self.play(FadeIn(prob_group, shift=UP*0.1), run_time=0.7)
        self.wait(2.5)
        self.play(FadeOut(VGroup(label, box, prob_group)), run_time=0.5)
'''


def segment_solution_step(seg: dict) -> str:
    num      = seg.get("step_number", 1)
    title    = seg.get("step_title", f"步骤 {num}")
    contents = seg.get("content_lines", [])
    formula  = seg.get("formula", "")
    color    = seg.get("highlight_color", STEP_COLORS[(num - 1) % len(STEP_COLORS)])

    # Build content line code
    content_code = "\n".join(
        f'        c{i} = self._tx("{l}", font_size=28, color="#e2e8f0")'
        for i, l in enumerate(contents)
    )
    content_vars = ", ".join(f"c{i}" for i in range(len(contents)))
    content_group = (
        f"        content_group = VGroup({content_vars}).arrange(DOWN, aligned_edge=LEFT, buff=0.15)"
        if contents else
        "        content_group = VGroup()"
    )

    formula_block = ""
    if formula:
        formula_block = f'''\
        formula_tex = MathTex(r"{formula.strip('$')}", color=WHITE, font_size=38)
        formula_box = BackgroundRectangle(formula_tex,
                                          color="{color}",
                                          fill_opacity=0.25,
                                          buff=0.2)
        formula_grp = VGroup(formula_box, formula_tex)
        formula_grp.next_to(content_group, DOWN, buff=0.3)
        step_all = VGroup(badge_grp, step_title_txt, content_group, formula_grp)
        step_all.arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        step_all.move_to(ORIGIN)
        self.play(FadeIn(step_title_txt, badge_grp),       run_time=0.5)
        self.play(FadeIn(content_group, shift=RIGHT*0.1),  run_time=0.5)
        self.play(FadeIn(formula_box), Write(formula_tex), run_time=0.7)
        indicator = self._highlight_box(formula_tex, "{color}")
        self.play(Create(indicator),    run_time=0.4)
        self.wait(2)
        self.play(FadeOut(VGroup(badge_grp, step_title_txt, content_group, formula_grp, indicator)),
                  run_time=0.5)'''
    else:
        formula_block = f'''\
        step_all = VGroup(badge_grp, step_title_txt, content_group)
        step_all.arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        step_all.move_to(ORIGIN)
        self.play(FadeIn(step_title_txt, badge_grp),      run_time=0.5)
        self.play(FadeIn(content_group, shift=RIGHT*0.1), run_time=0.5)
        self.wait(2)
        self.play(FadeOut(step_all), run_time=0.5)'''

    return f'''\
        # ── STEP {num}: {title} ──────────────────────────────────
        badge_grp      = self._step_badge({num}, "{color}")
        step_title_txt = self._tx("  {title}", font_size=30, color="{color}", weight=BOLD)
        step_title_txt.next_to(badge_grp, RIGHT, buff=0.1)
        header_row = VGroup(badge_grp, step_title_txt).arrange(RIGHT, buff=0.1)
        header_row.to_corner(UL, buff=0.5)

{content_code}
{content_group}
        content_group.next_to(header_row, DOWN, buff=0.4).shift(RIGHT * 0.5)

{formula_block}
'''


def segment_summary(seg: dict) -> str:
    title   = seg.get("title", "解题总结")
    points  = seg.get("points", [])
    insight = seg.get("key_insight", "")

    points_code = "\n".join(
        f'        pt{i} = self._tx("✓  {p}", font_size=26, color="#86efac")'
        for i, p in enumerate(points)
    )
    points_vars = ", ".join(f"pt{i}" for i in range(len(points)))

    return f'''\
        # ── SUMMARY ────────────────────────────────────────────────
        sum_title = self._tx("{title}", font_size=36, weight=BOLD, color="#f59e0b")
        sum_title.to_edge(UP, buff=0.8)

{points_code}
        pts_group = VGroup({points_vars}).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        pts_group.next_to(sum_title, DOWN, buff=0.5)

        insight_txt = self._tx("💡  {insight}", font_size=24, color="#fbbf24")
        insight_box = RoundedRectangle(corner_radius=0.15,
                                       width=insight_txt.width + 0.8,
                                       height=insight_txt.height + 0.4,
                                       fill_color="#451a03", fill_opacity=0.7,
                                       stroke_color="#f59e0b", stroke_width=2)
        insight_box.next_to(pts_group, DOWN, buff=0.4)
        insight_txt.move_to(insight_box)

        self.play(Write(sum_title),                               run_time=0.6)
        self.play(FadeIn(pts_group, shift=UP*0.1, lag_ratio=0.2), run_time=0.8)
        self.play(DrawBorderThenFill(insight_box),                run_time=0.4)
        self.play(FadeIn(insight_txt),                            run_time=0.3)
        self.wait(3)
        self.play(FadeOut(VGroup(sum_title, pts_group, insight_box, insight_txt)),
                  run_time=0.6)
'''


DISPATCH = {
    "title":            segment_intro,
    "problem_statement": segment_problem,
    "solution_step":    segment_solution_step,
    "summary":          segment_summary,
}


def generate(storyboard: dict) -> str:
    output_name = "TutorScene.py"
    code = MANIM_HEADER.format(output_name=output_name)

    for seg in storyboard.get("segments", []):
        seg_type = seg.get("type", "")
        handler  = DISPATCH.get(seg_type)
        if handler:
            code += indent(handler(seg), "        ") + "\n"
        else:
            code += f"        # Unknown segment type: {seg_type}\n"

    # Close the method and class
    code += "        self.wait(1)\n"
    return code


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_manim.py <storyboard_json> <output_py>")
        sys.exit(1)

    storyboard_path = Path(sys.argv[1])
    output_path     = Path(sys.argv[2])

    with open(storyboard_path, encoding="utf-8") as f:
        storyboard = json.load(f)

    code = generate(storyboard)
    output_path.write_text(code, encoding="utf-8")

    print(f"Generated Manim script: {output_path}")
    print(f"\nRender with:")
    print(f"  manim -pql {output_path} TutorScene   # quick preview")
    print(f"  manim -pqh {output_path} TutorScene   # high quality")


if __name__ == "__main__":
    main()
