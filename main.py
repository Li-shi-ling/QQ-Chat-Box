import io
import logging
import time
from typing import Optional
from src.core.qqbox import ChatBubbleGenerator, resize_by_scale, get_qq_info
from PIL import Image

import keyboard
import pyperclip

from src.config.config_loader import ConfigLoader
from src.core.clipboard_manager import ClipboardManager
from src.utils.system_utils import SystemUtils
from src.utils.logger import setup_logger
import os



class EmojiGenerator:
    """表情生成器主类"""

    def __init__(self):
        self.config = ConfigLoader.load_config()
        os.environ['avatar_cache_location'] = self.config.avatar_cache_location
        # 初始化
        self._initialize()
        self.qqbox = ChatBubbleGenerator()
        self.qq = None
        self.set_qq()

    def _initialize(self):
        """初始化应用"""
        setup_logger(self.config.logging_level)
        self._register_hotkeys()
        logging.info("表情生成器初始化完成")
        logging.info(f"热键绑定: {self.config.hotkey}")
        logging.info(f"允许的进程: {self.config.allowed_processes}")

    def set_qq(self):
        self.qq = input("QQ:")
        if get_qq_info(self.qq) is None:
            logging.info(f"没找到对应qq")

    def _register_hotkeys(self):
        """注册热键"""
        # 主生成热键
        keyboard.add_hotkey(
            self.config.hotkey,
            self.generate_image,
            suppress=self.config.block_hotkey or self.config.hotkey == self.config.send_hotkey,
        )

        keyboard.add_hotkey(
            "ctrl+1",
            self.set_qq,
        )

    def generate_image(self):
        """生成图像的主函数"""
        # 检查进程权限
        if not self._check_process_permission():
            return

        # 获取用户输入
        user_text, old_clipboard = ClipboardManager.cut_all_and_get_text(
            self.config.select_all_hotkey,
            self.config.cut_hotkey,
            self.config.delay
        )

        logging.debug(f"用户输入 - 文本: '{user_text}'")

        # 处理输入
        if not user_text:
            logging.info("未检测到文本输入，取消生成")
            return

        # 生成图片
        # -------------------------------------------------------------
        png = resize_by_scale(
            self.qqbox.create_chat_message(self.qq, user_text),
            0.5
        )
        if not png:
            return

        # 输出结果
        self._output_result(png, old_clipboard)

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

    def _output_result(self, png: Image, old_clipboard: str):
        """输出结果到剪贴板并执行后续操作"""
        # 复制到剪贴板
        ClipboardManager.copy_png_to_clipboard(png)

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

    # 运行应用
    app = EmojiGenerator()
    app.run()