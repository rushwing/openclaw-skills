#!/usr/bin/env python3
"""
Generate a Manim animation script from a storyboard JSON.

Usage:
    python generate_manim.py <storyboard_json> <output_py>

The output Python file can then be rendered with:
    manim -pql <output_py> TutorScene         # low quality preview
    manim -pqh <output_py> TutorScene         # high quality

Supported segment types
-----------------------
Legacy (v1):
    title, problem_statement, solution_step, summary

New (v2, from updated SKILL.md):
    title_card, text_card, geometry_drawing, highlight_geometry,
    equation_steps, final_equation, answer_reveal

Storyboard JSON format (v2 example):
{
    "title": "正方形面积问题",
    "subject": "数学",
    "segments": [
        {
            "id": "intro",
            "type": "title_card",
            "narration": "...",
            "visual": {
                "elements": [
                    {"role": "主标题", "text": "方法名"},
                    {"role": "副标题", "text": "题目类型"}
                ]
            }
        },
        ...
    ]
}
"""

import re
import sys
import json
from pathlib import Path


# ── Colour palette (matches TutorScene_template.py) ─────────────────────────
STEP_COLORS = ["#7c3aed", "#2563eb", "#059669", "#d97706", "#dc2626", "#0891b2"]

# ── Regex helpers ────────────────────────────────────────────────────────────
_CJK_RE      = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]')
_HEX_RE      = re.compile(r'(?:fill|color|stroke|background)\s*[=:]\s*(#[0-9a-fA-F]{6})', re.I)
_OPACITY_RE  = re.compile(r'(?:opacity|fill_opacity)\s*[=:]\s*([\d.]+)', re.I)
_FONTSIZE_RE = re.compile(r'font_size\s*[=:]\s*(\d+)', re.I)


def has_chinese(s: str) -> bool:
    return bool(_CJK_RE.search(s))


def _col(style: str, el: dict, default: str = "#ffffff") -> str:
    """Extract the first hex colour from element dict keys or style string."""
    for key in ("fill", "color", "stroke"):
        v = el.get(key, "")
        if isinstance(v, str) and v.startswith("#"):
            return v
    m = _HEX_RE.search(style)
    return m.group(1) if m else default


def _opac(style: str, el: dict, default: float = 1.0) -> float:
    for key in ("opacity", "fill_opacity"):
        v = el.get(key)
        if v is not None:
            return float(v)
    m = _OPACITY_RE.search(style)
    return float(m.group(1)) if m else default


def _fsize(style: str, el: dict, default: int = 24) -> int:
    v = el.get("font_size")
    if v is not None:
        return int(v)
    m = _FONTSIZE_RE.search(style)
    return int(m.group(1)) if m else default


def _is_coord_list(vertices) -> bool:
    """Return True when vertices is a list of [x, y, z] arrays (not placeholder strings)."""
    if not isinstance(vertices, list) or len(vertices) == 0:
        return False
    first = vertices[0]
    return isinstance(first, (list, tuple)) and len(first) >= 2


# ── Manim file header ────────────────────────────────────────────────────────
MANIM_HEADER = '''\
from manim import *
import numpy as np

# Chinese font — install with: sudo apt-get install -y fonts-noto-cjk
CHINESE_FONT = "Noto Sans CJK SC"   # Linux/Raspberry Pi; macOS: "PingFang SC"


class TutorScene(Scene):
    """Auto-generated educational animation. Run with:
        manim -pql {output_name} TutorScene
    """

    def construct(self):
        config.background_color = "#0f172a"
        self._fig      = None
        self._tris     = None
        self._calc_grp = None
        self._asm_grp  = None
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
    return s


# ═══════════════════════════════════════════════════════════════════════════ #
#  Legacy segment handlers (v1 storyboard format)
# ═══════════════════════════════════════════════════════════════════════════ #

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
        formula_stripped = formula.strip('$')
        if has_chinese(formula_stripped):
            formula_block = f'''\
        formula_tex = self._tx("{formula_stripped}", font_size=36, color=WHITE)
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
        self.play(FadeIn(formula_box, formula_tex),        run_time=0.7)
        indicator = self._highlight_box(formula_tex, "{color}")
        self.play(Create(indicator),    run_time=0.4)
        self.wait(2)
        self.play(FadeOut(VGroup(badge_grp, step_title_txt, content_group, formula_grp, indicator)),
                  run_time=0.5)'''
        else:
            formula_block = f'''\
        formula_tex = MathTex(r"{formula_stripped}", color=WHITE, font_size=38)
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


