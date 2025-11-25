from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import os
import re

# -------------------- 基础工具函数 --------------------
def resize_and_paste_avatar_advanced(avatar, background, target_size=None, position="center", margin=20, scale=None):
    """ 高级版本：支持绝对/相对位置，支持 scale 缩放 """
    try:
        if isinstance(avatar, (str, os.PathLike)):
            avatar = Image.open(avatar).convert("RGBA")
        elif not isinstance(avatar, Image.Image):
            raise ValueError("avatar必须是路径或PIL Image对象")
        if isinstance(background, (str, os.PathLike)):
            background = Image.open(background).convert("RGBA")
        elif not isinstance(background, Image.Image):
            raise ValueError("background必须是路径或PIL Image对象")
        if scale:
            w, h = avatar.size
            avatar = avatar.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
        if target_size:
            avatar = avatar.resize(target_size, Image.Resampling.LANCZOS)
        bg_w, bg_h = background.size
        av_w, av_h = avatar.size
        if isinstance(position, str):
            if position == "center":
                x, y = (bg_w - av_w)//2, (bg_h - av_h)//2
            elif position == "top-left":
                x, y = margin, margin
            elif position == "top-right":
                x, y = bg_w - av_w - margin, margin
            elif position == "bottom-left":
                x, y = margin, bg_h - av_h - margin
            elif position == "bottom-right":
                x, y = bg_w - av_w - margin, bg_h - av_h - margin
            else:
                x, y = 0, 0
        elif isinstance(position, (tuple, list)) and len(position) == 2:
            x, y = position
        else:
            x, y = 0, 0

        x = max(0, min(x, bg_w - av_w))
        y = max(0, min(y, bg_h - av_h))
        result = background.copy()
        result.paste(avatar, (x, y), avatar)
        return result
    except Exception as e:
        print(f"处理失败: {e}")
        return None

def create_rectangle_background(size, color="#F0F0F2", save_path=None):
    """ 生成矩形背景图片 """
    if color.startswith('#'):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        rgb_color = (r, g, b)
    else:
        rgb_color = (240, 240, 242)
    image = Image.new('RGBA', size, rgb_color + (255,))
    if save_path:
        image.save(save_path, "PNG")
    return image

def create_circular_avatar(image, radius):
    """ 将图片裁剪为圆形 """
    diameter = radius * 2
    w, h = image.size
    if w > h:
        left, top, right, bottom = (w-h)//2, 0, (w+h)//2, h
    else:
        left, top, right, bottom = 0, (h-w)//2, w, (h+w)//2
    image = image.crop((left, top, right, bottom))
    image = image.resize((diameter, diameter), Image.Resampling.LANCZOS)
    mask = Image.new('L', (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter, diameter), fill=255)
    result = Image.new('RGBA', (diameter, diameter), (0, 0, 0, 0))
    result.putalpha(mask)
    result.paste(image, (0, 0), mask)
    return result

