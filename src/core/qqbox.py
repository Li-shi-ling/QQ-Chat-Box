from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import requests
import math
import json
import os
import re

# 联和两张图
def resize_and_paste_avatar_advanced(avatar, background, target_size=None, position="center", margin=20, scale=None):
    """
    高级版本：支持绝对位置、相对位置，并新增 scale 比例缩放

    Args:
        avatar: 头像，可以是路径字符串或PIL Image对象
        background: 背景，可以是路径字符串或PIL Image对象
        target_size (tuple): (width, height)，最终固定尺寸
        position (str/tuple): 相对或绝对位置
        margin (int): 边距（相对位置用）
        scale (float): ⭐ 按比例缩放。例：0.5=缩小一半，2.0=放大两倍

    Returns:
        PIL Image对象 或 None（失败时）
    """
    try:
        # --- 1. 读取图片 ---
        if isinstance(avatar, (str, os.PathLike)):
            avatar = Image.open(avatar).convert("RGBA")
        elif not isinstance(avatar, Image.Image):
            raise ValueError("avatar必须是路径或PIL Image对象")

        if isinstance(background, (str, os.PathLike)):
            background = Image.open(background).convert("RGBA")
        elif not isinstance(background, Image.Image):
            raise ValueError("background必须是路径或PIL Image对象")

        # --- 2. 按比例缩放 scale ---
        if scale is not None:
            if not isinstance(scale, (int, float)) or scale <= 0:
                raise ValueError("scale 必须是正数")
            w, h = avatar.size
            new_w = int(w * scale)
            new_h = int(h * scale)
            avatar = avatar.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # --- 3. 如果指定了 target_size，再强制覆盖 ---
        if target_size:
            avatar = avatar.resize(target_size, Image.Resampling.LANCZOS)

        # --- 位置计算 ---
        bg_width, bg_height = background.size
        av_width, av_height = avatar.size

        if isinstance(position, str):
            if position == "center":
                x = (bg_width - av_width) // 2
                y = (bg_height - av_height) // 2
            elif position == "top-left":
                x = margin
                y = margin
            elif position == "top-right":
                x = bg_width - av_width - margin
                y = margin
            elif position == "bottom-left":
                x = margin
                y = bg_height - av_height - margin
            elif position == "bottom-right":
                x = bg_width - av_width - margin
                y = bg_height - av_height - margin
            else:
                x, y = 0, 0
        elif isinstance(position, (tuple, list)) and len(position) == 2:
            x, y = position
        else:
            x, y = 0, 0

        # --- 防止越界 ---
        x = max(0, min(x, bg_width - av_width))
        y = max(0, min(y, bg_height - av_height))

        # --- 5. 合成 ---
        result = background.copy()
        result.paste(avatar, (x, y), avatar)
        return result

    except Exception as e:
        print(f"处理失败: {e}")
        return None

def create_rectangle_background(size, color="#F0F0F2", save_path=None):
    """
    生成矩形背景图片

    Args:
        size (tuple): 图片尺寸 (width, height)
        color (str): 背景颜色，默认 #F0F0F2
        save_path (str): 保存路径，None则不保存

    Returns:
        PIL Image对象
    """
    # 将十六进制颜色转换为RGB
    if color.startswith('#'):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        rgb_color = (r, g, b)
    else:
        rgb_color = (240, 240, 242)  # 默认颜色 #F0F0F2

    # 创建图片
    image = Image.new('RGB', size, rgb_color)

    if save_path:
        image.save(save_path, "PNG")

    return image

def create_chat_bubble(text, max_width=480, font_path="./resources/fonts/SourceHanSansSC-Light.otf",
        font_size=36, font=None, padding=21, bg_color=(255, 255, 255, 220),
        text_color=(0, 0, 0, 255), corner_radius=27, save_path=None
    ):

    # ----- ① 加载字体 -----
    if font is None:
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()

    # 临时画布测量
    temp = Image.new("RGB", (1, 1))
    draw_tmp = ImageDraw.Draw(temp)

    # ----- ② 自动换行 -----
    lines = []
    current = ""

    for ch in text:
        # 如果遇到换行符，立即换行
        if ch == '\n':
            if current:  # 如果当前行有内容，先保存当前行
                lines.append(current)
            current = ""
            continue

        test = current + ch
        w = draw_tmp.textlength(test, font=font)
        if w <= max_width - padding * 2:
            current = test
        else:
            lines.append(current)
            current = ch

    # 处理最后一行
    if current:
        lines.append(current)

    # ----- ③ 计算文本尺寸 -----
    bbox = font.getbbox("字")
    line_height = int(bbox[3] - bbox[1] + 4)  # 增加一点行间距
    text_height = line_height * len(lines)
    text_width = max(draw_tmp.textlength(line, font=font) for line in lines)

    width = int(text_width + padding * 2)
    height = int(text_height + padding * (2 + len(lines)))

    # ----- ④ 创建图层 -----
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ----- ⑤ 绘制圆角气泡 -----
    draw.rounded_rectangle(
        (0, 0, width, height),
        radius=corner_radius,
        fill=bg_color,
        outline=(230, 230, 230, 255),
        width=2
    )

    # ----- ⑥ 绘制文本，垂直居中 -----
    y = padding
    for line in lines:
        draw.text((padding, y), line, fill=text_color, font=font)
        y += line_height + padding

    if save_path:
        img.save(save_path)

    return img