# ═══════════════════════════════════════════════════════════════════════════ #
#  New segment handlers (v2 storyboard format)
# ═══════════════════════════════════════════════════════════════════════════ #

def segment_title_card(seg: dict) -> str:
    """type: title_card — full-screen title + subtitle, fades out."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])
    title = subtitle = ""

    for el in elements:
        role = el.get("role", "")
        text = el.get("text", "")
        if "主标题" in role:
            title = text
        elif "副标题" in role:
            subtitle = text

    if not title:
        title = seg.get("title", seg.get("method_name", "解题"))
    if not subtitle:
        subtitle = seg.get("subtitle", seg.get("narration", "")[:30])

    return f'''\
        # ── TITLE CARD ──────────────────────────────────────────────
        title_txt = self._tx("{title}", font_size=58, weight=BOLD, color=WHITE)
        sub_txt   = self._tx("{subtitle}", font_size=24, color="#94a3b8")
        sub_txt.next_to(title_txt, DOWN, buff=0.5)
        group = VGroup(title_txt, sub_txt).move_to(ORIGIN)

        self.play(FadeIn(title_txt, shift=UP*0.3), run_time=0.8)
        self.play(FadeIn(sub_txt),                 run_time=0.5)
        self.wait(3)
        self.play(FadeOut(group),                  run_time=0.5)
'''


def segment_text_card(seg: dict) -> str:
    """type: text_card — rounded blue card with problem text lines."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])
    lines      = []
    label_text = "题  目"

    for el in elements:
        role = el.get("role", "")
        if "角标" in role:
            label_text = el.get("text", label_text)
        elif "文本" in role or ("题目" in role and el.get("lines")):
            el_lines = el.get("lines", [])
            if el_lines:
                lines = el_lines
            elif el.get("text"):
                lines = [el.get("text")]

    if not lines:
        lines = seg.get("lines", [seg.get("narration", "题目内容")])

    line_code = "\n".join(
        f'        tc_line{i} = self._tx("{l}", font_size=26, color="#e2e8f0")'
        for i, l in enumerate(lines)
    )
    vgroup_items = ", ".join(f"tc_line{i}" for i in range(len(lines)))

    return f'''\
        # ── TEXT CARD ───────────────────────────────────────────────
        tc_label = self._tx("{label_text}", font_size=22, color="#64748b", weight=BOLD)
        tc_label.to_corner(UL, buff=0.5)

{line_code}
        tc_group = VGroup({vgroup_items}).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        tc_group.move_to(ORIGIN)

        tc_box = RoundedRectangle(corner_radius=0.2,
                                   width=tc_group.width + 1.0,
                                   height=tc_group.height + 0.8,
                                   fill_color="#1e3a5f", fill_opacity=0.85,
                                   stroke_color="#3b82f6", stroke_width=2)
        tc_box.move_to(tc_group)

        self.play(FadeIn(tc_label),                         run_time=0.3)
        self.play(DrawBorderThenFill(tc_box),               run_time=0.6)
        self.play(FadeIn(tc_group, shift=UP*0.1),           run_time=0.8)
        self.wait(13)
        self.play(FadeOut(VGroup(tc_label, tc_box, tc_group)), run_time=0.5)
'''


