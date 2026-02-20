"""
生成时钟字体图片 - TUI版本
使用Textual框架提供交互式界面，支持字体搜索和自定义字符
"""

import os
from pathlib import Path
from typing import ClassVar

from fonttools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Static,
    ListView,
    ListItem,
    Log,
)


class FontItem(ListItem):
    """字体列表项"""

    def __init__(self, font_path: str, font_name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_path = font_path
        self.font_name = font_name

    def compose(self) -> ComposeResult:
        yield Label(self.font_name)


class FontGeneratorApp(App):
    """字体图片生成器TUI应用"""

    CSS: ClassVar[str] = """
    Screen {
        layout: vertical;
    }

    .main-container {
        layout: horizontal;
        height: 1fr;
    }

    .left-panel {
        width: 1fr;
        padding: 1;
        border-right: solid $primary;
    }

    .right-panel {
        width: 2fr;
        padding: 1;
    }

    .search-container {
        height: auto;
        margin-bottom: 1;
    }

    #search-input {
        width: 1fr;
    }

    #font-list {
        height: 1fr;
        border: solid $primary;
    }

    .settings-container {
        height: auto;
        margin-bottom: 1;
    }

    .setting-row {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

    .setting-label {
        width: 15;
        padding: 1;
    }

    .setting-input {
        width: 1fr;
    }

    .preview-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #preview-log {
        height: 1fr;
    }

    .button-row {
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    Button {
        margin-right: 1;
    }

    .status-bar {
        height: 1;
        background: $primary;
        color: $text-on-primary;
        padding: 0 1;
    }
    """

    TITLE: str = "时钟字体图片生成器"
    BINDINGS: ClassVar = [
        ("q", "quit", "退出"),
        ("g", "generate", "生成图片"),
        ("r", "refresh_fonts", "刷新字体列表"),
    ]

    # 系统字体目录
    FONT_DIRS: ClassVar[list[str]] = []

    def __init__(self) -> None:
        super().__init__()
        self.all_fonts: list[tuple[str, str]] = []  # (path, name)
        self.selected_font_path: str | None = None
        self._init_font_dirs()

    def _init_font_dirs(self) -> None:
        """初始化系统字体目录"""
        if os.name == "nt":  # Windows
            windir = os.environ.get("WINDIR", "C:\\Windows")
            self.FONT_DIRS = [
                os.path.join(windir, "Fonts"),
                os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\Fonts"),
            ]
        elif os.name == "posix":
            if os.uname().sysname == "Darwin":  # macOS
                self.FONT_DIRS = [
                    "/System/Library/Fonts",
                    "/Library/Fonts",
                    os.path.expanduser("~/Library/Fonts"),
                ]
            else:  # Linux
                self.FONT_DIRS = [
                    "/usr/share/fonts",
                    "/usr/local/share/fonts",
                    os.path.expanduser("~/.fonts"),
                    os.path.expanduser("~/.local/share/fonts"),
                ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="main-container"):
            with Container(classes="left-panel"):
                with Container(classes="search-container"):
                    yield Label("搜索字体:")
                    yield Input(
                        placeholder="输入字体名称搜索...",
                        id="search-input",
                    )
                yield Label("字体列表:")
                yield ListView(id="font-list")
            with Container(classes="right-panel"):
                with Container(classes="settings-container"):
                    yield Label("生成设置")
                    with Container(classes="setting-row"):
                        yield Label("输出目录:", classes="setting-label")
                        yield Input(
                            value="../obs_clock",
                            placeholder="输出目录路径",
                            id="output-dir",
                            classes="setting-input",
                        )
                    with Container(classes="setting-row"):
                        yield Label("图片宽度:", classes="setting-label")
                        yield Input(
                            value="22",
                            placeholder="图片宽度(像素)",
                            id="img-width",
                            classes="setting-input",
                        )
                    with Container(classes="setting-row"):
                        yield Label("图片高度:", classes="setting-label")
                        yield Input(
                            value="30",
                            placeholder="图片高度(像素)",
                            id="img-height",
                            classes="setting-input",
                        )
                    with Container(classes="setting-row"):
                        yield Label("生成字符:", classes="setting-label")
                        yield Input(
                            value="0123456789:/.",
                            placeholder="要生成的字符",
                            id="chars",
                            classes="setting-input",
                        )
                with Container(classes="preview-container"):
                    yield Label("预览/日志:")
                    yield Log(id="preview-log")
                with Container(classes="button-row"):
                    yield Button("生成图片", id="generate-btn", variant="primary")
                    yield Button("刷新字体", id="refresh-btn")
        yield Footer()

    def on_mount(self) -> None:
        """应用启动时加载字体"""
        self.call_later(self._load_fonts)

    async def _load_fonts(self) -> None:
        """加载系统字体"""
        log = self.query_one("#preview-log", Log)
        log.write_line("正在扫描系统字体...")

        self.all_fonts = []

        for font_dir in self.FONT_DIRS:
            if not os.path.exists(font_dir):
                continue

            for root, _, files in os.walk(font_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()

                    if ext in (".ttf", ".otf"):
                        try:
                            font = TTFont(file_path)
                            font_name = self._get_font_name(font)
                            if font_name:
                                self.all_fonts.append((file_path, font_name))
                            font.close()
                        except Exception:
                            pass
                    elif ext == ".ttc":
                        try:
                            ttc = TTCollection(file_path)
                            for i, font in enumerate(ttc.fonts):
                                font_name = self._get_font_name(font)
                                if font_name:
                                    self.all_fonts.append(
                                        (f"{file_path}:{i}", font_name)
                                    )
                        except Exception:
                            pass

        # 去重并排序
        seen = set()
        unique_fonts = []
        for path, name in self.all_fonts:
            if name not in seen:
                seen.add(name)
                unique_fonts.append((path, name))

        self.all_fonts = sorted(unique_fonts, key=lambda x: x[1].lower())

        log.write_line(f"找到 {len(self.all_fonts)} 个字体")
        self._update_font_list()

    def _get_font_name(self, font: TTFont) -> str | None:
        """从字体文件获取字体名称"""
        try:
            name_table = font["name"]
            # 优先获取英文名称
            for record in name_table.names:
                if record.nameID == 4:  # Full font name
                    try:
                        return record.toUnicode()
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    def _update_font_list(self, filter_text: str = "") -> None:
        """更新字体列表显示"""
        font_list = self.query_one("#font-list", ListView)
        font_list.clear()

        filter_lower = filter_text.lower()
        for path, name in self.all_fonts:
            if filter_lower and filter_lower not in name.lower():
                continue
            font_list.append(FontItem(path, name))

    def on_input_changed(self, event: Input.Changed) -> None:
        """处理输入变化"""
        if event.input.id == "search-input":
            self._update_font_list(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """处理字体选择"""
        if event.list_view.id == "font-list":
            item = event.item
            if isinstance(item, FontItem):
                self.selected_font_path = item.font_path
                log = self.query_one("#preview-log", Log)
                log.write_line(f"已选择字体: {item.font_name}")
                log.write_line(f"路径: {item.font_path}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "generate-btn":
            self.action_generate()
        elif event.button.id == "refresh-btn":
            self.action_refresh_fonts()

    def action_refresh_fonts(self) -> None:
        """刷新字体列表"""
        self._load_fonts()

    def action_generate(self) -> None:
        """生成图片"""
        log = self.query_one("#preview-log", Log)

        if not self.selected_font_path:
            log.write_line("[red]错误: 请先选择一个字体[/red]")
            return

        # 获取设置
        output_dir = self.query_one("#output-dir", Input).value
        width_str = self.query_one("#img-width", Input).value
        height_str = self.query_one("#img-height", Input).value
        chars = self.query_one("#chars", Input).value

        try:
            width = int(width_str)
            height = int(height_str)
        except ValueError:
            log.write_line("[red]错误: 宽度和高度必须是整数[/red]")
            return

        if not chars:
            log.write_line("[red]错误: 请输入要生成的字符[/red]")
            return

        # 处理TTC字体路径
        font_path = self.selected_font_path
        if ":" in font_path and font_path.endswith(tuple(f":{i}" for i in range(100))):
            path, index = font_path.rsplit(":", 1)
            font_path = path

        log.write_line(f"开始生成...")
        log.write_line(f"字体: {font_path}")
        log.write_line(f"输出目录: {output_dir}")
        log.write_line(f"尺寸: {width}x{height}")
        log.write_line(f"字符: {chars}")

        try:
            generate_char_images(font_path, output_dir, width, height, chars, log)
            log.write_line("[green]生成完成！[/green]")
        except Exception as e:
            log.write_line(f"[red]生成失败: {e}[/red]")


def find_optimal_font_size(
    font_path: str, target_width: int, target_height: int, chars: str
) -> int | None:
    """
    查找最佳字体大小，使字符正好撑满图像

    Args:
        font_path: 字体文件路径
        target_width: 目标宽度
        target_height: 目标高度
        chars: 要检查的字符列表

    Returns:
        最佳字体大小，如果找不到则返回None
    """
    min_size = 1
    max_size = 200
    best_size = None

    while min_size <= max_size:
        mid_size = (min_size + max_size) // 2
        font = ImageFont.truetype(font_path, mid_size)

        img = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        all_fit = True
        max_char_width = 0
        max_char_height = 0

        for char in chars:
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]
            max_char_width = max(max_char_width, char_width)
            max_char_height = max(max_char_height, char_height)

            if char_width > target_width or char_height > target_height:
                all_fit = False
                break

        if all_fit:
            if (
                max_char_width >= target_width - 2
                and max_char_height >= target_height - 2
            ):
                best_size = mid_size
                break
            elif (
                max_char_width < target_width - 2
                or max_char_height < target_height - 2
            ):
                best_size = mid_size
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1
        else:
            max_size = mid_size - 1

    if best_size is not None:
        for size in range(best_size, best_size + 10):
            try:
                font = ImageFont.truetype(font_path, size)
                img = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)

                all_fit = True
                for char in chars:
                    bbox = draw.textbbox((0, 0), char, font=font)
                    char_width = bbox[2] - bbox[0]
                    char_height = bbox[3] - bbox[1]
                    if char_width > target_width or char_height > target_height:
                        all_fit = False
                        break

                if all_fit:
                    best_size = size
                else:
                    break
            except Exception:
                break

    return best_size


def generate_char_images(
    font_path: str,
    output_dir: str,
    width: int,
    height: int,
    chars: str,
    log: Log | None = None,
) -> None:
    """
    生成字符图片

    Args:
        font_path: 字体文件路径
        output_dir: 输出目录
        width: 图片宽度
        height: 图片高度
        chars: 要生成的字符列表
        log: 日志输出控件
    """
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 查找最佳字体大小
    font_size = find_optimal_font_size(font_path, width, height, chars)

    if font_size is None:
        raise ValueError("无法找到合适的字体大小")

    if log:
        log.write_line(f"使用字体大小: {font_size}")

    # 加载字体
    font = ImageFont.truetype(font_path, font_size)

    # 获取字体的度量信息，用于确定基线位置
    ascent, descent = font.getmetrics()
    total_height = ascent + descent

    for char in chars:
        # 创建透明背景图片
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 获取字符的边界框
        bbox = draw.textbbox((0, 0), char, font=font)
        char_width = bbox[2] - bbox[0]

        # 计算水平居中位置
        x = (width - char_width) // 2 - bbox[0]

        # 计算垂直位置：使用基线对齐方式
        # 将字体总高度在图片中垂直居中，然后字符相对于基线定位
        y = (height - total_height) // 2

        # 绘制白色字符
        draw.text((x, y), char, font=font, fill=(255, 255, 255, 255))

        # 生成文件名
        if char == ":":
            filename = "and.png"
        elif char == "/":
            filename = "slash.png"
        elif char == ".":
            filename = "dot.png"
        else:
            filename = f"{char}.png"

        # 保存图片
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, "PNG")
        if log:
            log.write_line(f"已生成: {filepath}")


def main():
    """主函数"""
    app = FontGeneratorApp()
    app.run()


if __name__ == "__main__":
    main()
