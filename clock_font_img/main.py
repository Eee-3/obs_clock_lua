"""
生成时钟字体图片 - TUI版本
使用prompt_toolkit框架提供交互式界面，支持实时搜索字体
"""

import os
import platform
import sys
from pathlib import Path
from typing import Any

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box
from PIL import Image, ImageDraw, ImageFont


def get_system_fonts() -> list[tuple[str, str]]:
    """
    从系统获取字体列表
    Windows: 使用注册表（高效，不占用内存）
    macOS/Linux: 扫描字体目录（仅顶层）
    """
    fonts: list[tuple[str, str]] = []

    if platform.system() == "Windows":
        import winreg

        font_dirs = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\Fonts"),
        ]

        try:
            reg_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            ]

            for hkey, subkey in reg_keys:
                try:
                    key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            if isinstance(value, str):
                                for font_dir in font_dirs:
                                    font_path = os.path.join(font_dir, value)
                                    if os.path.isfile(font_path):
                                        display_name = name.split("(")[0].strip()
                                        fonts.append((font_path, display_name))
                                        break
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except OSError:
                    pass

        except Exception as e:
            print(f"读取注册表失败: {e}")

    else:
        if platform.system() == "Darwin":
            font_dirs = [
                "/System/Library/Fonts",
                "/Library/Fonts",
                os.path.expanduser("~/Library/Fonts"),
            ]
        else:
            font_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts"),
            ]

        valid_extensions = {".ttf", ".otf", ".ttc"}
        for font_dir in font_dirs:
            if not os.path.isdir(font_dir):
                continue
            try:
                for file in os.listdir(font_dir):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in valid_extensions:
                        font_path = os.path.join(font_dir, file)
                        font_name = os.path.splitext(file)[0]
                        fonts.append((font_path, font_name))
            except PermissionError:
                pass

    # 去重并排序
    seen = set()
    unique_fonts = []
    for path, name in fonts:
        if name not in seen:
            seen.add(name)
            unique_fonts.append((path, name))

    return sorted(unique_fonts, key=lambda x: x[1].lower())


