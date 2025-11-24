import logging
import sys

def setup_logger(level: str = "INFO"):
    """设置日志配置"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('emoji_generator.log', encoding='utf-8')
        ]
    )