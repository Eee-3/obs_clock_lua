"""
生成时钟字体图片 - TUI版本
使用pick库提供交互式界面，支持实时搜索字体
"""

import os
import platform
import sys
from pathlib import Path

from pick import pick
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


def input_with_default(prompt: str, default: str) -> str:
    """带默认值的输入"""
    result = input(f"{prompt} [{default}]: ").strip()
    return result if result else default


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

    # 创建字体选择菜单（支持搜索）
    font_options = [(name, path) for path, name in fonts]
    
    selected, index = pick(
        [name for name, _ in font_options],
        "选择字体 (输入关键字搜索):",
    )
    
    font_path = font_options[index][1]
    font_name = selected
    print(f"\n已选择字体: {font_name}")
    print(f"字体路径: {font_path}\n")

    # 获取其他设置
    output_dir = input_with_default("输出目录", "../obs_clock")
    
    width_str = input_with_default("图片宽度 (像素)", "22")
    try:
        width = int(width_str)
    except ValueError:
        print("错误: 宽度必须是整数")
        return

    height_str = input_with_default("图片高度 (像素)", "30")
    try:
        height = int(height_str)
    except ValueError:
        print("错误: 高度必须是整数")
        return

    chars = input_with_default("要生成的字符", "0123456789:/.")

    print(f"\n即将生成 {len(chars)} 个字符图片到 {output_dir}")
    confirm = input_with_default("确认? (y/n)", "y")
    
    if confirm.lower() != "y":
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
