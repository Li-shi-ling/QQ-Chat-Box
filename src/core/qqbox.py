from PIL import Image
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
    download_avatar(avatar_url, os.path.join(avatar_cache_location,f"{qq}-{name}.jpg"))
    return True