def download_circular_avatar(avatar_url, save_path="avatar.png", crop_circle=True, circle_size=None):
    """ 下载头像，可选圆形裁剪 """
    try:
        response = requests.get(avatar_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGBA")
        if crop_circle:
            if circle_size is None:
                circle_size = min(image.size)//2
            image = create_circular_avatar(image, circle_size)
            if not save_path.lower().endswith('.png'):
                save_path = save_path.rsplit('.', 1)[0] + '.png'
        image.save(save_path, "PNG")
        return save_path
    except Exception as e:
        print(f"下载失败: {e}")
        return None

def get_qq_info(qq):
    """ 获取QQ信息，返回昵称和头像路径 """
    avatar_cache_location = os.environ.get('avatar_cache_location', '.')
    if not os.path.exists(avatar_cache_location):
        os.makedirs(avatar_cache_location)
    for filename in os.listdir(avatar_cache_location):
        if filename.startswith(f"{qq}-") and filename.lower().endswith('.png'):
            name = filename[len(f"{qq}-"):-4]
            return {"qq": qq, "name": name, "avatar_path": os.path.join(avatar_cache_location, filename)}
    response = requests.get(f"https://uapis.cn/api/v1/social/qq/userinfo?qq={qq}")
    if response.status_code != 200:
        return False
    data = response.json()
    name = data.get("nickname", qq)
    avatar_url = data.get("avatar_url")
    if not avatar_url:
        return False
    save_path = os.path.join(avatar_cache_location, f"{qq}-{name}.png")
    downloaded_path = download_circular_avatar(avatar_url, save_path)
    if downloaded_path:
        return {"qq": qq, "name": name, "avatar_path": downloaded_path}
    return None

# -------------------- 超采样气泡生成 --------------------
def create_chat_bubble(text, max_width=480,
                       font_path="./resources/fonts/SourceHanSansSC-Light.otf",
                       font_size=20, font=None, padding=21,
                       bg_color=(255, 255, 255, 220),
                       text_color=(0, 0, 0, 255),
                       corner_radius=27):

    scale_factor = 2  # 超采样倍数
    if font is None:
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size*scale_factor)
        else:
            font = ImageFont.load_default()
    temp_img = Image.new("RGBA", (max_width*scale_factor*2, 1), (0,0,0,0))
    draw_tmp = ImageDraw.Draw(temp_img)
    lines, current = [], ""
    for ch in text:
        test = current + ch
        w = draw_tmp.textlength(test, font=font)
        if w <= (max_width - padding*2)*scale_factor:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    bbox = font.getbbox("字")
    line_height = bbox[3] - bbox[1] + 4
    text_height = line_height * len(lines)
    text_width = max(draw_tmp.textlength(line, font=font) for line in lines)
    width = int(text_width + padding*4)
    height = int(text_height + padding*6)
    img = Image.new("RGBA", (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (0,0,width,height),
        radius=corner_radius*scale_factor,
        fill=bg_color,
        outline=(230,230,230,255),
        width=2*scale_factor
    )
    y = padding*2
    for line in lines:
        draw.text((padding*2, y), line, fill=text_color, font=font)
        y += line_height
    img = img.resize((width//scale_factor, height//scale_factor), Image.Resampling.LANCZOS)
    return img

class ChatBubbleGenerator:
    def __init__(
        self,
        bubble_font_path="./resources/fonts/SourceHanSansSC-Light.otf",#"./resources/fonts/msyh.ttc",#
        nickname_font_path="./resources/fonts/SourceHanSansSC-ExtraLight.otf",
        bubble_font_size=40,
        nickname_font_size=15,
        bubble_padding=17,
        bubble_bg_color=(255, 255, 255, 220),
        text_color=(0, 0, 0, 255),
        corner_radius=27,
        avatar_size=(89, 89),
        margin=20
    ):
        self.bubble_font_path = bubble_font_path
        self.nickname_font_path = nickname_font_path
        self.bubble_font_size = bubble_font_size
        self.nickname_font_size = nickname_font_size
        self.bubble_padding = bubble_padding
        self.bubble_bg_color = bubble_bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.avatar_size = avatar_size
        self.margin = margin
        # 超采样字体
        scale_factor = 2
        self.bubble_font = ImageFont.truetype(bubble_font_path, bubble_font_size*scale_factor) \
            if os.path.exists(bubble_font_path) else ImageFont.load_default()
        self.nickname_font = ImageFont.truetype(nickname_font_path, nickname_font_size*scale_factor) \
            if os.path.exists(nickname_font_path) else ImageFont.load_default()

    def create_chat_message(
        self,
        qq,
        text,
        bubble_position=(126, 50),
        avatar_position=(23, 10),
        background_color="#F0F0F2"
    ):
        avatar_data = get_qq_info(qq)
        if avatar_data is None:
            raise ValueError(f"未能获取{qq}信息")
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
        bg_w = int(max(bubble_position[0] + bubble_w + self.margin,
                   avatar_position[0] + self.avatar_size[0] + self.margin,self.calculate_name_bar(nickname)))


        bg_h = max(bubble_position[1] + bubble_h + self.margin,
                   avatar_position[1] + self.avatar_size[1] + self.margin)


        background = create_rectangle_background((bg_w, bg_h), color=background_color)
        result     = resize_and_paste_avatar_advanced(bubble, background, position=bubble_position)
        avatar_img = Image.open(avatar_path).convert("RGBA")
        avatar_img = avatar_img.resize(self.avatar_size, Image.Resampling.LANCZOS)
        result = resize_and_paste_avatar_advanced(avatar_img, result, position=avatar_position)
        draw = ImageDraw.Draw(result)
        draw.text((bubble_position[0], avatar_position[1]), nickname, fill=self.text_color, font=self.nickname_font)
        return result

    def calculate_name_bar(self,nickname):
        print(nickname)
        # 匹配中文字符
        cn_leng = len(re.findall(r'[\u4e00-\u9fff]', nickname))
        en_leng = len(nickname)- cn_leng#len(re.findall(r'[a-zA-Z]', nickname))
        print(en_leng,cn_leng)
        return int(1.92*self.nickname_font_size*en_leng + 4.18 * self.nickname_font_size*cn_leng)

def resize_by_scale(image, scale_factor):
    """按比例缩小图像"""
    width, height = image.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
