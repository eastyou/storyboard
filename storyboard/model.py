"""分镜纸数据模型：镜号、分页、画面框尺寸计算与参数校验。"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from typing import Dict, Sequence, Tuple, Union

Number = Union[int, float]

MIN_FRAMES = 1
MAX_FRAMES = 24
MIN_PER_PAGE = 1
MAX_PER_PAGE = 6
MAX_PROJECT_CHARS = 30
MAX_TITLE_CHARS = 40

# A4 纵向版面毫米尺寸，render 中的 CSS 会按同一比例换算。
PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
MARGIN_X_MM = 12.0
MARGIN_TOP_MM = 11.0
MARGIN_BOTTOM_MM = 9.0
HEADER_MM = 24.0
FOOTER_MM = 7.0
COLUMN_GAP_MM = 4.0
CARD_PADDING_MM = 2.5
CARD_BORDER_MM = 0.3
CARD_HEAD_MM = 5.0
WRITE_LINES_MM = 18.0
FRAME_SAFETY_MM = 0.5

CONTENT_WIDTH_MM = PAGE_WIDTH_MM - MARGIN_X_MM * 2
MAIN_HEIGHT_MM = (
    PAGE_HEIGHT_MM
    - MARGIN_TOP_MM
    - MARGIN_BOTTOM_MM
    - HEADER_MM
    - FOOTER_MM
)

RATIOS: Dict[str, Tuple[int, int]] = {"4:3": (4, 3), "16:9": (16, 9)}
STYLES: Dict[str, int] = {"grid": 2, "full": 1}


class StoryboardError(ValueError):
    """分镜参数或数据不合法。"""


def _parse_int(value: object, label: str, minimum: int, maximum: int) -> int:
    """把整数或数字字符串转换为指定范围内的整数。"""
    if isinstance(value, bool):
        raise StoryboardError("%s必须是整数" % label)
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise StoryboardError("%s不能为空" % label)
        try:
            number = int(text, 10)
        except ValueError as exc:
            raise StoryboardError(
                "%s必须是整数，当前是「%s」" % (label, value)
            ) from exc
    else:
        raise StoryboardError("%s必须是整数" % label)
    if not minimum <= number <= maximum:
        raise StoryboardError(
            "%s必须在 %d~%d 之间，当前是 %d"
            % (label, minimum, maximum, number)
        )
    return number


def _measure(value: object, label: str) -> float:
    """把正数校验为有限浮点数（毫米）。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StoryboardError("%s必须是数字" % label)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise StoryboardError("%s必须是有效数字" % label) from exc
    if not isfinite(number) or number <= 0:
        raise StoryboardError("%s必须大于 0" % label)
    return number


def validate_frame_count(value: object) -> int:
    """校验画面格数：1~24。"""
    return _parse_int(value, "帧数", MIN_FRAMES, MAX_FRAMES)


def validate_per_page(value: object) -> int:
    """校验每页格数：1~6。"""
    return _parse_int(value, "每页格数", MIN_PER_PAGE, MAX_PER_PAGE)


def validate_project(value: object) -> str:
    """校验项目名：1~30 个字符，返回去除首尾空白后的文本。"""
    if not isinstance(value, str):
        raise StoryboardError("项目名必须是文本")
    text = value.strip()
    if not text:
        raise StoryboardError("项目名不能为空")
    if len(text) > MAX_PROJECT_CHARS:
        raise StoryboardError(
            "项目名最多 %d 个字符，当前是 %d 个"
            % (MAX_PROJECT_CHARS, len(text))
        )
    return text


def validate_title(value: object) -> str:
    """校验标题：1~40 个字符，返回去除首尾空白后的文本。"""
    if not isinstance(value, str):
        raise StoryboardError("标题必须是文本")
    text = value.strip()
    if not text:
        raise StoryboardError("标题不能为空")
    if len(text) > MAX_TITLE_CHARS:
        raise StoryboardError(
            "标题最多 %d 个字符，当前是 %d 个"
            % (MAX_TITLE_CHARS, len(text))
        )
    return text


def validate_ratio(value: object) -> str:
    """校验画面比例，仅支持 4:3 与 16:9。"""
    if not isinstance(value, str):
        raise StoryboardError("画面比例必须是文本")
    text = value.strip()
    if text not in RATIOS:
        raise StoryboardError(
            "画面比例必须是 4:3 或 16:9，当前是「%s」" % value
        )
    return text


def validate_style(value: object) -> str:
    """校验版式，仅支持 grid（2 列）与 full（1 列）。"""
    if not isinstance(value, str):
        raise StoryboardError("版式必须是文本")
    text = value.strip().lower()
    if text not in STYLES:
        raise StoryboardError(
            "版式必须是 grid 或 full，当前是「%s」" % value
        )
    return text


def frame_label(number: int) -> str:
    """把镜号补零为两位，如 1 -> 01、24 -> 24。"""
    if isinstance(number, bool) or not isinstance(number, int):
        raise StoryboardError("镜号必须是整数")
    if not MIN_FRAMES <= number <= MAX_FRAMES:
        raise StoryboardError(
            "镜号必须在 %d~%d 之间，当前是 %d"
            % (MIN_FRAMES, MAX_FRAMES, number)
        )
    return "%02d" % number