def segment_geometry_drawing(seg: dict) -> str:
    """type: geometry_drawing — draws geometric shapes, stores in self._fig."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])

    lines     = ["        # ── GEOMETRY DRAWING ─────────────────────────────────────",
                 "        _fig_parts = []"]
    anim_seq  = []

    for i, el in enumerate(elements):
        role     = el.get("role", "")
        shape    = el.get("shape", "")
        style    = el.get("style", "")
        text     = el.get("text", "")
        vertices = el.get("vertices")
        labels   = el.get("labels", [])
        points   = el.get("points", [])
        var      = f"_gfig{i}"

        # ── Shadow / filled polygon ──────────────────────────────────────
        if "阴影" in role or "shadow" in role.lower():
            if vertices and _is_coord_list(vertices):
                fill_c = _col(style, el, "#3b82f6")
                fill_o = _opac(style, el, 0.30)
                verts_str = ", ".join(f"np.array({list(v)})" for v in vertices)
                lines.append(
                    f'        {var} = Polygon({verts_str},\n'
                    f'            fill_color="{fill_c}", fill_opacity={fill_o}, stroke_width=0)'
                )
                lines.append(f'        _fig_parts.append({var})')
                anim_seq.append(f'FadeIn({var})')
            else:
                lines.append(f'        # TODO: fill in vertices for "{role}"')

        # ── Main shape outline (Square / Polygon) ────────────────────────
        elif "主图形" in role or "轮廓" in role or shape in ("Square", "Rectangle"):
            side   = el.get("side_length", 2.5)
            center = el.get("center", el.get("GS", [-2.0, 0.0, 0.0]))
            if vertices and _is_coord_list(vertices):
                stroke_c = _col(style, el, "#ffffff")
                verts_str = ", ".join(f"np.array({list(v)})" for v in vertices)
                lines.append(
                    f'        {var} = Polygon({verts_str},\n'
                    f'            fill_opacity=0, stroke_color="{stroke_c}", stroke_width=2.5)'
                )
            else:
                lines.append(
                    f'        {var} = Square(side_length={side}, color=WHITE,\n'
                    f'            stroke_width=2.5, fill_opacity=0)\n'
                    f'        {var}.move_to(np.array({center}))'
                )
            lines.append(f'        _fig_parts.append({var})')
            anim_seq.append(f'Create({var})')

        # ── Generic Polygon outline ──────────────────────────────────────
        elif "Polygon" in shape and vertices and _is_coord_list(vertices):
            stroke_c = _col(style, el, "#ffffff")
            fill_c   = el.get("fill", "")
            fill_o   = _opac(style, el, 0.0)
            verts_str = ", ".join(f"np.array({list(v)})" for v in vertices)
            if fill_c:
                lines.append(
                    f'        {var} = Polygon({verts_str},\n'
                    f'            fill_color="{fill_c}", fill_opacity={fill_o},\n'
                    f'            stroke_color="{stroke_c}", stroke_width=2)'
                )
            else:
                lines.append(
                    f'        {var} = Polygon({verts_str},\n'
                    f'            color="{stroke_c}", stroke_width=2, fill_opacity={fill_o})'
                )
            lines.append(f'        _fig_parts.append({var})')
            anim_seq.append(f'Create({var})')

        # ── Vertex labels ────────────────────────────────────────────────
        elif "顶点标签" in role or ("标签" in role and labels):
            if labels:
                lbl_vars = []
                for j, lbl in enumerate(labels):
                    ltext = lbl.get("text", lbl.get("name", ""))
                    lpos  = lbl.get("position", lbl.get("pos", [0, 0, 0]))
                    lvar  = f"_gvlbl{i}_{j}"
                    lines.append(
                        f'        {lvar} = self._tx("{ltext}", font_size=22, color=WHITE)\n'
                        f'        {lvar}.move_to(np.array({list(lpos)}))'
                    )
                    lines.append(f'        _fig_parts.append({lvar})')
                    lbl_vars.append(lvar)
                anim_seq.append(f'FadeIn(VGroup({", ".join(lbl_vars)}))')
            else:
                lines.append(f'        # TODO: add vertex labels for "{role}"')

        # ── Special points (midpoints, etc.) ────────────────────────────
        elif "特殊点" in role or "中点" in role or "Dot" in shape:
            if points:
                for j, pt in enumerate(points):
                    pname = pt.get("label", pt.get("text", ""))
                    ppos  = pt.get("position", pt.get("pos", [0, 0, 0]))
                    dvar  = f"_gdot{i}_{j}"
                    tlvar = f"_gdtxt{i}_{j}"
                    lines.append(
                        f'        {dvar}  = Dot(np.array({list(ppos)}), radius=0.08, color=YELLOW)\n'
                        f'        {tlvar} = self._tx("{pname}", font_size=20, color=YELLOW)\n'
                        f'        {tlvar}.next_to({dvar}, UR, buff=0.1)\n'
                        f'        _fig_parts.extend([{dvar}, {tlvar}])'
                    )
                    anim_seq.append(f'FadeIn({dvar}, {tlvar})')
            else:
                lines.append(f'        # TODO: add special points for "{role}"')

        # ── Text annotations ─────────────────────────────────────────────
        elif text:
            pos    = el.get("position", el.get("pos", None))
            color  = _col(style, el, "#93c5fd")
            fs     = _fsize(style, el, 22)
            lines.append(f'        {var} = self._tx("{text}", font_size={fs}, color="{color}")')
            if pos and _is_coord_list([pos]):
                lines.append(f'        {var}.move_to(np.array({list(pos)}))')
            else:
                lines.append(f'        {var}.to_edge(DOWN, buff=0.6)')
            lines.append(f'        _fig_parts.append({var})')
            anim_seq.append(f'FadeIn({var})')

        else:
            lines.append(f'        # skipped element: "{role}" (shape={shape})')

    lines.append("        self._fig = VGroup(*_fig_parts)")

    if anim_seq:
        for a in anim_seq:
            lines.append(f'        self.play({a}, run_time=0.6)')
    else:
        lines.append("        self.play(FadeIn(self._fig), run_time=1.0)")

    lines.append("        self.wait(7)")
    lines.append("")
    return "\n".join(lines) + "\n"


def segment_highlight_geometry(seg: dict) -> str:
    """type: highlight_geometry — overlay highlights on self._fig, store in self._tris."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])

    lines    = ["        # ── HIGHLIGHT GEOMETRY ────────────────────────────────────",
                "        _tris_parts = []"]
    anim_seq = []
    caption_var = None

    for i, el in enumerate(elements):
        role     = el.get("role", "")
        style    = el.get("style", "")
        text     = el.get("text", "")
        vertices = el.get("vertices")
        labels   = el.get("labels", [])
        var      = f"_htri{i}"

        # ── Highlight polygon ─────────────────────────────────────────────
        if "关键图形" in role or "高亮" in role or "三角形" in role:
            if vertices and _is_coord_list(vertices):
                fill_c   = _col(style, el, "#f59e0b")
                fill_o   = _opac(style, el, 0.55)
                stroke_c = el.get("stroke", fill_c)
                verts_str = ", ".join(f"np.array({list(v)})" for v in vertices)
                lines.append(
                    f'        {var} = Polygon({verts_str},\n'
                    f'            fill_color="{fill_c}", fill_opacity={fill_o},\n'
                    f'            stroke_color="{stroke_c}", stroke_width=2)'
                )
                lines.append(f'        _tris_parts.append({var})')
                anim_seq.append(f'FadeIn({var})')
            else:
                lines.append(f'        # TODO: fill in vertices for highlight "{role}"')

        # ── Labels for highlight shapes ───────────────────────────────────
        elif ("标签" in role or "label" in role.lower()) and (labels or text):
            if labels:
                for j, lbl in enumerate(labels):
                    ltext = lbl.get("text", "")
                    lpos  = lbl.get("position", lbl.get("pos", [0, 0, 0]))
                    color = _col(style, el, "#fbbf24")
                    fs    = _fsize(style, el, 17)
                    lvar  = f"_hlbl{i}_{j}"
                    lines.append(
                        f'        {lvar} = self._tx("{ltext}", font_size={fs}, color="{color}")\n'
                        f'        {lvar}.move_to(np.array({list(lpos)}))\n'
                        f'        _tris_parts.append({lvar})'
                    )
                    anim_seq.append(f'FadeIn({lvar})')
            elif text:
                pos   = el.get("position", el.get("pos", None))
                fs    = _fsize(style, el, 17)
                color = _col(style, el, "#fbbf24")
                lines.append(f'        {var} = self._tx("{text}", font_size={fs}, color="{color}")')
                if pos and _is_coord_list([pos]):
                    lines.append(f'        {var}.move_to(np.array({list(pos)}))')
                lines.append(f'        _tris_parts.append({var})')
                anim_seq.append(f'FadeIn({var})')

        # ── Bottom caption ────────────────────────────────────────────────
        elif ("底部" in role or "说明" in role or "结论" in role) and text:
            lines.append(
                f'        {var} = self._tx("{text}", font_size=26, color="#fbbf24", weight=BOLD)\n'
                f'        {var}.to_edge(DOWN, buff=0.8)'
            )
            caption_var = var

        else:
            lines.append(f'        # skipped element: "{role}"')

    lines.append("        self._tris = VGroup(*_tris_parts)")

    if anim_seq:
        for a in anim_seq:
            lines.append(f'        self.play({a}, run_time=0.6)')
    else:
        lines.append("        self.play(FadeIn(self._tris), run_time=0.8)")

    lines.append("        self.play(Indicate(self._tris, scale_factor=1.1), run_time=0.6)")

    if caption_var:
        lines.append(f'        self.play(FadeIn({caption_var}), run_time=0.5)')
        lines.append("        self.wait(14)")
        lines.append(f'        self.play(FadeOut({caption_var}), run_time=0.4)')
    else:
        lines.append("        self.wait(15)")

    lines.append("")
    return "\n".join(lines) + "\n"


