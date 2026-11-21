"""分镜数据模型单元测试。"""

from __future__ import annotations

import unittest

from storyboard.model import (
    CONTENT_WIDTH_MM,
    MAX_FRAMES,
    PageLayout,
    StoryboardError,
    Frame,
    build_frames,
    fit_size,
    frame_label,
    frame_size,
    grid_shape,
    page_count,
    paginate,
    ratio_size,
    validate_frame_count,
    validate_per_page,
    validate_project,
    validate_ratio,
    validate_style,
    validate_title,
)


class FrameLabelTest(unittest.TestCase):
    def test_label_pads_single_digit(self) -> None:
        self.assertEqual(frame_label(1), "01")

    def test_label_keeps_two_digits(self) -> None:
        self.assertEqual(frame_label(10), "10")

    def test_label_last_frame(self) -> None:
        self.assertEqual(frame_label(MAX_FRAMES), "24")

    def test_label_rejects_zero(self) -> None:
        with self.assertRaises(StoryboardError):
            frame_label(0)

    def test_label_rejects_overflow(self) -> None:
        with self.assertRaises(StoryboardError):
            frame_label(MAX_FRAMES + 1)

    def test_label_rejects_bool(self) -> None:
        with self.assertRaises(StoryboardError):
            frame_label(True)

    def test_label_rejects_text(self) -> None:
        with self.assertRaises(StoryboardError):
            frame_label("1")  # type: ignore[arg-type]


class FrameTest(unittest.TestCase):
    def test_frame_label_property(self) -> None:
        self.assertEqual(Frame(3).label, "03")

    def test_frame_rejects_zero(self) -> None:
        with self.assertRaises(StoryboardError):
            Frame(0)

    def test_frame_rejects_overflow(self) -> None:
        with self.assertRaises(StoryboardError):
            Frame(MAX_FRAMES + 1)

    def test_frame_rejects_bool(self) -> None:
        with self.assertRaises(StoryboardError):
            Frame(True)


class BuildFramesTest(unittest.TestCase):
    def test_build_one_frame(self) -> None:
        frames = build_frames(1)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].label, "01")

    def test_build_continuous_numbers(self) -> None:
        frames = build_frames(12)
        self.assertEqual([frame.number for frame in frames], list(range(1, 13)))

    def test_build_max_frames(self) -> None:
        frames = build_frames(MAX_FRAMES)
        self.assertEqual(frames[0].label, "01")
        self.assertEqual(frames[-1].label, "24")

    def test_build_rejects_zero(self) -> None:
        with self.assertRaises(StoryboardError):
            build_frames(0)

    def test_build_rejects_overflow(self) -> None:
        with self.assertRaises(StoryboardError):
            build_frames(MAX_FRAMES + 1)

    def test_build_rejects_text(self) -> None:
        with self.assertRaises(StoryboardError):
            build_frames("6")  # type: ignore[arg-type]


