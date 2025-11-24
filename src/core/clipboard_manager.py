import io
import time
import logging
from typing import Optional, Tuple
import keyboard
import pyperclip
import win32clipboard
from PIL import Image


class ClipboardManager:
    """剪贴板管理类"""

    @staticmethod
    def copy_png_to_clipboard(png_bytes: bytes):
        """将PNG字节流复制到剪贴板"""
        try:
            image = Image.open(io.BytesIO(png_bytes))

            # 转换为BMP格式（Windows剪贴板需要）
            with io.BytesIO() as output:
                image.convert("RGB").save(output, "BMP")
                bmp_data = output.getvalue()[14:]  # 去掉BMP文件头

            # 写入剪贴板
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
            win32clipboard.CloseClipboard()

        except Exception as e:
            logging.error(f"复制到剪贴板失败: {e}")
            raise

    @staticmethod
    def get_image_from_clipboard() -> Optional[Image.Image]:
        """从剪贴板获取图像"""
        try:
            win32clipboard.OpenClipboard()

            # 检查剪贴板中是否有图像
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                return None

            # 获取图像数据
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            if not data:
                return None

            # 转换为PIL图像
            header = (
                    b"BM"
                    + (len(data) + 14).to_bytes(4, "little")
                    + b"\x00\x00\x00\x00\x36\x00\x00\x00"
            )
            image = Image.open(io.BytesIO(header + data))
            return image

        except Exception as e:
            logging.error(f"从剪贴板获取图像失败: {e}")
            return None
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    @staticmethod
    def cut_all_and_get_text(
            select_hotkey: str = "ctrl+a",
            cut_hotkey: str = "ctrl+x",
            delay: float = 0.1
    ) -> Tuple[str, str]:
        """
        模拟全选和剪切操作，获取文本内容

        Returns:
            Tuple[新剪贴板内容, 原剪贴板内容]
        """
        # 备份原剪贴板内容
        old_clipboard = pyperclip.paste()

        # 清空剪贴板
        pyperclip.copy("")

        # 发送全选和剪切快捷键
        keyboard.send(select_hotkey)
        time.sleep(delay)
        keyboard.send(cut_hotkey)
        time.sleep(delay)

        # 获取剪切后的内容
        new_clipboard = pyperclip.paste()

        return new_clipboard, old_clipboard