def segment_equation_steps(seg: dict) -> str:
    """type: equation_steps — right-panel calc steps, store in self._calc_grp."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])

    section_title = ""
    step_lines    = []
    result_text   = ""
    result_color  = "#c4b5fd"
    result_bg     = "#4c1d95"

    for el in elements:
        role  = el.get("role", "")
        text  = el.get("text", "")
        style = el.get("style", "")
        if "小节标题" in role or ("标题" in role and "副" not in role):
            if not section_title:
                section_title = text
        elif "推导步骤" in role or "步骤" in role or "eq" in role.lower():
            if text:
                step_lines.append(text)
            for ln in el.get("lines", []):
                step_lines.append(ln)
        elif "结果" in role or "高亮框" in role or "中间" in role:
            result_text  = text or result_text
            result_color = _col(style, el, "#c4b5fd")
            result_bg    = _col(style, el, "#4c1d95") if "fill" in style else "#4c1d95"

    lines = ["        # ── EQUATION STEPS ────────────────────────────────────────",
             "        _calc_parts = []"]

    # Section title
    if section_title:
        lines.append(
            f'        _calc_title = self._tx("{section_title}", font_size=22, color="#f59e0b", weight=BOLD)\n'
            f'        _calc_title.to_corner(UR, buff=0.6).shift(DOWN * 0.8)\n'
            f'        _calc_parts.append(_calc_title)'
        )

    # Step lines
    prev = "_calc_title" if section_title else None
    for j, ln in enumerate(step_lines):
        vname = f"_calc_eq{j}"
        lines.append(f'        {vname} = self._tx("{ln}", font_size=19, color="#e2e8f0")')
        if prev:
            lines.append(f'        {vname}.next_to({prev}, DOWN, aligned_edge=LEFT, buff=0.3)')
        else:
            lines.append(f'        {vname}.to_corner(UR, buff=0.6).shift(DOWN * 0.8)')
        lines.append(f'        _calc_parts.append({vname})')
        prev = vname

    # Result box
    if result_text:
        lines.append(
            f'        _calc_res_txt = self._tx("{result_text}", font_size=21,\n'
            f'            color="{result_color}", weight=BOLD)'
        )
        if prev:
            lines.append(f'        _calc_res_txt.next_to({prev}, DOWN, aligned_edge=LEFT, buff=0.4)')
        else:
            lines.append('        _calc_res_txt.to_corner(UR, buff=1.5)')
        lines.append(
            '        _calc_res_box = SurroundingRectangle(_calc_res_txt, corner_radius=0.12, buff=0.18,\n'
            f'            fill_color="{result_bg}", fill_opacity=0.4,\n'
            f'            stroke_color="{result_color}", stroke_width=2)\n'
            '        _calc_parts.extend([_calc_res_box, _calc_res_txt])'
        )

    lines.append("        self._calc_grp = VGroup(*_calc_parts)")

    # Animations
    if section_title:
        lines.append("        self.play(FadeIn(_calc_title), run_time=0.4)")
    for j in range(len(step_lines)):
        lines.append(f'        self.play(FadeIn(_calc_eq{j}, shift=RIGHT*0.1), run_time=0.4)')
    if result_text:
        lines.append(
            "        self.play(DrawBorderThenFill(_calc_res_box),\n"
            "                  FadeIn(_calc_res_txt), run_time=0.6)"
        )
    lines.append("        self.wait(10)")
    lines.append("")
    return "\n".join(lines) + "\n"


def segment_final_equation(seg: dict) -> str:
    """type: final_equation — fade calc, show assembly formula + answer."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])

    section_title = ""
    formula_lines = []
    answer_text   = ""
    answer_color  = "#34d399"

    for el in elements:
        role  = el.get("role", "")
        text  = el.get("text", "")
        style = el.get("style", "")
        if "小节标题" in role or ("标题" in role and "副" not in role):
            if not section_title:
                section_title = text
        elif "拼合公式" in role or "代入" in role or "公式" in role:
            if text:
                formula_lines.append(text)
            for ln in el.get("lines", []):
                formula_lines.append(ln)
        elif "最终答案" in role or ("答案" in role and "最终" in role):
            answer_text  = text or answer_text
            answer_color = _col(style, el, "#34d399")

    lines = [
        "        # ── FINAL EQUATION ────────────────────────────────────────",
        "        if self._calc_grp is not None:",
        "            self.play(FadeOut(self._calc_grp), run_time=0.4)",
        "        _asm_parts = []",
    ]

    if section_title:
        lines.append(
            f'        _asm_title = self._tx("{section_title}", font_size=22,\n'
            f'            color="#10b981", weight=BOLD)\n'
            f'        _asm_title.to_corner(UR, buff=0.6).shift(DOWN * 0.8)\n'
            f'        _asm_parts.append(_asm_title)'
        )

    prev = "_asm_title" if section_title else None
    for j, fl in enumerate(formula_lines):
        vname = f"_asm_eq{j}"
        lines.append(f'        {vname} = self._tx("{fl}", font_size=18, color="#e2e8f0")')
        if prev:
            lines.append(f'        {vname}.next_to({prev}, DOWN, aligned_edge=LEFT, buff=0.3)')
        else:
            lines.append(f'        {vname}.to_corner(UR, buff=0.6).shift(DOWN * 0.8)')
        lines.append(f'        _asm_parts.append({vname})')
        prev = vname

    if answer_text:
        lines.append(
            f'        _asm_ans_txt = self._tx("{answer_text}", font_size=30,\n'
            f'            color="{answer_color}", weight=BOLD)'
        )
        if prev:
            lines.append(f'        _asm_ans_txt.next_to({prev}, DOWN, aligned_edge=LEFT, buff=0.4)')
        else:
            lines.append('        _asm_ans_txt.to_corner(UR, buff=1.5)')
        lines.append(
            '        _asm_ans_box = SurroundingRectangle(_asm_ans_txt, corner_radius=0.15, buff=0.2,\n'
            f'            fill_color="#064e3b", fill_opacity=0.5,\n'
            f'            stroke_color="{answer_color}", stroke_width=2.5)\n'
            '        _asm_parts.extend([_asm_ans_box, _asm_ans_txt])'
        )

    lines.append("        self._asm_grp = VGroup(*_asm_parts)")

    # Animations
    if section_title:
        lines.append("        self.play(FadeIn(_asm_title), run_time=0.4)")
    for j in range(len(formula_lines)):
        lines.append(f'        self.play(FadeIn(_asm_eq{j}), run_time=0.4)')
    if answer_text:
        lines.append(
            "        self.play(DrawBorderThenFill(_asm_ans_box),\n"
            "                  FadeIn(_asm_ans_txt), run_time=0.6)"
        )
    lines.append("        self.wait(6)")

    # Fade out geometry + highlight + assembly
    lines += [
        "        _to_clear = [self._asm_grp]",
        "        if self._fig  is not None: _to_clear.append(self._fig)",
        "        if self._tris is not None: _to_clear.append(self._tris)",
        "        self.play(FadeOut(VGroup(*_to_clear)), run_time=0.6)",
        "        self._fig = self._tris = self._asm_grp = None",
    ]
    lines.append("")
    return "\n".join(lines) + "\n"