class NumberValidationTest(unittest.TestCase):
    def test_frame_count_accepts_bounds(self) -> None:
        self.assertEqual(validate_frame_count(1), 1)
        self.assertEqual(validate_frame_count(24), 24)

    def test_frame_count_accepts_numeric_text(self) -> None:
        self.assertEqual(validate_frame_count(" 6 "), 6)

    def test_frame_count_rejects_zero(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_frame_count(0)

    def test_frame_count_rejects_overflow(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_frame_count(25)

    def test_frame_count_rejects_word(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "整数"):
            validate_frame_count("六")

    def test_frame_count_rejects_bool(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_frame_count(False)

    def test_per_page_accepts_bounds(self) -> None:
        self.assertEqual(validate_per_page(1), 1)
        self.assertEqual(validate_per_page(6), 6)

    def test_per_page_rejects_zero(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "1~6"):
            validate_per_page(0)

    def test_per_page_rejects_overflow(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_per_page(7)

    def test_per_page_rejects_empty(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_per_page("")


class TextValidationTest(unittest.TestCase):
    def test_project_trims_spaces(self) -> None:
        self.assertEqual(validate_project("  我的定格动画  "), "我的定格动画")

    def test_project_accepts_max_length(self) -> None:
        text = "项" * 30
        self.assertEqual(validate_project(text), text)

    def test_project_rejects_empty(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "不能为空"):
            validate_project("   ")

    def test_project_rejects_overflow(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "30"):
            validate_project("项" * 31)

    def test_project_rejects_non_text(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_project(123)  # type: ignore[arg-type]

    def test_title_accepts_max_length(self) -> None:
        text = "题" * 40
        self.assertEqual(validate_title(text), text)

    def test_title_rejects_empty(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_title("")

    def test_title_rejects_overflow(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "40"):
            validate_title("题" * 41)

    def test_title_rejects_non_text(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_title(None)  # type: ignore[arg-type]

    def test_style_accepts_grid_and_full(self) -> None:
        self.assertEqual(validate_style("grid"), "grid")
        self.assertEqual(validate_style(" FULL "), "full")

    def test_style_rejects_strip(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "grid 或 full"):
            validate_style("strip")

    def test_style_rejects_non_text(self) -> None:
        with self.assertRaises(StoryboardError):
            validate_style(2)  # type: ignore[arg-type]

    def test_ratio_accepts_supported(self) -> None:
        self.assertEqual(validate_ratio("4:3"), "4:3")
        self.assertEqual(validate_ratio("16:9"), "16:9")

    def test_ratio_rejects_other(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "4:3 或 16:9"):
            validate_ratio("1:1")


class PageCountTest(unittest.TestCase):
    def test_exact_division(self) -> None:
        self.assertEqual(page_count(6, 3), 2)

    def test_partial_last_page(self) -> None:
        self.assertEqual(page_count(7, 3), 3)

    def test_single_page(self) -> None:
        self.assertEqual(page_count(1, 6), 1)

    def test_empty_frames(self) -> None:
        self.assertEqual(page_count(0, 3), 0)

    def test_max_frames_per_page(self) -> None:
        self.assertEqual(page_count(24, 6), 4)

    def test_rejects_negative(self) -> None:
        with self.assertRaises(StoryboardError):
            page_count(-1, 3)

    def test_rejects_bad_per_page(self) -> None:
        with self.assertRaises(StoryboardError):
            page_count(6, 7)


class PaginateTest(unittest.TestCase):
    def test_even_pages(self) -> None:
        pages = paginate(build_frames(6), 3)
        self.assertEqual([len(page.frames) for page in pages], [3, 3])

    def test_last_page_remainder(self) -> None:
        pages = paginate(build_frames(7), 3)
        self.assertEqual([len(page.frames) for page in pages], [3, 3, 1])

    def test_one_page(self) -> None:
        pages = paginate(build_frames(2), 6)
        self.assertEqual(len(pages), 1)

    def test_empty_frames(self) -> None:
        self.assertEqual(paginate([], 3), ())

    def test_page_numbers_are_sequential(self) -> None:
        pages = paginate(build_frames(8), 3)
        self.assertEqual([page.number for page in pages], [1, 2, 3])

    def test_total_frames_on_every_page(self) -> None:
        pages = paginate(build_frames(7), 3)
        self.assertEqual([page.total_frames for page in pages], [7, 7, 7])

    def test_rejects_non_frame(self) -> None:
        with self.assertRaises(StoryboardError):
            paginate(["01"], 3)  # type: ignore[list-item]

    def test_rejects_text_container(self) -> None:
        with self.assertRaises(StoryboardError):
            paginate("abc", 3)  # type: ignore[arg-type]

    def test_rejects_bad_per_page(self) -> None:
        with self.assertRaises(StoryboardError):
            paginate(build_frames(3), 0)


class PageLayoutTest(unittest.TestCase):
    def test_accepts_valid_page(self) -> None:
        page = PageLayout(1, (Frame(1), Frame(2)), 6)
        self.assertEqual(len(page.frames), 2)

    def test_rejects_empty_page(self) -> None:
        with self.assertRaises(StoryboardError):
            PageLayout(1, (), 0)

    def test_rejects_zero_number(self) -> None:
        with self.assertRaises(StoryboardError):
            PageLayout(0, (Frame(1),), 1)

    def test_rejects_total_less_than_frames(self) -> None:
        with self.assertRaises(StoryboardError):
            PageLayout(1, (Frame(1), Frame(2)), 1)

    def test_rejects_non_frame_item(self) -> None:
        with self.assertRaises(StoryboardError):
            PageLayout(1, ("01",), 1)  # type: ignore[arg-type]


class SizeTest(unittest.TestCase):
    def test_ratio_4_3_height(self) -> None:
        width, height = ratio_size(80, "4:3")
        self.assertAlmostEqual(width, 80)
        self.assertAlmostEqual(height, 60)

    def test_ratio_16_9_height(self) -> None:
        width, height = ratio_size(80, "16:9")
        self.assertAlmostEqual(width, 80)
        self.assertAlmostEqual(height, 45)

    def test_ratio_rejects_zero_width(self) -> None:
        with self.assertRaises(StoryboardError):
            ratio_size(0, "4:3")

    def test_ratio_rejects_negative_width(self) -> None:
        with self.assertRaises(StoryboardError):
            ratio_size(-10, "4:3")

    def test_ratio_rejects_text_width(self) -> None:
        with self.assertRaises(StoryboardError):
            ratio_size("80", "4:3")  # type: ignore[arg-type]

    def test_ratio_rejects_unknown_ratio(self) -> None:
        with self.assertRaises(StoryboardError):
            ratio_size(80, "3:2")

    def test_fit_size_width_bound(self) -> None:
        width, height = fit_size(100, 100, "4:3")
        self.assertAlmostEqual(width, 100)
        self.assertAlmostEqual(height, 75)

    def test_fit_size_height_bound(self) -> None:
        width, height = fit_size(100, 50, "4:3")
        self.assertAlmostEqual(width, 50 * 4 / 3)
        self.assertAlmostEqual(height, 50)

    def test_fit_size_rejects_zero_height(self) -> None:
        with self.assertRaises(StoryboardError):
            fit_size(100, 0, "4:3")

    def test_grid_shape_two_columns(self) -> None:
        self.assertEqual(grid_shape(3, "grid"), (2, 2))
        self.assertEqual(grid_shape(6, "grid"), (3, 2))

    def test_full_shape_one_column(self) -> None:
        self.assertEqual(grid_shape(3, "full"), (3, 1))

    def test_grid_frame_ratio_4_3(self) -> None:
        width, height = frame_size(6, "grid", "4:3")
        self.assertAlmostEqual(height / width, 3 / 4, places=6)

    def test_grid_frame_ratio_16_9(self) -> None:
        width, height = frame_size(6, "grid", "16:9")
        self.assertAlmostEqual(height / width, 9 / 16, places=6)

    def test_frame_fits_usable_width(self) -> None:
        width, _ = frame_size(1, "grid", "4:3")
        self.assertLessEqual(width, CONTENT_WIDTH_MM)

    def test_full_layout_is_wider_than_grid(self) -> None:
        grid_width, _ = frame_size(1, "grid", "4:3")
        full_width, _ = frame_size(1, "full", "4:3")
        self.assertGreater(full_width, grid_width)

    def test_frame_size_accepts_text_per_page(self) -> None:
        width, height = frame_size("3", "grid", "4:3")  # type: ignore[arg-type]
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_frame_size_rejects_bad_per_page(self) -> None:
        with self.assertRaises(StoryboardError):
            frame_size(0, "grid", "4:3")

    def test_frame_size_rejects_bad_style(self) -> None:
        with self.assertRaises(StoryboardError):
            frame_size(3, "strip", "4:3")


if __name__ == "__main__":
    unittest.main()
