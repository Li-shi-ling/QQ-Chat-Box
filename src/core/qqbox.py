from PIL import Image, ImageDraw
from io import BytesIO
import requests
import json
import os

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
        
        print(f"头像已成功下载到: {save_path}")
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
        print(f"头像已成功下载到: {save_path} (尺寸: {image.size})")
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
    avatar_cache_location = os.environ.get('avatar_cache_location')
    response = requests.get(f"https://uapis.cn/api/v1/social/qq/userinfo?qq={qq}")
    data = json.loads(response.text)
    if response.status_code == 200:
        name = data["nickname"]
        qq = data["qq"]
        avatar_url = data["avatar_url"]
    else:
        return False
    download_circular_avatar(avatar_url, os.path.join(avatar_cache_location, f"{qq}-{name}.png"))
    return True