def segment_answer_reveal(seg: dict) -> str:
    """type: answer_reveal — full-screen large answer + key insight box."""
    visual   = seg.get("visual", {})
    elements = visual.get("elements", [])

    question_text = ""
    answer_text   = ""
    answer_color  = "#34d399"
    insight_text  = ""

    for el in elements:
        role  = el.get("role", "")
        text  = el.get("text", "")
        style = el.get("style", "")
        if "问题回顾" in role:
            question_text = text
        elif "大号" in role or ("答案" in role and "最终" in role):
            answer_text  = text or answer_text
            answer_color = _col(style, el, "#34d399")
        elif "提示" in role or "关键" in role or "💡" in text:
            insight_text = text.lstrip("💡 ").strip() if text else insight_text

    # Fallback to top-level fields
    if not answer_text:
        answer_text = seg.get("answer", "")
    if not insight_text:
        insight_text = seg.get("key_insight", "")

    lines = ["        # ── ANSWER REVEAL ──────────────────────────────────────────"]
    anim_parts = []

    if question_text:
        lines.append(
            f'        _ar_q = self._tx("{question_text}", font_size=34, color="#94a3b8")\n'
            f'        _ar_q.move_to(UP * 1.8)'
        )
        anim_parts.append('FadeIn(_ar_q, shift=UP*0.2)')

    if answer_text:
        lines.append(
            f'        _ar_ans = self._tx("{answer_text}", font_size=64,\n'
            f'            color="{answer_color}", weight=BOLD)\n'
            f'        _ar_ans.move_to(ORIGIN)'
        )
        lines.append(
            '        _ar_box = RoundedRectangle(corner_radius=0.3,\n'
            '            width=_ar_ans.width + 0.8, height=_ar_ans.height + 0.5,\n'
            f'            fill_color="#064e3b", fill_opacity=0.6,\n'
            f'            stroke_color="{answer_color}", stroke_width=3)\n'
            '        _ar_box.move_to(_ar_ans)'
        )
        anim_parts += ['DrawBorderThenFill(_ar_box)', 'FadeIn(_ar_ans)']

    if insight_text:
        lines.append(
            f'        _ar_ins = self._tx("💡  {insight_text}", font_size=22, color="#fbbf24")\n'
            '        _ar_ins_box = RoundedRectangle(corner_radius=0.15,\n'
            '            width=_ar_ins.width + 0.8, height=_ar_ins.height + 0.4,\n'
            '            fill_color="#451a03", fill_opacity=0.7,\n'
            '            stroke_color="#f59e0b", stroke_width=2)\n'
        )
        if answer_text:
            lines.append('        _ar_ins_box.next_to(_ar_box, DOWN, buff=0.6)')
        else:
            lines.append('        _ar_ins_box.to_edge(DOWN, buff=1.0)')
        lines.append('        _ar_ins.move_to(_ar_ins_box)')
        anim_parts += ['DrawBorderThenFill(_ar_ins_box)', 'FadeIn(_ar_ins)']

    for a in anim_parts:
        lines.append(f'        self.play({a}, run_time=0.5)')

    lines.append("        self.wait(10)")
    lines.append("")
    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════════════════════ #
