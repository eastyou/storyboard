"""HTML 渲染单元测试。"""

from __future__ import annotations

import re
import unittest

from storyboard.model import MAX_FRAMES, StoryboardError, build_frames
from storyboard.render import SHOT_HINTS, render_html


class RenderBasicsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.page = render_html(
            build_frames(6),
            per_page=3,
            project="我的定格动画",
            title="分镜纸",
        )

    def test_has_doctype_and_charset(self) -> None:
        self.assertTrue(self.page.startswith("<!doctype html>"))
        self.assertIn('<meta charset="utf-8">', self.page)

    def test_language_is_chinese(self) -> None:
        self.assertIn('<html lang="zh-CN">', self.page)

    def test_title_and_project_visible(self) -> None:
        self.assertIn("<title>分镜纸</title>", self.page)
        self.assertIn("项目：我的定格动画", self.page)

    def test_two_pages_for_six_frames(self) -> None:
        self.assertEqual(self.page.count('<div class="page">'), 2)
        self.assertEqual(self.page.count('<section class="sheet">'), 2)

    def test_six_frame_cards(self) -> None:
        self.assertEqual(self.page.count('<article class="frame'), 6)

    def test_odd_last_frame_spans_full_width(self) -> None:
        self.assertEqual(self.page.count('<article class="frame span-full">'), 2)
        self.assertIn("grid-column: 1 / -1;", self.page)
        self.assertIn("grid-template-columns: minmax(0, 1.1fr)", self.page)
        self.assertIn('canvas[data-ratio="4:3"] { aspect-ratio: 4 / 3; }', self.page)

    def test_frame_numbers_are_padded(self) -> None:
        for number in range(1, 7):
            self.assertIn(">%02d<" % number, self.page)

    def test_page_footers(self) -> None:
        self.assertIn("第 1 / 2 页", self.page)
        self.assertIn("第 2 / 2 页", self.page)
        self.assertIn("共 6 格", self.page)

    def test_meta_fields(self) -> None:
        self.assertIn("姓名：", self.page)
        self.assertIn("小组：", self.page)
        self.assertIn("日期：", self.page)

    def test_three_writing_rows_per_frame(self) -> None:
        self.assertEqual(self.page.count("画面说明"), 6)
        self.assertEqual(self.page.count("台词/音效"), 6)
        self.assertEqual(self.page.count("时长（秒）"), 6)

    def test_shot_hints_are_blank_checkboxes(self) -> None:
        for hint in SHOT_HINTS:
            self.assertEqual(self.page.count(hint), 6)
        self.assertEqual(self.page.count("\u25a1"), 6 * len(SHOT_HINTS))

    def test_no_network_resources(self) -> None:
        self.assertNotIn("http://", self.page)
        self.assertNotIn("https://", self.page)
        self.assertNotIn("<link", self.page)
        self.assertNotIn("<script", self.page)
        self.assertNotIn("@import", self.page)
        self.assertNotIn("url(", self.page)

    def test_print_rules_present(self) -> None:
        self.assertIn("size: A4 portrait", self.page)
        self.assertIn("break-after: page", self.page)
        self.assertIn("break-inside: avoid", self.page)

    def test_grid_style_marker(self) -> None:
        self.assertIn("style-grid", self.page)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", self.page)


class RenderRatioTest(unittest.TestCase):
    def test_4_3_frame_size(self) -> None:
        page = render_html(build_frames(6), ratio="4:3")
        match = re.search(
            r'class="canvas" data-ratio="4:3" style="width:([0-9.]+)cqw;'
            r'height:([0-9.]+)cqw"',
            page,
        )
        self.assertIsNotNone(match)
        assert match is not None
        width = float(match.group(1))
        height = float(match.group(2))
        self.assertAlmostEqual(height / width, 0.75, places=4)

    def test_16_9_frame_size(self) -> None:
        page = render_html(build_frames(6), ratio="16:9")
        matches = re.findall(
            r'data-ratio="16:9" style="width:([0-9.]+)cqw;'
            r'height:([0-9.]+)cqw"',
            page,
        )
        self.assertEqual(len(matches), 6)
        for width, height in matches:
            self.assertAlmostEqual(
                float(height) / float(width), 9 / 16, places=4
            )

    def test_ratio_text_in_tag(self) -> None:
        page = render_html(build_frames(3), ratio="16:9")
        self.assertIn("A4 纵向 · 16:9", page)


class RenderLayoutTest(unittest.TestCase):
    def test_full_style_uses_one_column(self) -> None:
        page = render_html(build_frames(3), per_page=3, style="full")
        self.assertIn("style-full", page)
        self.assertIn("grid-template-columns:repeat(1,minmax(0,1fr))", page)
        self.assertIn("grid-template-rows:repeat(3,minmax(0,1fr))", page)

    def test_pages_for_twenty_four_frames(self) -> None:
        page = render_html(build_frames(MAX_FRAMES), per_page=6)
        self.assertEqual(page.count('<div class="page">'), 4)
        self.assertIn("第 4 / 4 页", page)
        self.assertIn("共 24 格", page)
        self.assertIn(">24<", page)

    def test_single_frame_single_page(self) -> None:
        page = render_html(build_frames(1), per_page=1)
        self.assertEqual(page.count('<div class="page">'), 1)
        self.assertIn("第 1 / 1 页", page)
        self.assertIn("共 1 格", page)

    def test_meta_rows_repeat_on_each_page(self) -> None:
        page = render_html(build_frames(6), per_page=3)
        self.assertEqual(page.count("姓名："), 2)
        self.assertEqual(page.count("小组："), 2)
        self.assertEqual(page.count("日期："), 2)


class RenderEscapeTest(unittest.TestCase):
    def test_project_is_escaped(self) -> None:
        page = render_html(
            build_frames(1), project='<b>&"动画"</b>', title="分镜纸"
        )
        self.assertIn("&lt;b&gt;&amp;&quot;动画&quot;&lt;/b&gt;", page)
        self.assertNotIn("<b>&", page)

    def test_title_is_escaped(self) -> None:
        page = render_html(build_frames(1), title="<em>标题</em>")
        self.assertIn("<title>&lt;em&gt;标题&lt;/em&gt;</title>", page)
        self.assertIn("&lt;em&gt;标题&lt;/em&gt;", page)

    def test_text_is_trimmed(self) -> None:
        page = render_html(
            build_frames(1), project="  我的项目  ", title="  我的标题  "
        )
        self.assertIn("项目：我的项目", page)
        self.assertNotIn("  我的项目  ", page)


class RenderValidationTest(unittest.TestCase):
    def test_rejects_empty_frames(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html([])

    def test_rejects_non_frame(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html(["01"])  # type: ignore[list-item]

    def test_rejects_text_frames(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html("abc")  # type: ignore[arg-type]

    def test_rejects_bad_per_page(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html(build_frames(3), per_page=7)

    def test_rejects_bad_style(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html(build_frames(3), style="strip")

    def test_rejects_bad_ratio(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html(build_frames(3), ratio="1:1")

    def test_rejects_empty_project(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html(build_frames(3), project="  ")

    def test_rejects_long_title(self) -> None:
        with self.assertRaises(StoryboardError):
            render_html(build_frames(3), title="长" * 41)

    def test_rejects_too_many_frames(self) -> None:
        frames = build_frames(MAX_FRAMES) + (build_frames(1)[0],)
        with self.assertRaises(StoryboardError):
            render_html(frames)


if __name__ == "__main__":
    unittest.main()
