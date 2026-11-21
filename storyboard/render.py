"""把分镜数据渲染成 A4 纵向、可打印的自包含 HTML。"""

from __future__ import annotations

import html
from typing import List, Sequence, Tuple

from .model import (
    CARD_BORDER_MM,
    CARD_HEAD_MM,
    CARD_PADDING_MM,
    COLUMN_GAP_MM,
    FOOTER_MM,
    HEADER_MM,
    MARGIN_BOTTOM_MM,
    MARGIN_TOP_MM,
    MARGIN_X_MM,
    MAX_FRAMES,
    PAGE_WIDTH_MM,
    WRITE_LINES_MM,
    Frame,
    PageLayout,
    StoryboardError,
    frame_size,
    grid_shape,
    paginate,
    validate_frame_count,
    validate_per_page,
    validate_project,
    validate_ratio,
    validate_style,
    validate_title,
)

SHOT_HINTS: Tuple[str, ...] = ("远景", "中景", "近景", "特写")


def _num(value: float) -> str:
    """去掉浮点数末尾多余的 0。"""
    text = "%.3f" % value
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _cq(mm: float) -> str:
    """把毫米换算为容器宽度百分比单位 cqw（页面宽 210mm）。"""
    return "%scqw" % _num(mm / PAGE_WIDTH_MM * 100.0)


def _pt(pt: float) -> str:
    """把磅值换算为 cqw，使屏幕缩放与打印字号一致。"""
    return _cq(pt * 0.352778)


def _frame_markup(
    frame: Frame,
    size: Tuple[float, float],
    ratio: str,
    wide: bool = False,
) -> str:
    width_mm, height_mm = size
    shots = "".join(
        '<span class="shot">\u25a1 %s</span>' % html.escape(name)
        for name in SHOT_HINTS
    )
    canvas = (
        '<div class="canvas-wrap">'
        '<div class="canvas" data-ratio="%s" style="width:%s;height:%s"></div>'
        "</div>"
        % (html.escape(ratio), _cq(width_mm), _cq(height_mm))
    )
    class_name = "frame span-full" if wide else "frame"
    return (
        '<article class="%s">'
        '<div class="frame-head"><span class="no">%s</span>'
        '<span class="shots">%s</span></div>'
        "%s"
        '<div class="lines">'
        '<div class="line"><span class="line-label">画面说明</span>'
        '<span class="line-rule"></span></div>'
        '<div class="line"><span class="line-label">台词/音效</span>'
        '<span class="line-rule"></span></div>'
        '<div class="line"><span class="line-label">时长（秒）</span>'
        '<span class="line-rule"></span></div>'
        "</div>"
        "</article>"
        % (class_name, html.escape(frame.label), shots, canvas)
    )


def _page_markup(
    page: PageLayout,
    total_pages: int,
    project: str,
    title: str,
    style: str,
    ratio: str,
    size: Tuple[float, float],
    rows: int,
    columns: int,
) -> str:
    frames_list = page.frames
    wide_index = (
        len(frames_list) - 1
        if columns == 2 and len(frames_list) > 1 and len(frames_list) % 2 == 1
        else -1
    )
    frames = "".join(
        _frame_markup(frame, size, ratio, index == wide_index)
        for index, frame in enumerate(frames_list)
    )
    grid_style = (
        "grid-template-columns:repeat(%d,minmax(0,1fr));"
        "grid-template-rows:repeat(%d,minmax(0,1fr))" % (columns, rows)
    )
    return (
        '<div class="page">'
        '<section class="sheet">'
        '<header class="board-head">'
        '<div class="head-top"><span class="project">项目：%s</span>'
        '<span class="tag">A4 纵向 · %s · %d 列</span></div>'
        '<h1 class="board-title">%s</h1>'
        '<div class="meta">'
        '<span class="field">姓名：<i></i></span>'
        '<span class="field">小组：<i></i></span>'
        '<span class="field">日期：<i></i></span>'
        "</div></header>"
        '<main class="board-grid style-%s" style="%s">%s</main>'
        '<footer class="board-foot">'
        "<span>第 %d / %d 页</span><span>共 %d 格</span>"
        "</footer></section></div>"
        % (
            html.escape(project),
            html.escape(ratio),
            columns,
            html.escape(title),
            html.escape(style),
            grid_style,
            frames,
            page.number,
            total_pages,
            page.total_frames,
        )
    )


def render_html(
    frames: Sequence[Frame],
    per_page: int = 3,
    project: str = "我的定格动画",
    title: str = "分镜纸",
    style: str = "grid",
    ratio: str = "4:3",
) -> str:
    """生成完整 HTML 文档，包含全部页面与内联样式。"""
    if isinstance(frames, (str, bytes)):
        raise StoryboardError("帧列表必须是 Frame 序列")
    try:
        items = tuple(frames)
    except TypeError as exc:
        raise StoryboardError("帧列表必须是 Frame 序列") from exc
    for item in items:
        if not isinstance(item, Frame):
            raise StoryboardError("帧列表只能包含 Frame 对象")
    if len(items) > MAX_FRAMES:
        raise StoryboardError(
            "帧数必须在 1~%d 之间，当前是 %d" % (MAX_FRAMES, len(items))
        )
    validate_frame_count(len(items))
    size_per_page = validate_per_page(per_page)
    project_text = validate_project(project)
    title_text = validate_title(title)
    style_key = validate_style(style)
    ratio_key = validate_ratio(ratio)
    rows, columns = grid_shape(size_per_page, style_key)
    size = frame_size(size_per_page, style_key, ratio_key)
    pages = paginate(items, size_per_page)

    body: List[str] = []
    for page in pages:
        body.append(
            _page_markup(
                page,
                len(pages),
                project_text,
                title_text,
                style_key,
                ratio_key,
                size,
                rows,
                columns,
            )
        )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n"
        "</body>\n</html>\n"
        % (html.escape(title_text), _style(), "\n".join(body))
    )


