from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import os

# ------------------------------------------------------------------------------
# 获取 QQ 信息（缓存 + API）
# ------------------------------------------------------------------------------
def get_qq_info(qq):
    avatar_cache = os.environ.get("avatar_cache_location", ".")
    if not os.path.exists(avatar_cache):
        os.makedirs(avatar_cache)

    # 先查缓存
    for filename in os.listdir(avatar_cache):
        if filename.startswith(f"{qq}-") and filename.endswith(".png"):
            nickname = filename[len(f"{qq}-"):-4]
            return {
                "qq": qq,
                "name": nickname,
                "avatar_path": os.path.join(avatar_cache, filename)
            }

    # 请求 API
    url = f"https://uapis.cn/api/v1/social/qq/userinfo?qq={qq}"
    res = requests.get(url)
    if res.status_code != 200:
        return None

    data = res.json()
    nickname = data.get("nickname", qq)
    # avatar_url = data.get("avatar_url")
    avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"
    # avatar_url = f"http://q.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640&img_type=png"

    save_path = os.path.join(avatar_cache, f"{qq}-{nickname}.png")
    download_circular_avatar(avatar_url, save_path)

    return {
        "qq": qq,
        "name": nickname,
        "avatar_path": save_path
    }

def create_circular_avatar(img,size=None):
    # 中心裁剪正方形
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    if size is None:
        size = min(w,h)
    # 调整大小
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    # 创建圆形遮罩
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result

# ------------------------------------------------------------------------------
# 下载头像并裁剪为圆形
# ------------------------------------------------------------------------------
def download_circular_avatar(url, save_path="avatar.png", size=None):
    try:
        r = requests.get(url)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        result = create_circular_avatar(img)
        result.save(save_path)
        return save_path
    except:
        return None

# ------------------------------------------------------------------------------
# 兼容性函数：按比例缩放图像
# ------------------------------------------------------------------------------
def resize_by_scale(image, scale_factor):
    w, h = image.size
    return image.resize((int(w * scale_factor), int(h * scale_factor)), Image.Resampling.LANCZOS)

