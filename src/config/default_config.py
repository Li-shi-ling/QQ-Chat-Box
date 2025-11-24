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

    # 文件路径
    FONT_FILE = "resources/fonts/font.ttf"
    BASEIMAGE_FILE = "resources/base_images/base.png"
    BASE_OVERLAY_FILE = "resources/base_images/base_overlay.png"

    # 表情映射
    BASEIMAGE_MAPPING: Dict[str, str] = {
        "#普通#": "resources/base_images/base.png",
        "#开心#": "resources/base_images/开心.png",
        "#生气#": "resources/base_images/生气.png",
        "#无语#": "resources/base_images/无语.png",
        "#脸红#": "resources/base_images/脸红.png",
        "#病娇#": "resources/base_images/病娇.png",
    }

    # 区域坐标
    TEXT_BOX_TOPLEFT: Tuple[int, int] = (119, 450)
    IMAGE_BOX_BOTTOMRIGHT: Tuple[int, int] = (398, 625)

    # 功能开关
    USE_BASE_OVERLAY = True
    AUTO_PASTE_IMAGE = True
    AUTO_SEND_IMAGE = True

    # 日志配置
    LOGGING_LEVEL = "INFO"

    # 表情切换快捷键
    EMOTION_SWITCH_HOTKEYS: Dict[str, str] = {
        "alt+1": "#普通#",
        "alt+2": "#开心#",
        "alt+3": "#生气#",
        "alt+4": "#无语#",
        "alt+5": "#脸红#",
        "alt+6": "#病娇#",
    }

    # 文本处理
    TEXT_WRAP_ALGORITHM = "original"  # "original" 或 "knuth_plass"