# 下载qq头像
def download_avatar(avatar_url, save_path="avatar.jpg"):
    """
    下载头像到本地

    Args:
        avatar_url (str): 头像的URL地址
        save_path (str): 本地保存路径，默认avatar.jpg
    """
    try:
        # 发送GET请求
        response = requests.get(avatar_url, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        # 获取文件扩展名
        content_type = response.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            extension = '.jpg'
        elif 'png' in content_type:
            extension = '.png'
        elif 'gif' in content_type:
            extension = '.gif'
        else:
            # 从URL中提取扩展名
            extension = '.' + avatar_url.split('.')[-1] if '.' in avatar_url else '.jpg'

        # 确保保存路径有正确的扩展名
        if not save_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            save_path = save_path.rsplit('.', 1)[0] + extension

        # 写入文件
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return save_path

    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        return None

def download_circular_avatar(avatar_url, save_path="avatar.png", crop_circle=True, circle_size=None):
    """
    下载头像到本地，可选圆形裁剪

    Args:
        avatar_url (str): 头像的URL地址
        save_path (str): 本地保存路径，默认avatar.png
        crop_circle (bool): 是否进行圆形裁剪，默认True
        circle_size (int): 圆形半径（中心到边界的距离），默认None（自动计算为图片最小边的一半）
    """
    try:
        # 发送GET请求
        response = requests.get(avatar_url)
        response.raise_for_status()  # 检查请求是否成功

        # 将图片内容读取为PIL Image对象
        image = Image.open(BytesIO(response.content)).convert("RGBA")

        if crop_circle:
            # 如果没有指定circle_size，自动计算为图片最小边的一半
            if circle_size is None:
                width, height = image.size
                circle_size = min(width, height) // 2

            # 进行圆形裁剪
            image = create_circular_avatar(image, circle_size)
            # 圆形图片强制保存为PNG格式以保持透明通道
            if not save_path.lower().endswith('.png'):
                save_path = save_path.rsplit('.', 1)[0] + '.png'

        # 获取文件扩展名（仅在非圆形裁剪时使用）
        if not crop_circle:
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                extension = '.jpg'
                format_type = 'JPEG'
            elif 'png' in content_type:
                extension = '.png'
                format_type = 'PNG'
            elif 'gif' in content_type:
                extension = '.gif'
                format_type = 'GIF'
            else:
                extension = '.' + avatar_url.split('.')[-1] if '.' in avatar_url else '.jpg'
                format_type = 'JPEG'

            # 确保保存路径有正确的扩展名
            if not save_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                save_path = save_path.rsplit('.', 1)[0] + extension
        else:
            # 圆形裁剪时强制使用PNG格式
            format_type = 'PNG'

        # 保存图片
        if format_type == 'JPEG' and image.mode == 'RGBA':
            # JPEG不支持透明通道，转换为RGB
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
            image = background

        image.save(save_path, format_type)
        return save_path

    except Exception as e:
        print(f"下载失败: {e}")
        return None

def create_circular_avatar(image, radius):
    """
    将图片裁剪为圆形

    Args:
        image: PIL Image对象
        radius: 圆形半径

    Returns:
        圆形头像的PIL Image对象
    """
    # 计算最终图片尺寸（直径）
    diameter = radius * 2

    # 调整图片大小为正方形，确保中心裁剪
    width, height = image.size

    # 计算裁剪区域（从中心裁剪）
    if width > height:
        # 宽图，从左右裁剪
        left = (width - height) // 2
        top = 0
        right = left + height
        bottom = height
    else:
        # 高图，从上下裁剪
        left = 0
        top = (height - width) // 2
        right = width
        bottom = top + width

    # 先进行中心正方形裁剪
    image = image.crop((left, top, right, bottom))

    # 调整到目标尺寸
    image = image.resize((diameter, diameter), Image.Resampling.LANCZOS)

    # 创建圆形蒙版
    mask = Image.new('L', (diameter, diameter), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, diameter, diameter), fill=255)

    # 创建带透明通道的结果图像
    result = Image.new('RGBA', (diameter, diameter), (0, 0, 0, 0))

    # 应用圆形蒙版
    result.putalpha(mask)

    # 将原图粘贴到结果图像上
    result.paste(image, (0, 0), mask)

    return result

