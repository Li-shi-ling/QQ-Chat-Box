import io
import logging
import time
from typing import Optional

import keyboard
import pyperclip

from src.config.config_loader import ConfigLoader
from src.core.clipboard_manager import ClipboardManager
from src.core.image_processor import ImageProcessor
from src.core.text_processor import TextProcessor
from src.utils.system_utils import SystemUtils
from src.utils.logger import setup_logger
import os



class EmojiGenerator:
    """表情生成器主类"""

    def __init__(self):
        self.config = ConfigLoader.load_config()
        self.current_emotion = "#普通#"
        self.current_base_image = self.config.baseimage_mapping.get(
            self.current_emotion, self.config.baseimage_file
        )
        self.region_ratio = 1.0
        os.environ['avatar_cache_location'] = self.config.avatar_cache_location
        # 初始化
        self._initialize()

    def _initialize(self):
        """初始化应用"""
        setup_logger(self.config.logging_level)
        self._register_hotkeys()
        self._calculate_region_ratio()

        logging.info("表情生成器初始化完成")
        logging.info(f"热键绑定: {self.config.hotkey}")
        logging.info(f"允许的进程: {self.config.allowed_processes}")
        logging.info(f"表情切换快捷键: {self.config.emotion_switch_hotkeys}")

    def _register_hotkeys(self):
        """注册热键"""
        # 主生成热键
        keyboard.add_hotkey(
            self.config.hotkey,
            self.generate_image,
            suppress=self.config.block_hotkey or self.config.hotkey == self.config.send_hotkey,
        )

        # 表情切换热键
        self._register_emotion_hotkeys()

    def _register_emotion_hotkeys(self):
        """注册表情切换热键"""
        for hotkey, emotion_tag in self.config.emotion_switch_hotkeys.items():
            keyboard.add_hotkey(
                hotkey,
                self.switch_emotion,
                args=(emotion_tag,),
                suppress=False
            )

    def _calculate_region_ratio(self):
        """计算区域比例"""
        self.region_ratio = SystemUtils.calculate_region_ratio(
            self.config.text_box_topleft,
            self.config.image_box_bottomright
        )
        logging.info(f"区域比例: {self.region_ratio}")

    def switch_emotion(self, emotion_tag: str):
        """切换表情"""
        self.current_emotion = emotion_tag
        self.current_base_image = self.config.baseimage_mapping.get(
            emotion_tag, self.config.baseimage_file
        )
        logging.info(f"已切换到表情: {emotion_tag} ({self.current_base_image})")

    def _extract_emotion_keyword(self, text: str) -> str:
        """从文本中提取表情关键词并更新当前表情"""
        cleaned_text = text

        for keyword, image_file in self.config.baseimage_mapping.items():
            if keyword in text:
                self.current_base_image = image_file
                cleaned_text = text.replace(keyword, "").strip()
                logging.info(f"检测到关键词 '{keyword}'，使用底图: {image_file}")
                break

        return cleaned_text

    def _process_mixed_content(self, text: str, image: ImageProcessor) -> Optional[bytes]:
        """处理同时包含文本和图片的内容"""
        x1, y1 = self.config.text_box_topleft
        x2, y2 = self.config.image_box_bottomright
        region_width = x2 - x1
        region_height = y2 - y1

        # 根据图片方向选择布局
        if ImageProcessor.is_vertical_image(image, self.region_ratio):
            logging.info("使用左右排布（竖图）")
            return self._create_side_by_side_layout(text, image, x1, y1, x2, y2, region_width)
        else:
            logging.info("使用上下排布（横图）")
            return self._create_top_bottom_layout(text, image, x1, y1, x2, y2, region_height)

    def _create_side_by_side_layout(self, text: str, image: ImageProcessor,
                                    x1: int, y1: int, x2: int, y2: int,
                                    region_width: int) -> bytes:
        """创建左右布局"""
        spacing = 10
        left_width = region_width // 2 - spacing // 2
        right_width = region_width - left_width - spacing

        left_region_right = x1 + left_width
        right_region_left = left_region_right + spacing

        # 先绘制图像
        intermediate_bytes = ImageProcessor.paste_image_auto(
            base_image=self.current_base_image,
            top_left=(x1, y1),
            bottom_right=(left_region_right, y2),
            content_image=image,
            align="center",
            valign="middle",
            padding=12,
            allow_upscale=True,
            keep_alpha=True,
            overlay_image=None,  # 暂时不应用overlay
        )

        # 再添加文本
        return TextProcessor.draw_text_auto(
            base_image=io.BytesIO(intermediate_bytes),
            top_left=(right_region_left, y1),
            bottom_right=(x2, y2),
            text=text,
            color=(0, 0, 0),
            max_font_height=64,
            font_path=self.config.font_file,
            overlay_image=self.config.base_overlay_file if self.config.use_base_overlay else None,
            wrap_algorithm=self.config.text_wrap_algorithm,
        )

    def _create_top_bottom_layout(self, text: str, image: ImageProcessor,
                                  x1: int, y1: int, x2: int, y2: int,
                                  region_height: int) -> bytes:
        """创建上下布局"""
        estimated_text_height = min(region_height // 2, 100)
        image_region_bottom = y1 + (region_height - estimated_text_height)
        text_region_top = image_region_bottom

        # 先绘制图像
        intermediate_bytes = ImageProcessor.paste_image_auto(
            base_image=self.current_base_image,
            top_left=(x1, y1),
            bottom_right=(x2, image_region_bottom),
            content_image=image,
            align="center",
            valign="middle",
            padding=12,
            allow_upscale=True,
            keep_alpha=True,
            overlay_image=None,  # 暂时不应用overlay
        )

        # 再添加文本
        return TextProcessor.draw_text_auto(
            base_image=io.BytesIO(intermediate_bytes),
            top_left=(x1, text_region_top),
            bottom_right=(x2, y2),
            text=text,
            color=(0, 0, 0),
            max_font_height=64,
            font_path=self.config.font_file,
            overlay_image=self.config.base_overlay_file if self.config.use_base_overlay else None,
            wrap_algorithm=self.config.text_wrap_algorithm,
        )

    def generate_image(self):
        """生成图像的主函数"""
        # 检查进程权限
        if not self._check_process_permission():
            return

        # 获取用户输入
        user_image = ClipboardManager.get_image_from_clipboard()
        user_text, old_clipboard = ClipboardManager.cut_all_and_get_text(
            self.config.select_all_hotkey,
            self.config.cut_hotkey,
            self.config.delay
        )

        logging.debug(f"用户输入 - 文本: '{user_text}', 图片: {user_image is not None}")

        # 处理输入
        if not user_text and not user_image:
            logging.info("未检测到文本或图片输入，取消生成")
            return

        # 生成图片
        png_bytes = self._create_final_image(user_text, user_image)
        if not png_bytes:
            return

        # 输出结果
        self._output_result(png_bytes, old_clipboard)

    def _check_process_permission(self) -> bool:
        """检查进程权限"""
        if not self.config.allowed_processes:
            return True

        current_process = SystemUtils.get_foreground_process_name()
        allowed = SystemUtils.is_process_allowed(current_process, self.config.allowed_processes)

        if not allowed:
            logging.info(f"当前进程 {current_process} 不在允许列表中，跳过执行")
            if not self.config.block_hotkey:
                keyboard.send(self.config.hotkey)
            return False

        return True

    def _create_final_image(self, text: str, image: Optional[ImageProcessor]) -> Optional[bytes]:
        """创建最终图像"""
        x1, y1 = self.config.text_box_topleft
        x2, y2 = self.config.image_box_bottomright

        try:
            # 提取表情关键词
            cleaned_text = self._extract_emotion_keyword(text)

            # 根据输入类型处理
            if not text and image:
                logging.info("从剪切板中捕获了图片内容")
                return ImageProcessor.paste_image_auto(
                    base_image=self.current_base_image,
                    top_left=(x1, y1),
                    bottom_right=(x2, y2),
                    content_image=image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True,
                    keep_alpha=True,
                    overlay_image=self.config.base_overlay_file if self.config.use_base_overlay else None,
                )

            elif text and not image:
                logging.info(f"从文本生成图片: {cleaned_text}")
                return TextProcessor.draw_text_auto(
                    base_image=self.current_base_image,
                    top_left=(x1, y1),
                    bottom_right=(x2, y2),
                    text=cleaned_text,
                    color=(0, 0, 0),
                    max_font_height=64,
                    font_path=self.config.font_file,
                    overlay_image=self.config.base_overlay_file if self.config.use_base_overlay else None,
                    wrap_algorithm=self.config.text_wrap_algorithm,
                )

            else:  # 同时有文本和图片
                logging.info("同时处理文本和图片内容")
                logging.info(f"文本内容: {cleaned_text}")
                return self._process_mixed_content(cleaned_text, image)

        except Exception as e:
            logging.error(f"生成图片失败: {e}")
            return None

    def _output_result(self, png_bytes: bytes, old_clipboard: str):
        """输出结果到剪贴板并执行后续操作"""
        # 复制到剪贴板
        ClipboardManager.copy_png_to_clipboard(png_bytes)

        # 自动粘贴和发送
        if self.config.auto_paste_image:
            keyboard.send(self.config.paste_hotkey)
            time.sleep(self.config.delay)

            if self.config.auto_send_image:
                keyboard.send(self.config.send_hotkey)

        # 恢复原始剪贴板内容
        pyperclip.copy(old_clipboard)
        logging.info("成功地生成并发送图片！")

    def run(self):
        """运行主循环"""
        logging.info("键盘监听已启动，按下 {} 以生成图片".format(self.config.hotkey))

        try:
            keyboard.wait()
        except KeyboardInterrupt:
            logging.info("程序已退出")
        except Exception as e:
            logging.error(f"程序运行出错: {e}")


if __name__ == "__main__":
    # 创建默认配置文件（如果不存在）
    ConfigLoader.create_default_config()

    # 运行应用
    app = EmojiGenerator()
    app.run()