#  Dispatch table
# ═══════════════════════════════════════════════════════════════════════════ #

DISPATCH = {
    # ── v1 (legacy) ──────────────────────────────────────────────────────────
    "title":             segment_intro,
    "problem_statement": segment_problem,
    "solution_step":     segment_solution_step,
    "summary":           segment_summary,
    # ── v2 (new SKILL.md storyboard format) ──────────────────────────────────
    "title_card":        segment_title_card,
    "text_card":         segment_text_card,
    "geometry_drawing":  segment_geometry_drawing,
    "highlight_geometry": segment_highlight_geometry,
    "equation_steps":    segment_equation_steps,
    "final_equation":    segment_final_equation,
    "answer_reveal":     segment_answer_reveal,
}


# ═══════════════════════════════════════════════════════════════════════════ #
#  Code generator
# ═══════════════════════════════════════════════════════════════════════════ #

def generate(storyboard: dict) -> str:
    output_name = "TutorScene.py"
    code = MANIM_HEADER.format(output_name=output_name)

    for seg in storyboard.get("segments", []):
        seg_type = seg.get("type", "")
        handler  = DISPATCH.get(seg_type)
        if handler:
            # Handlers already produce 8-space indented code for the method body.
            code += handler(seg) + "\n"
        else:
            code += f"        # Unknown segment type: {seg_type}\n"

    # Close the method
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