def get_qq_info(qq):
    avatar_cache_location = os.environ.get('avatar_cache_location', '.')  # 默认当前目录
    if not os.path.exists(avatar_cache_location):
        os.makedirs(avatar_cache_location)

    # 检查缓存目录中是否存在对应qq的头像文件
    for filename in os.listdir(avatar_cache_location):
        if filename.startswith(f"{qq}-") and filename.lower().endswith('.png'):
            # 文件名格式: qq-昵称.png
            name = filename[len(f"{qq}-"):-4]  # 去掉 qq- 和 .png 获取昵称
            file_path = os.path.join(avatar_cache_location, filename)
            return {"qq": qq, "name": name, "avatar_path": file_path}

    # 如果缓存不存在，则访问API获取QQ信息
    response = requests.get(f"https://uapis.cn/api/v1/social/qq/userinfo?qq={qq}")
    if response.status_code != 200:
        return False  # 请求失败

    data = response.json()
    name = data.get("nickname", qq)
    avatar_url = data.get("avatar_url")
    if not avatar_url:
        return False  # 没有头像URL

    # 构建保存路径
    save_path = os.path.join(avatar_cache_location, f"{qq}-{name}.png")

    # 下载圆形头像
    downloaded_path = download_circular_avatar(avatar_url, save_path)
    if downloaded_path:
        return {"qq": qq, "name": name, "avatar_path": downloaded_path}
    else:
        return None

class ChatBubbleGenerator:
    def __init__(
        self,
        bubble_font_path="./resources/fonts/Microsoft-YaHei-Semilight.ttc", # "./resources/fonts/Microsoft-YaHei-Light.ttc", # "./resources/fonts/SourceHanSansSC-Light.otf",
        nickname_font_path="./resources/fonts/SourceHanSansSC-ExtraLight.otf",
        bubble_font_size=34,
        nickname_font_size=25,
        bubble_padding=20,
        bubble_bg_color=(255, 255, 255, 220),
        text_color=(0, 0, 0, 255),
        corner_radius=27,
        avatar_size=(89, 89),
        margin=20
    ):
        """
        初始化聊天气泡生成器，字体只加载一次
        """
        print(bubble_font_path)
        self.bubble_font = ImageFont.truetype(bubble_font_path, bubble_font_size) \
            if os.path.exists(bubble_font_path) else ImageFont.load_default()
        self.nickname_font = ImageFont.truetype(nickname_font_path, nickname_font_size) \
            if os.path.exists(nickname_font_path) else ImageFont.load_default()

        self.bubble_font_size = bubble_font_size
        self.nickname_font_size = nickname_font_size
        self.bubble_padding = bubble_padding
        self.bubble_bg_color = bubble_bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.avatar_size = avatar_size
        self.margin = margin

    def create_chat_message(
        self,
        qq,
        text,
        bubble_position=(126, 50),
        avatar_position=(23, 10),
        background_color="#F0F0F2"
    ):
        """
        生成聊天气泡 + 背景 + 头像 + 昵称
        背景大小自动适应气泡和头像
        """
        avatar_data = get_qq_info(qq)
        assert not avatar_data is None, f"没能成功获取{qq}的信息"
        nickname = avatar_data["name"]
        avatar_path = avatar_data["avatar_path"]
        bubble = create_chat_bubble(
            text=text,
            font=self.bubble_font,
            font_size=self.bubble_font_size,
            padding=self.bubble_padding,
            bg_color=self.bubble_bg_color,
            text_color=self.text_color,
            corner_radius=self.corner_radius
        )
        bubble_w, bubble_h = bubble.size
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        nickname_width = int(temp_draw.textlength(nickname, font=self.nickname_font)) + self.bubble_padding
        bg_w = max(
            bubble_position[0] + bubble_w + self.margin,
            avatar_position[0] + self.avatar_size[0] + self.margin,
            bubble_position[0] + nickname_width
        )
        bg_h = max(
            bubble_position[1] + bubble_h + self.margin,
            avatar_position[1] + self.avatar_size[1] + self.margin
        )
        background = create_rectangle_background((bg_w, bg_h), color=background_color)
        result = resize_and_paste_avatar_advanced(
            avatar=bubble,
            background=background,
            position=bubble_position
        )
        avatar_img = Image.open(avatar_path).convert("RGBA")
        avatar_img = avatar_img.resize(self.avatar_size, Image.Resampling.LANCZOS)
        result = resize_and_paste_avatar_advanced(
            avatar=avatar_img,
            background=result,
            position=avatar_position
        )
        draw = ImageDraw.Draw(result)
        draw.text(
            (bubble_position[0], avatar_position[1]),
            nickname,
            fill=self.text_color,
            font=self.nickname_font
        )
        return result

def resize_by_scale(image, scale_factor):
    """按比例缩小图像"""
    width, height = image.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)