def _style() -> str:
    template = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  html, body { margin: 0; }
  body {
    padding: 16px 0 28px;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC",
      "Source Han Sans SC", sans-serif;
    overflow-x: hidden;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .page {
    width: min(210mm, calc(100vw - 12px));
    margin: 0 auto 14px;
    container-type: inline-size;
  }
  .sheet {
    width: 100%;
    aspect-ratio: 210 / 297;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: __PAD_TOP__ __PAD_X__ __PAD_BOTTOM__;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.16);
    break-inside: avoid;
  }
  .board-head {
    flex: 0 0 __HEADER__;
    min-height: 0;
  }
  .head-top {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 2mm;
    font-size: __FONT_SMALL__;
    line-height: 1.2;
    color: #475569;
  }
  .project { letter-spacing: 0.5pt; white-space: nowrap; }
  .tag { font-size: __FONT_TINY__; color: #94a3b8; white-space: nowrap; }
  .board-title {
    margin: 0.8mm 0 1mm;
    text-align: center;
    font-size: __FONT_TITLE__;
    font-weight: 600;
    letter-spacing: 5pt;
    line-height: 1.15;
  }
  .meta {
    display: flex;
    gap: 6cqw;
    font-size: __FONT_META__;
    line-height: 1.2;
    color: #475569;
  }
  .field { display: inline-flex; align-items: flex-end; gap: 1mm; }
  .field i {
    display: inline-block;
    width: 8.095cqw;
    height: 1.1em;
    border-bottom: 0.2mm solid #94a3b8;
  }
  .board-grid {
    flex: 1 1 auto;
    min-height: 0;
    display: grid;
    gap: __GAP__;
  }
  .frame {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    padding: __CARD_PAD__;
    border: __CARD_BORDER__ solid #475569;
    border-radius: 0.8mm;
    background: #fff;
  }
  .frame-head {
    flex: 0 0 __CARD_HEAD__;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5mm;
    width: 100%;
    font-size: __FONT_SMALL__;
    line-height: 1;
    white-space: nowrap;
  }
  .no {
    font-size: __FONT_NO__;
    font-weight: 700;
    letter-spacing: 0.5pt;
  }
  .shots {
    display: flex;
    gap: 2mm;
    font-size: __FONT_TINY__;
    color: #64748b;
  }
  .canvas-wrap {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .canvas {
    flex: 0 0 auto;
    border: 0.35mm solid #0f172a;
    background: #fff;
  }
  .frame.span-full {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
    grid-template-rows: auto minmax(0, 1fr);
    column-gap: 4mm;
    align-items: stretch;
  }
  .frame.span-full .frame-head {
    grid-column: 1 / -1;
    align-self: start;
  }
  .frame.span-full .canvas-wrap {
    grid-column: 1;
    align-self: center;
  }
  .frame.span-full .lines {
    grid-column: 2;
    align-self: stretch;
  }
  .frame.span-full .canvas {
    width: 100% !important;
    height: auto !important;
  }
  .frame.span-full .canvas[data-ratio="4:3"] { aspect-ratio: 4 / 3; }
  .frame.span-full .canvas[data-ratio="16:9"] { aspect-ratio: 16 / 9; }
  .lines {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    width: 100%;
    min-height: __LINES__;
  }
  .line {
    flex: 1 1 0;
    display: flex;
    align-items: flex-end;
    gap: 1.5mm;
    min-height: 0;
    border-bottom: 0.2mm solid #cbd5e1;
  }
  .line:last-child { border-bottom-color: #94a3b8; }
  .line-label {
    flex: 0 0 7.2cqw;
    font-size: __FONT_TINY__;
    line-height: 1.1;
    color: #334155;
    white-space: nowrap;
  }
  .line-rule { flex: 1 1 auto; }
  .board-foot {
    flex: 0 0 __FOOTER__;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding-top: 0.6mm;
    border-top: 0.2mm solid #e2e8f0;
    font-size: __FONT_TINY__;
    color: #64748b;
  }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    html, body { padding: 0; background: #fff; }
    .page {
      width: 210mm;
      margin: 0;
      break-after: page;
      page-break-after: always;
    }
    .page:last-child {
      break-after: auto;
      page-break-after: auto;
    }
    .sheet {
      width: 210mm;
      height: 297mm;
      aspect-ratio: auto;
      box-shadow: none;
      border-radius: 0;
    }
  }
"""
    replacements = {
        "__PAD_TOP__": _cq(MARGIN_TOP_MM),
        "__PAD_X__": _cq(MARGIN_X_MM),
        "__PAD_BOTTOM__": _cq(MARGIN_BOTTOM_MM),
        "__HEADER__": _cq(HEADER_MM),
        "__FOOTER__": _cq(FOOTER_MM),
        "__GAP__": _cq(COLUMN_GAP_MM),
        "__CARD_PAD__": _cq(CARD_PADDING_MM),
        "__CARD_BORDER__": _cq(CARD_BORDER_MM),
        "__CARD_HEAD__": _cq(CARD_HEAD_MM),
        "__LINES__": _cq(WRITE_LINES_MM),
        "__FONT_TITLE__": _pt(16.0),
        "__FONT_SMALL__": _pt(8.5),
        "__FONT_META__": _pt(8.0),
        "__FONT_TINY__": _pt(7.0),
        "__FONT_NO__": _pt(9.0),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template
