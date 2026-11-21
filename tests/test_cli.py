"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from storyboard.cli import main
from storyboard.model import MAX_FRAMES


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = self.root / "分镜纸.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def run_exit(self, argv: List[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(argv)
        return int(ctx.exception.code)

    def test_default_generation(self) -> None:
        code, out, _ = self.run_cli(["-o", str(self.target)])
        self.assertEqual(code, 0)
        self.assertTrue(self.target.exists())
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count('<div class="page">'), 2)
        self.assertIn("共 6 格", page)
        self.assertIn("我的定格动画", page)
        self.assertIn("6 格，2 页", out)

    def test_custom_generation(self) -> None:
        code, out, _ = self.run_cli(
            [
                "--frames", "8",
                "--per-page", "2",
                "--style", "full",
                "--ratio", "16:9",
                "--project", "我的短片",
                "--title", "拍摄脚本",
                "-o", str(self.target),
            ]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count('<div class="page">'), 4)
        self.assertIn("共 8 格", page)
        self.assertIn("style-full", page)
        self.assertIn("16:9", page)
        self.assertIn("项目：我的短片", page)
        self.assertIn("<title>拍摄脚本</title>", page)
        self.assertIn("8 格，4 页", out)

    def test_single_frame(self) -> None:
        code, _, _ = self.run_cli(
            ["--frames", "1", "--per-page", "6", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("第 1 / 1 页", page)
        self.assertIn("共 1 格", page)

    def test_max_frames(self) -> None:
        code, _, _ = self.run_cli(
            ["--frames", "24", "--per-page", "6", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count('<div class="page">'), 4)
        self.assertIn("共 24 格", page)
        self.assertIn(">24<", page)

    def test_frames_zero_rejected(self) -> None:
        code, _, err = self.run_cli(
            ["--frames", "0", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误:", err)
        self.assertIn("帧数", err)
        self.assertFalse(self.target.exists())

    def test_frames_overflow_rejected(self) -> None:
        self.assertEqual(
            self.run_cli(
                ["--frames", str(MAX_FRAMES + 1), "-o", str(self.target)]
            )[0],
            2,
        )
        self.assertFalse(self.target.exists())

    def test_frames_text_rejected(self) -> None:
        code, _, err = self.run_cli(
            ["--frames", "六", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("整数", err)

    def test_per_page_zero_rejected(self) -> None:
        code, _, err = self.run_cli(
            ["--per-page", "0", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("每页格数", err)

    def test_per_page_overflow_rejected(self) -> None:
        self.assertEqual(
            self.run_cli(["--per-page", "7", "-o", str(self.target)])[0], 2
        )

    def test_invalid_style_rejected(self) -> None:
        code, _, err = self.run_cli(
            ["--style", "strip", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("grid 或 full", err)

    def test_invalid_ratio_rejected(self) -> None:
        code, _, err = self.run_cli(
            ["--ratio", "1:1", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("4:3 或 16:9", err)

    def test_empty_project_rejected(self) -> None:
        code, _, err = self.run_cli(
            ["--project", "   ", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("项目名", err)

    def test_long_project_rejected(self) -> None:
        code, _, _ = self.run_cli(
            ["--project", "项" * 31, "-o", str(self.target)]
        )
        self.assertEqual(code, 2)

    def test_empty_title_rejected(self) -> None:
        code, _, err = self.run_cli(["--title", "", "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("标题", err)

    def test_long_title_rejected(self) -> None:
        code, _, _ = self.run_cli(
            ["--title", "题" * 41, "-o", str(self.target)]
        )
        self.assertEqual(code, 2)

    def test_empty_output_rejected(self) -> None:
        code, _, err = self.run_cli(["-o", "  "])
        self.assertEqual(code, 2)
        self.assertIn("输出路径", err)

    def test_output_is_directory(self) -> None:
        code, _, err = self.run_cli(["-o", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_missing_parent_directory(self) -> None:
        code, _, err = self.run_cli(
            ["-o", str(self.root / "missing" / "分镜纸.html")]
        )
        self.assertEqual(code, 1)
        self.assertIn("错误:", err)

    def test_output_utf8(self) -> None:
        code, _, _ = self.run_cli(
            ["--project", "语文课短片", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        self.assertIn(
            "语文课短片", self.target.read_text(encoding="utf-8")
        )

    def test_arguments_are_trimmed(self) -> None:
        code, _, _ = self.run_cli(
            [
                "--project", "  三班项目  ",
                "--title", "  分镜练习  ",
                "-o", str(self.target),
            ]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("项目：三班项目", page)
        self.assertIn("<title>分镜练习</title>", page)

    def test_stdout_contains_next_step(self) -> None:
        code, out, _ = self.run_cli(["-o", str(self.target)])
        self.assertEqual(code, 0)
        self.assertIn("A4 纵向", out)
        self.assertIn(str(self.target), out)

    def test_help(self) -> None:
        self.assertEqual(self.run_exit(["--help"]), 0)

    def test_version(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("storyboard 0.1.0", out.getvalue())

    def test_unknown_argument(self) -> None:
        self.assertEqual(self.run_exit(["--unknown"]), 2)


if __name__ == "__main__":
    unittest.main()
