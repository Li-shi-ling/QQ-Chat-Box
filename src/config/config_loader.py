import os
from typing import Dict, Any, Tuple, List
import yaml
from pydantic import BaseModel

from .default_config import DefaultConfig


class ConfigModel(BaseModel):
    """配置数据模型"""
    hotkey: str = DefaultConfig.HOTKEY
    allowed_processes: List[str] = DefaultConfig.ALLOWED_PROCESSES
    select_all_hotkey: str = DefaultConfig.SELECT_ALL_HOTKEY
    cut_hotkey: str = DefaultConfig.CUT_HOTKEY
    paste_hotkey: str = DefaultConfig.PASTE_HOTKEY
    send_hotkey: str = DefaultConfig.SEND_HOTKEY
    block_hotkey: bool = DefaultConfig.BLOCK_HOTKEY
    delay: float = DefaultConfig.DELAY
    font_file: str = DefaultConfig.FONT_FILE
    baseimage_mapping: Dict[str, str] = DefaultConfig.BASEIMAGE_MAPPING
    baseimage_file: str = DefaultConfig.BASEIMAGE_FILE
    text_box_topleft: Tuple[int, int] = DefaultConfig.TEXT_BOX_TOPLEFT
    image_box_bottomright: Tuple[int, int] = DefaultConfig.IMAGE_BOX_BOTTOMRIGHT
    base_overlay_file: str = DefaultConfig.BASE_OVERLAY_FILE
    use_base_overlay: bool = DefaultConfig.USE_BASE_OVERLAY
    auto_paste_image: bool = DefaultConfig.AUTO_PASTE_IMAGE
    auto_send_image: bool = DefaultConfig.AUTO_SEND_IMAGE
    logging_level: str = DefaultConfig.LOGGING_LEVEL
    emotion_switch_hotkeys: Dict[str, str] = DefaultConfig.EMOTION_SWITCH_HOTKEYS
    text_wrap_algorithm: str = DefaultConfig.TEXT_WRAP_ALGORITHM

    class Config:
        arbitrary_types_allowed = True


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_config(config_file: str = "config/config.yaml") -> ConfigModel:
        """
        从YAML文件加载配置

        Args:
            config_file: 配置文件路径

        Returns:
            ConfigModel: 配置对象
        """
        # 如果配置文件不存在，使用默认配置
        if not os.path.exists(config_file):
            return ConfigModel()

        try:
            # 读取YAML配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 处理坐标值，确保它们是元组而不是列表
            ConfigLoader._process_coordinates(config_data)

            # 创建并返回配置对象
            return ConfigModel(**config_data)

        except Exception as e:
            print(f"加载配置文件失败，使用默认配置: {e}")
            return ConfigModel()

    @staticmethod
    def _process_coordinates(config_data: Dict[str, Any]):
        """处理坐标配置"""
        if 'text_box_topleft' in config_data and isinstance(config_data['text_box_topleft'], list):
            config_data['text_box_topleft'] = tuple(config_data['text_box_topleft'])

        if 'image_box_bottomright' in config_data and isinstance(config_data['image_box_bottomright'], list):
            config_data['image_box_bottomright'] = tuple(config_data['image_box_bottomright'])

    @staticmethod
    def create_default_config(config_file: str = "config/config.yaml"):
        """创建默认配置文件"""
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        default_config = {
            'hotkey': DefaultConfig.HOTKEY,
            'allowed_processes': DefaultConfig.ALLOWED_PROCESSES,
            'select_all_hotkey': DefaultConfig.SELECT_ALL_HOTKEY,
            'cut_hotkey': DefaultConfig.CUT_HOTKEY,
            'paste_hotkey': DefaultConfig.PASTE_HOTKEY,
            'send_hotkey': DefaultConfig.SEND_HOTKEY,
            'block_hotkey': DefaultConfig.BLOCK_HOTKEY,
            'delay': DefaultConfig.DELAY,
            'font_file': DefaultConfig.FONT_FILE,
            'baseimage_mapping': DefaultConfig.BASEIMAGE_MAPPING,
            'baseimage_file': DefaultConfig.BASEIMAGE_FILE,
            'text_box_topleft': list(DefaultConfig.TEXT_BOX_TOPLEFT),
            'image_box_bottomright': list(DefaultConfig.IMAGE_BOX_BOTTOMRIGHT),
            'base_overlay_file': DefaultConfig.BASE_OVERLAY_FILE,
            'use_base_overlay': DefaultConfig.USE_BASE_OVERLAY,
            'auto_paste_image': DefaultConfig.AUTO_PASTE_IMAGE,
            'auto_send_image': DefaultConfig.AUTO_SEND_IMAGE,
            'logging_level': DefaultConfig.LOGGING_LEVEL,
            'emotion_switch_hotkeys': DefaultConfig.EMOTION_SWITCH_HOTKEYS,
            'text_wrap_algorithm': DefaultConfig.TEXT_WRAP_ALGORITHM,
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True, indent=2)

        print(f"默认配置文件已创建: {config_file}")