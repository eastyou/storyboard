"""命令行入口：生成 A4 可打印分镜纸。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import (
    MAX_FRAMES,
    MAX_PER_PAGE,
    MAX_PROJECT_CHARS,
    MAX_TITLE_CHARS,
    MIN_FRAMES,
    MIN_PER_PAGE,
    StoryboardError,
    build_frames,
    page_count,
    validate_frame_count,
    validate_per_page,
    validate_project,
    validate_ratio,
    validate_style,
    validate_title,
)
from .render import render_html


class _Parser(argparse.ArgumentParser):
    """把 argparse 的参数错误统一为中文并返回退出码 2。"""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, "错误: %s\n" % message)


def _validate_output(value: object) -> str:
    if not isinstance(value, str):
        raise StoryboardError("输出路径必须是文本")
    text = value.strip()
    if not text:
        raise StoryboardError("输出路径不能为空")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="storyboard",
        description="分镜纸：生成 A4 可打印的定格动画/短片分镜纸",
    )
    parser.add_argument(
        "--version", action="version", version="storyboard 0.1.0"
    )
    parser.add_argument(
        "--frames",
        default=str(MIN_FRAMES + 5),
        metavar="1~%d" % MAX_FRAMES,
        help="画面格数，默认 6",
    )
    parser.add_argument(
        "--per-page",
        default="3",
        metavar="1~%d" % MAX_PER_PAGE,
        help="每页格数，默认 3",
    )
    parser.add_argument(
        "--style",
        default="grid",
        help="版式：grid（2 列网格）或 full（1 列），默认 grid",
    )
    parser.add_argument(
        "--ratio",
        default="4:3",
        help="画面框比例：4:3 或 16:9，默认 4:3",
    )
    parser.add_argument(
        "--project",
        default="我的定格动画",
        help="项目名，1~%d 个字符，默认「我的定格动画」" % MAX_PROJECT_CHARS,
    )
    parser.add_argument(
        "--title",
        default="分镜纸",
        help="标题，1~%d 个字符，默认「分镜纸」" % MAX_TITLE_CHARS,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="分镜纸.html",
        help="输出 HTML 路径，默认 分镜纸.html",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        frame_count = validate_frame_count(args.frames)
        per_page = validate_per_page(args.per_page)
        style = validate_style(args.style)
        ratio = validate_ratio(args.ratio)
        project = validate_project(args.project)
        title = validate_title(args.title)
        output = _validate_output(args.output)
        frames = build_frames(frame_count)
        document = render_html(
            frames,
            per_page=per_page,
            project=project,
            title=title,
            style=style,
            ratio=ratio,
        )
    except StoryboardError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2

    target = Path(output)
    try:
        target.write_text(document, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print(
        "已生成 %s：%d 格，%d 页，%s 版式，%s 比例"
        % (
            output,
            frame_count,
            page_count(frame_count, per_page),
            style,
            ratio,
        )
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
