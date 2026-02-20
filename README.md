# OBS 日期及毫秒级时钟源

一个用于 OBS Studio 的 Lua 脚本，以图片形式显示**日期**以及毫秒级精度的**时钟**。

## 功能特性

- **双行显示**
  - 第一行：日期（格式：`YYYY/MM/DD`）
  - 第二行：时间（格式：`HH:MM:SS.mmm`，精确到毫秒）
- **图片渲染**：使用图片数字显示，可自定义字体样式
- **居中对齐**：两行内容自动居中对齐
- **实时更新**：每帧刷新显示

## 效果预览

<img width="2530" height="843" alt="image" src="https://github.com/user-attachments/assets/54be9f83-6238-4d3b-9607-ef06e69cbd40" />


## 安装使用
### 1. 下载脚本及资源
1. 从Release下载最新脚本压缩包

### 2. 加载脚本

1. 打开 OBS Studio
2. 菜单栏选择 `工具` → `脚本`
 <img width="2560" height="484" alt="image" src="https://github.com/user-attachments/assets/7cb7c0c2-c50b-44ca-9db5-18dfdc823be9" />

3. 点击 `+` 按钮，选择 `obs_clock.lua` 文件
 <img width="1013" height="698" alt="image" src="https://github.com/user-attachments/assets/56a9acf1-575a-4d04-a0a6-72e5e35c6f48" />


### 3. 添加时钟源

1. 在场景中点击 `+` 添加新源
2. 选择 `日期与毫秒级时间`
3. 时钟将显示在画面中
<img width="556" height="778" alt="image" src="https://github.com/user-attachments/assets/b0c932b6-7f02-44ba-b704-3b528ab3658a" />


## 自定义字体
### 详见 [`clock_font_img/`](clock_font_img/) 目录

本项目包含 `clock_font_img` 目录，提供了生成自定义字体图片的工具：

- 使用 Python 编写
- 可生成自定义样式的数字图片

## 技术规格

| 属性 | 值 |
|------|-----|
| 源宽度 | 264 像素 |
| 源高度 | 60 像素 |
| 字符宽度 | 22 像素 |
| 行高 | 30 像素 |

## 文件结构

```
obs_clock_lua/
├── obs_clock.lua          # 主脚本文件
├── obs_clock/             # 图片资源目录
│   ├── 0.png - 9.png      # 数字图片
│   ├── and.png            # 冒号分隔符
│   ├── slash.png          # 斜杠分隔符
│   └── dot.png            # 小数点分隔符
└── clock_font_img/        # 字体图片生成工具
      ── main.py
    └── ...
```

## 来源声明

Lua 脚本基于 [imfuding/obs_ms_clock](https://github.com/imfuding/obs_ms_clock) 项目。

## 许可证

本项目采用 MIT LICENSE
除了:
- **obs_clock** 目录中图片的字体为[Inter 28pt SemiBold Italic](https://github.com/rsms/inter)遵循其原 [OFL-1.1](https://github.com/rsms/inter/blob/master/LICENSE.txt)协议
- **obs_clock.lua** 中来自[原项目](https://github.com/imfuding/obs_ms_clock)的部分 遵循其原有许可(未指定许可证)
