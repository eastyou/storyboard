# storyboard

[![CI](https://github.com/eastyou/storyboard/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/storyboard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给课堂用的定格动画/短片分镜纸生成器：一条命令生成 A4 纵向、可直接打印的分镜表格。**零第三方依赖，不联网，打印即用。**

每一格都有 4:3 或 16:9 的空白画面框，框下是「画面说明」「台词/音效」「时长（秒）」三行填写区；镜号自动补零，远景/中景/近景/特写保留为空白勾选项，学生按需勾选，不预设任何内容。

## 特性

- **1~24 格**：`--frames` 指定格数，自动连续编号并补零（01、02…）
- **自动分页**：`--per-page 1~6`，每页按版式排满，页脚显示页码与「共 X 格」
- **两种版式**：`grid` 两列网格（默认）/ `full` 单列大图
- **两种画幅**：`--ratio 4:3`（默认）或 `16:9`，框高按可用宽度精确计算
- **三行填写区**：画面说明、台词/音效、时长（秒），每格独立
- **A4 纵向**：页眉含项目名、标题、姓名/小组/日期填写行
- **自包含 HTML**：CSS 全部内联，无网络资源，屏幕缩放不横向溢出
- **打印友好**：`@page A4 portrait`，格与页均不跨页，实线分隔
- **严格校验**：中文错误提示，参数错误退出码 2，写文件失败退出码 1
- **137 个单元测试**：覆盖边界、分页、比例、转义、CLI 退出码

## 安装

```bash
pip install storyboard
```

也可以直接使用源码，在项目目录中运行：

```bash
python -m storyboard --help
```

要求 Python 3.9+，仅使用标准库。

## 用法

```bash
python -m storyboard \
  --frames 6 \
  --per-page 3 \
  --style grid \
  --project 我的定格动画 \
  --title 分镜纸 \
  -o examples/分镜纸.html
```

生成结果见 [`examples/分镜纸.html`](examples/分镜纸.html)，用浏览器打开即可预览或打印。

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `--frames` | 画面格数，1~24 | `6` |
| `--per-page` | 每页格数，1~6 | `3` |
| `--style` | 版式：`grid`（2 列）或 `full`（1 列） | `grid` |
| `--ratio` | 画面框比例：`4:3` 或 `16:9` | `4:3` |
| `--project` | 项目名，1~30 个字符 | `我的定格动画` |
| `--title` | 标题，1~40 个字符 | `分镜纸` |
| `-o, --output` | 输出 HTML 路径 | `分镜纸.html` |
| `--version` | 显示版本 | — |

```bash
# 16:9 大画幅，一页两格，共 12 格
python -m storyboard --frames 12 --per-page 2 --ratio 16:9 --style full \
  --project 校园微电影 --title 拍摄分镜 -o 分镜纸.html
```

### 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 生成成功 |
| `1` | 写入文件失败（目录不存在、无权限、目标是目录等） |
| `2` | 参数不合法（格数、页数、版式、比例、项目名、标题、输出路径） |

参数错误统一输出中文提示到标准错误，例如：

```text
错误: 帧数必须在 1~24 之间，当前是 0
```

## 页面结构

每页 A4 纵向（210mm × 297mm）：

1. 页眉：项目名、标题、姓名 / 小组 / 日期填写行
2. 主体：每页 `--per-page` 格，`grid` 两列自动换行，`full` 单列排列
3. 每格：左上角两位镜号 + 四个空白景别勾选项 + 画面框 + 三行填写区
4. 页脚：`第 X / Y 页` 与 `共 X 格`

画面框高度由可用宽度与 `--ratio` 计算，宽高严格保持 4:3 或 16:9；每页格数较多时会自动缩小画面框，保证整格不跨页。

## 打印

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P`：

- 纸张：**A4**
- 方向：**纵向**
- 边距：**无 / 默认**
- 缩放：**100%**（或「默认」）
- 如需打印浅色线条，勾选「背景图形」

生成的页面已使用 `@page { size: A4 portrait; margin: 0 }`，每张分镜纸对应一个打印页，格子不会被拆到两页。

## 课堂用法

- **语文写作**：用 6 格梳理记叙文的起因、经过、高潮、结局；「台词/音效」行练习人物对话与场景声音，先分镜再成文。
- **信息科技**：把定格动画拍摄拆成镜头序列，标注每格时长，理解帧、镜头与剪辑顺序；也可用于算法步骤或事件流程的可视化。
- **美术**：勾选远景/中景/近景/特写，练习景别与构图；在画面框中画草图，比较镜头节奏与画面重点。
- **小组协作**：姓名 / 小组 / 日期栏便于分工回收，页脚页码方便按顺序装订。

## 项目结构

```text
storyboard/
├── storyboard/
│   ├── __init__.py   # 对外导出
│   ├── __main__.py   # python -m storyboard
│   ├── cli.py        # 参数解析、退出码与文件写入
│   ├── model.py      # Frame、PageLayout、分页与尺寸计算
│   └── render.py     # A4 纵向 HTML/CSS 渲染
├── tests/            # 137 个 unittest 测试
├── examples/         # 示例分镜纸
├── pyproject.toml
└── .github/workflows/ci.yml
```

## 开发

```bash
# 运行全部单元测试
python -m unittest discover -s tests

# 生成示例
python -m storyboard --frames 6 --per-page 3 --style grid \
  --project 我的定格动画 --title 分镜纸 -o examples/分镜纸.html
```

CI 在 Ubuntu / macOS / Windows 上测试 Python 3.10 与 3.13，并在 Ubuntu 22.04 上额外测试 Python 3.9。

## 许可证

[MIT](LICENSE) © 2026 eastyou