@dataclass(frozen=True)
class Frame:
    """一格分镜，number 从 1 开始连续编号。"""

    number: int

    def __post_init__(self) -> None:
        frame_label(self.number)

    @property
    def label(self) -> str:
        """两位镜号文本，例如 01。"""
        return frame_label(self.number)


@dataclass(frozen=True)
class PageLayout:
    """一页分镜：页码、该页的格与全篇总格数。"""

    number: int
    frames: Tuple[Frame, ...]
    total_frames: int

    def __post_init__(self) -> None:
        if isinstance(self.number, bool) or not isinstance(self.number, int):
            raise StoryboardError("页码必须是整数")
        if self.number < 1:
            raise StoryboardError("页码必须从 1 开始")
        if isinstance(self.total_frames, bool) or not isinstance(
            self.total_frames, int
        ):
            raise StoryboardError("总格数必须是整数")
        try:
            items = tuple(self.frames)
        except TypeError as exc:
            raise StoryboardError("每页的帧必须是 Frame 序列") from exc
        if not items:
            raise StoryboardError("每页至少需要 1 格")
        for item in items:
            if not isinstance(item, Frame):
                raise StoryboardError("每页只能包含 Frame 对象")
        if self.total_frames < len(items):
            raise StoryboardError(
                "总格数 %d 不能少于本页格数 %d"
                % (self.total_frames, len(items))
            )
        object.__setattr__(self, "frames", items)


def build_frames(count: int) -> Tuple[Frame, ...]:
    """按 1~count 连续生成帧。"""
    if isinstance(count, bool) or not isinstance(count, int):
        raise StoryboardError("帧数必须是整数")
    total = validate_frame_count(count)
    return tuple(Frame(number) for number in range(1, total + 1))


def page_count(frame_count: object, per_page: object) -> int:
    """计算总页数；0 格返回 0 页。"""
    total = _parse_int(frame_count, "帧数", 0, MAX_FRAMES)
    size = validate_per_page(per_page)
    if total == 0:
        return 0
    return (total + size - 1) // size


def paginate(frames: Sequence[Frame], per_page: int) -> Tuple[PageLayout, ...]:
    """按每页格数切分帧，返回不可变的页面列表。"""
    size = validate_per_page(per_page)
    if isinstance(frames, (str, bytes)):
        raise StoryboardError("帧列表必须是 Frame 序列")
    try:
        items = tuple(frames)
    except TypeError as exc:
        raise StoryboardError("帧列表必须是 Frame 序列") from exc
    for item in items:
        if not isinstance(item, Frame):
            raise StoryboardError("帧列表只能包含 Frame 对象")
    total = len(items)
    pages = []
    for start in range(0, total, size):
        chunk = items[start : start + size]
        pages.append(
            PageLayout(
                number=len(pages) + 1,
                frames=chunk,
                total_frames=total,
            )
        )
    return tuple(pages)


def grid_shape(per_page: int, style: str) -> Tuple[int, int]:
    """返回（行数，列数）：grid 为 2 列，full 为 1 列。"""
    size = validate_per_page(per_page)
    key = validate_style(style)
    columns = STYLES[key]
    rows = int(ceil(size / float(columns)))
    return rows, columns


def ratio_size(width_mm: Number, ratio: str) -> Tuple[float, float]:
    """按可用宽度与比例计算宽高，宽度即传入值。"""
    width = _measure(width_mm, "宽度")
    key = validate_ratio(ratio)
    ratio_width, ratio_height = RATIOS[key]
    return width, width * ratio_height / ratio_width


def fit_size(
    max_width_mm: Number, max_height_mm: Number, ratio: str
) -> Tuple[float, float]:
    """在宽高上限内取最大且保持比例的尺寸。"""
    max_width = _measure(max_width_mm, "最大宽度")
    max_height = _measure(max_height_mm, "最大高度")
    width, height = ratio_size(max_width, ratio)
    if height <= max_height:
        return width, height
    ratio_width, ratio_height = RATIOS[validate_ratio(ratio)]
    return max_height * ratio_width / ratio_height, max_height


def frame_size(per_page: int, style: str, ratio: str) -> Tuple[float, float]:
    """按每页格数与版式计算画面框宽度和高度（毫米）。"""
    rows, columns = grid_shape(per_page, style)
    key = validate_ratio(ratio)
    card_width = (
        CONTENT_WIDTH_MM - COLUMN_GAP_MM * (columns - 1)
    ) / columns
    card_height = (MAIN_HEIGHT_MM - COLUMN_GAP_MM * (rows - 1)) / rows
    max_width = (
        card_width
        - CARD_PADDING_MM * 2
        - CARD_BORDER_MM * 2
    )
    max_height = (
        card_height
        - CARD_HEAD_MM
        - WRITE_LINES_MM
        - CARD_PADDING_MM * 2
        - CARD_BORDER_MM * 2
        - FRAME_SAFETY_MM
    )
    if max_width <= 0 or max_height <= 0:
        raise StoryboardError("当前每页格数过多，页面内排不下画面框")
    return fit_size(max_width, max_height, key)