def find_optimal_font_size(
    font_path: str, target_width: int, target_height: int, chars: str
) -> int | None:
    """查找最佳字体大小"""
    min_size = 1
    max_size = 200
    best_size = None

    while min_size <= max_size:
        mid_size = (min_size + max_size) // 2
        try:
            font = ImageFont.truetype(font_path, mid_size)
        except Exception:
            return None

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
) -> None:
    """生成字符图片"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    font_size = find_optimal_font_size(font_path, width, height, chars)
    if font_size is None:
        raise ValueError("无法找到合适的字体大小")

    print(f"使用字体大小: {font_size}")

    font = ImageFont.truetype(font_path, font_size)
    ascent, descent = font.getmetrics()
    total_height = ascent + descent

    for char in chars:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), char, font=font)
        char_width = bbox[2] - bbox[0]

        x = (width - char_width) // 2 - bbox[0]
        y = (height - total_height) // 2

        draw.text((x, y), char, font=font, fill=(255, 255, 255, 255))

        if char == ":":
            filename = "and.png"
        elif char == "/":
            filename = "slash.png"
        elif char == ".":
            filename = "dot.png"
        else:
            filename = f"{char}.png"

        filepath = os.path.join(output_dir, filename)
        img.save(filepath, "PNG")
        print(f"已生成: {filepath}")


class FontSelector:
    """字体选择器（支持实时搜索）"""

    def __init__(self, fonts: list[tuple[str, str]]):
        self.fonts = fonts
        self.filtered_fonts = fonts
        self.selected_index = 0
        self.search_text = ""
        self.result: tuple[str, str] | None = None

        # 创建搜索缓冲区
        self.search_buffer = Buffer()
        self.search_buffer.on_text_changed += self._on_search_changed

        # 创建键绑定
        self.kb = KeyBindings()

        @self.kb.add("up")
        def _up(event: Any) -> None:
            if self.selected_index > 0:
                self.selected_index -= 1

        @self.kb.add("down")
        def _down(event: Any) -> None:
            if self.selected_index < len(self.filtered_fonts) - 1:
                self.selected_index += 1

        @self.kb.add("enter")
        def _enter(event: Any) -> None:
            if self.filtered_fonts:
                self.result = self.filtered_fonts[self.selected_index]
                event.app.exit()

        @self.kb.add("escape")
        def _escape(event: Any) -> None:
            self.result = None
            event.app.exit()

        # 创建布局
        self.layout = self._create_layout()

        # 创建样式
        self.style = Style.from_dict({
            "search": "bg:#333333",
            "selected": "bg:#0066cc #ffffff",
            "normal": "",
            "title": "bold",
        })

    def _on_search_changed(self, buffer: Buffer) -> None:
        """搜索文本变化时过滤字体"""
        self.search_text = buffer.text.lower()
        if self.search_text:
            self.filtered_fonts = [
                (p, n) for p, n in self.fonts
                if self.search_text in n.lower()
            ]
        else:
            self.filtered_fonts = self.fonts
        self.selected_index = 0

    def _create_layout(self) -> Layout:
        """创建布局"""
        # 搜索框
        search_window = Window(
            height=1,
            content=BufferControl(
                buffer=self.search_buffer,
                focusable=True,
            ),
            style="class:search",
        )

        # 字体列表
        font_list = FormattedTextControl(
            text=self._get_font_list_text,
            focusable=False,
        )
        font_window = Window(content=font_list)

        # 帮助文本
        help_text = Window(
            height=1,
            content=FormattedTextControl(
                text=[("", "↑↓选择  Enter确认  ESC取消  输入搜索")],
            ),
        )

        # 标题
        title = Window(
            height=1,
            content=FormattedTextControl(
                text=[("class:title", "选择字体 (输入关键字搜索):")],
            ),
        )

        root = HSplit([
            title,
            search_window,
            Box(font_window, padding_top=1, padding_bottom=1),
            help_text,
        ])

        return Layout(root, focused_element=search_window)

    def _get_font_list_text(self) -> list[tuple[str, str]]:
        """获取字体列表显示文本"""
        result = []
        max_display = 20
        start = max(0, self.selected_index - max_display // 2)
        end = min(len(self.filtered_fonts), start + max_display)

        for i in range(start, end):
            _, name = self.filtered_fonts[i]
            if i == self.selected_index:
                result.append(("class:selected", f"  > {name}\n"))
            else:
                result.append(("class:normal", f"    {name}\n"))

        if not self.filtered_fonts:
            result.append(("", "  未找到匹配的字体"))

        return result

    def run(self) -> tuple[str, str] | None:
        """运行选择器"""
        app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            style=self.style,
            full_screen=False,
        )
        app.run()
        return self.result


def input_with_default(prompt: str, default: str) -> str | None:
    """带默认值的输入"""
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.validation import Validator

    class EmptyValidator(Validator):
        def validate(self, document: Any) -> None:
            pass

    try:
        result = pt_prompt(f"{prompt} [{default}]: ", validator=EmptyValidator())
        return result if result else default
    except KeyboardInterrupt:
        return None


def main():
    """主函数"""
    print("时钟字体图片生成器")
    print("=" * 40)

    print("正在获取系统字体列表...")
    fonts = get_system_fonts()
    print(f"找到 {len(fonts)} 个字体\n")

    if not fonts:
        print("未找到任何字体！")
        return

    # 选择字体
    selector = FontSelector(fonts)
    result = selector.run()

    if result is None:
        print("已取消")
        return

    font_path, font_name = result
    print(f"\n已选择字体: {font_name}")
    print(f"字体路径: {font_path}\n")

    # 获取其他设置
    output_dir = input_with_default("输出目录", "../obs_clock")
    if output_dir is None:
        print("已取消")
        return

    width_str = input_with_default("图片宽度 (像素)", "22")
    if width_str is None:
        print("已取消")
        return
    try:
        width = int(width_str)
    except ValueError:
        print("错误: 宽度必须是整数")
        return

    height_str = input_with_default("图片高度 (像素)", "30")
    if height_str is None:
        print("已取消")
        return
    try:
        height = int(height_str)
    except ValueError:
        print("错误: 高度必须是整数")
        return

    chars = input_with_default("要生成的字符", "0123456789:/.")
    if chars is None:
        print("已取消")
        return

    print(f"\n即将生成 {len(chars)} 个字符图片到 {output_dir}")
    confirm = input_with_default("确认? (y/n)", "y")
    if confirm is None or confirm.lower() != "y":
        print("已取消")
        return

    # 生成图片
    print("\n开始生成...")
    try:
        generate_char_images(font_path, output_dir, width, height, chars)
        print("\n生成完成！")
    except Exception as e:
        print(f"\n生成失败: {e}")


if __name__ == "__main__":
    main()
