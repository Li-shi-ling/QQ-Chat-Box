import logging
from typing import Optional
import psutil
import win32gui
import win32process


class SystemUtils:
    """系统工具类"""

    @staticmethod
    def get_foreground_process_name() -> Optional[str]:
        """获取当前前台窗口的进程名称"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().lower()

        except Exception as e:
            logging.error(f"无法获取当前进程名称: {e}")
            return None

    @staticmethod
    def is_process_allowed(
            current_process: Optional[str],
            allowed_processes: list
    ) -> bool:
        """检查当前进程是否在允许列表中"""
        if not allowed_processes:
            return True

        if current_process is None:
            return False

        allowed_processes_lower = [p.lower() for p in allowed_processes]
        return current_process in allowed_processes_lower

    @staticmethod
    def calculate_region_ratio(
            top_left: tuple,
            bottom_right: tuple
    ) -> float:
        """计算区域宽高比"""
        try:
            x1, y1 = top_left
            x2, y2 = bottom_right
            return (x2 - x1) / (y2 - y1)
        except Exception as e:
            logging.error(f"计算比例时出错: {e}")
            return 1.0