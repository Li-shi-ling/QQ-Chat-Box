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
        bubble_font_size=34,
        nickname_font_size=25,
        bubble_padding=20,
        bubble_bg_color=(255, 255, 255, 220),
        text_color=(0, 0, 0, 255),
        corner_radius=27,
        avatar_size=(89, 89),
        margin=20
    ):
        self.SCALE = 4  # supersampling 倍率

        # 气泡字体
        self.bubble_font = ImageFont.truetype(bubble_font_path, bubble_font_size * self.SCALE) \
            if os.path.exists(bubble_font_path) else ImageFont.load_default()

        # 昵称字体
        self.nickname_font = ImageFont.truetype(nickname_font_path, nickname_font_size * self.SCALE) \
            if os.path.exists(nickname_font_path) else ImageFont.load_default()

        self.bubble_font_size = bubble_font_size
        self.nickname_font_size = nickname_font_size
        self.bubble_padding = bubble_padding
        self.bubble_bg_color = bubble_bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.avatar_size = avatar_size
        self.margin = margin


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
    # 创建完整聊天消息（头像 + 气泡 + 昵称）
    # ------------------------------------------------------------------------------
    def create_chat_message(
        self,
        qq,
        text,
        bubble_position=(126, 50),
        avatar_position=(23, 10),
        background_color="#F0F0F2"
    ):
        info = get_qq_info(qq)
        assert info is not None, f"无法获取 QQ: {qq} 的信息"

        nickname = info["name"]
        avatar_path = info["avatar_path"]

        # 气泡
        bubble = self.create_chat_bubble(text)
        bubble_w, bubble_h = bubble.size

        # 昵称宽度（正常尺寸）
        nickname_font = ImageFont.truetype(
            "./resources/fonts/SourceHanSansSC-ExtraLight.otf",
            self.nickname_font_size
        )
        tmp = Image.new("RGBA", (10, 10))
        draw_tmp = ImageDraw.Draw(tmp)
        nickname_width = int(draw_tmp.textlength(nickname, font=nickname_font)) + self.bubble_padding

        # 背景尺寸
        bg_w = max(
            bubble_position[0] + bubble_w + self.margin,
            avatar_position[0] + self.avatar_size[0] + self.margin,
            bubble_position[0] + nickname_width
        )
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
        draw = ImageDraw.Draw(background)
        draw.text(
            (bubble_position[0], avatar_position[1]),
            nickname,
            fill=self.text_color,
            font=nickname_font
        )

        return background
