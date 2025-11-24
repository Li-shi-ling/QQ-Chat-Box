from typing import Dict, List, Tuple


class DefaultConfig:
    """默认配置常量"""

    # 热键配置
    HOTKEY = "enter"
    SELECT_ALL_HOTKEY = "ctrl+a"
    CUT_HOTKEY = "ctrl+x"
    PASTE_HOTKEY = "ctrl+v"
    SEND_HOTKEY = "enter"
    BLOCK_HOTKEY = False

    # 进程控制
    ALLOWED_PROCESSES: List[str] = ["qq.exe", "weixin.exe"]

    # 时间控制
    DELAY = 0.1

    # 功能开关
    AUTO_PASTE_IMAGE = True
    AUTO_SEND_IMAGE = True

    # 日志配置
    LOGGING_LEVEL = "INFO"

    # 头像缓存位置
    AVATAR_CACHE_LOCATION = "./avatar"