# ------------------------------------------------------------------------------
# 高 DPI 超清聊天气泡生成器
# ------------------------------------------------------------------------------
class ChatBubbleGenerator:
    def __init__(
        self,
        bubble_font_path="./resources/fonts/Microsoft-YaHei-Semilight.ttc",
        nickname_font_path="./resources/fonts/SourceHanSansSC-ExtraLight.otf",
        title_font_path="./resources/fonts/Microsoft-YaHei-Bold.ttc",
        bubble_font_size=34,
        nickname_font_size=25,
        title_font_size=19,
        bubble_padding=20,
        title_padding_x=25,
        title_padding_y=15,
        title_padding_y_offset=8,
        title_bubble_offset=5,
        bubble_bg_color=(255, 255, 255, 220),
        text_color=(0, 0, 0, 255),
        corner_radius=27,
        avatar_size=(89, 89),
        margin=20,
        title_bubble_name_offset=-1,
    ):
        self.SCALE = 4  # supersampling 倍率

        # 气泡字体
        self.bubble_font = ImageFont.truetype(bubble_font_path, bubble_font_size * self.SCALE)  if os.path.exists(bubble_font_path) else ImageFont.load_default()

        # 昵称字体
        self.nickname_font = ImageFont.truetype(nickname_font_path, nickname_font_size)  if os.path.exists(nickname_font_path) else ImageFont.load_default()

        # 头衔字体
        self.title_SCALE_font = ImageFont.truetype(title_font_path, title_font_size * self.SCALE)  if os.path.exists(nickname_font_path) else ImageFont.load_default()
        self.title_font = ImageFont.truetype(title_font_path, title_font_size) if os.path.exists(nickname_font_path) else ImageFont.load_default()

        self.title_padding_x = title_padding_x
        self.title_padding_y = title_padding_y
        self.bubble_font_size = bubble_font_size
        self.nickname_font_size = nickname_font_size
        self.title_font_size = title_font_size
        self.bubble_padding = bubble_padding
        self.bubble_bg_color = bubble_bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.avatar_size = avatar_size
        self.margin = margin
        self.title_bubble_offset = title_bubble_offset
        self.title_padding_y_offset = title_padding_y_offset
        self.title_bubble_name_offset = title_bubble_name_offset


    # ------------------------------------------------------------------------------
    # 创建聊天气泡（高 DPI supersampling）
    # ------------------------------------------------------------------------------
    def create_chat_bubble(self, text):
        SCALE = self.SCALE
        font = self.bubble_font
        padding = self.bubble_padding * SCALE
        max_width = 640 * SCALE

        # 临时画布测量文本
        tmp = Image.new("RGBA", (10, 10))
        draw_tmp = ImageDraw.Draw(tmp)

        lines = []
        current = ""
        for ch in text:
            test = current + ch
            if ch == "\n":
                lines.append(current)
                current = ""
            else:
                try:
                    w = draw_tmp.textlength(test, font=font)
                except:
                    ch = " "
                    test = current + ch
                    w = draw_tmp.textlength(test, font=font)
                if w <= max_width - padding * 2:
                    current = test
                else:
                    lines.append(current)
                    current = ch
        if current:
            lines.append(current)
        # 保留原 bbox 行高算法
        bbox = font.getbbox("字")
        line_height = int(bbox[3] - bbox[1] + 4 * SCALE)
        text_height = line_height * len(lines)
        text_width = max(draw_tmp.textlength(line, font=font) for line in lines)
        width = int(text_width + padding * 2)
        height = text_height + padding * (2 + len(lines))
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            (0, 0, width, height),
            radius=self.corner_radius * SCALE,
            fill=self.bubble_bg_color,
            outline=(230, 230, 230, 255),
            width=2 * SCALE
        )

        y = padding
        for line in lines:
            draw.text((padding, y), line, fill=self.text_color, font=font)
            y += line_height + padding

        # 缩回正常尺寸实现高清
        img = img.resize((width // SCALE, height // SCALE), Image.Resampling.LANCZOS)
        return img

    # ------------------------------------------------------------------------------
    # 添加创建头衔气泡的方法
    # ------------------------------------------------------------------------------
    def create_title_bubble(self, text, bg_color):
        """创建头衔气泡（与昵称气泡样式相同）"""
        SCALE = self.SCALE
        font = self.title_SCALE_font

        # 测量文本
        tmp = Image.new("RGBA", (10, 10))
        draw_tmp = ImageDraw.Draw(tmp)
        text_width = int(draw_tmp.textlength(text, font=font))

        # 获取字体高度
        bbox = font.getbbox(text)
        text_height = int(bbox[3] - bbox[1] + 4 * SCALE)

        # 添加内边距
        width = int(text_width + self.title_padding_x * 2)
        height = int(text_height + self.title_padding_y * 3)

        # 创建头衔气泡
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制圆角矩形背景
        draw.rounded_rectangle(
            (0, 0, width, height),
            radius=8 * SCALE,
            fill=bg_color
        )

        # 绘制头衔文字（白色文字）
        draw.text(
            (self.title_padding_x, self.title_padding_y_offset),
            text,
            fill=(255, 255, 255, 255),
            font=font
        )

        # 缩回正常尺寸
        img = img.resize((width // SCALE, height // SCALE), Image.Resampling.LANCZOS)
        return img

    # ------------------------------------------------------------------------------
    # 创建完整聊天消息（头像 + 气泡 + 昵称）
    # ------------------------------------------------------------------------------
    def create_chat_message(
        self,
        qq,
        text,
        qq_title_key = None,
        bubble_position=(120, 60),
        avatar_position=(23, 10),
        background_color="#F0F0F2"
    ):
        print(qq)
        print(text)
        print(qq_title_key)
        print(bubble_position)
        print(avatar_position)
        print(background_color)
        info = get_qq_info(qq)
        assert info is not None, f"无法获取 QQ: {qq} 的信息"

        nickname = info["name"]
        avatar_path = info["avatar_path"]

        # 气泡
        bubble = self.create_chat_bubble(text)
        bubble_w, bubble_h = bubble.size

        # 昵称宽度（正常尺寸）
        tmp = Image.new("RGBA", (10, 10))
        draw_tmp = ImageDraw.Draw(tmp)

        # 头衔
        qq_title = qq_title_key.get(qq, None)
        is_title = not qq_title is None
        if is_title:
            tmp_nickname = qq_title.get("notes",None)
            content = qq_title.get("content","")
            title_color = qq_title.get("color","1")
            if not tmp_nickname is None:
                nickname = tmp_nickname
            nickname_width = int(draw_tmp.textlength(nickname, font=self.nickname_font)) + self.bubble_padding
            title_width = int(draw_tmp.textlength(content, font=self.title_font)) + self.bubble_padding
            bg_w = max(
                bubble_position[0] + bubble_w + self.margin,
                avatar_position[0] + self.avatar_size[0] + self.margin,
                bubble_position[0] + nickname_width + title_width + self.title_bubble_name_offset
            )
        else:
            nickname_width = int(draw_tmp.textlength(nickname, font=self.nickname_font)) + self.bubble_padding
            # 背景尺寸
            bg_w = max(
                bubble_position[0] + bubble_w + self.margin,
                avatar_position[0] + self.avatar_size[0] + self.margin,
                bubble_position[0] + nickname_width
            )

        # 背景尺寸
        bg_h = max(
            bubble_position[1] + bubble_h + self.margin,
            avatar_position[1] + self.avatar_size[1] + self.margin
        )

        # 背景
        r = int(background_color[1:3], 16)
        g = int(background_color[3:5], 16)
        b = int(background_color[5:7], 16)
        background = Image.new("RGBA", (bg_w, bg_h), (r, g, b, 255))

        # 贴气泡
        background.paste(bubble, bubble_position, bubble)

        # 贴头像
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar = avatar.resize(self.avatar_size, Image.Resampling.LANCZOS)
        background.paste(avatar, avatar_position, avatar)

        # 昵称
        if is_title:
            color_map = {
                1: (181, 182, 181, 220),  # #B5B6B5
                2: (214, 154, 255, 220),  # #D69AFF
                3: (255, 198, 41, 220),  # #FFC629
                4: (82, 215, 197, 220)  # #52D7C5
            }
            title_bg_color = color_map.get(int(title_color), color_map[1])
            title_bubble = self.create_title_bubble(content,title_bg_color)
            background.paste(title_bubble, (bubble_position[0], avatar_position[1] + self.title_bubble_offset), title_bubble)
            draw = ImageDraw.Draw(background)
            draw.text(
                (bubble_position[0] + title_width + self.title_bubble_name_offset, avatar_position[1]),
                nickname,
                fill=self.text_color,
                font=self.nickname_font
            )
        else:
            # 昵称
            draw = ImageDraw.Draw(background)
            draw.text(
                (bubble_position[0], avatar_position[1]),
                nickname,
                fill=self.text_color,
                font=self.nickname_font
            )
        return background
