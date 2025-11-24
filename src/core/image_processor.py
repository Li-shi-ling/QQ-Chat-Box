import os
from io import BytesIO
from typing import Literal, Tuple, Union
from PIL import Image

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]


class ImageProcessor:
    """图像处理核心类"""

    @staticmethod
    def load_image(image_source: Union[str, Image.Image]) -> Image.Image:
        """加载图像"""
        if isinstance(image_source, Image.Image):
            return image_source.copy()
        else:
            return Image.open(image_source).convert("RGBA")

    @staticmethod
    def paste_image_auto(
            base_image: Union[str, Image.Image],
            top_left: Tuple[int, int],
            bottom_right: Tuple[int, int],
            content_image: Image.Image,
            align: Align = "center",
            valign: VAlign = "middle",
            padding: int = 0,
            allow_upscale: bool = False,
            keep_alpha: bool = True,
            overlay_image: Union[str, Image.Image, None] = None,
    ) -> bytes:
        """
        在指定矩形内放置一张图片，按比例缩放至最大但不超过该矩形。
        """
        if not isinstance(content_image, Image.Image):
            raise TypeError("content_image 必须为 PIL.Image.Image")

        # 加载底图
        img = ImageProcessor.load_image(base_image)

        # 加载覆盖图层
        img_overlay = None
        if overlay_image is not None:
            img_overlay = ImageProcessor.load_image(overlay_image)

        # 验证区域坐标
        x1, y1 = top_left
        x2, y2 = bottom_right
        if not (x2 > x1 and y2 > y1):
            raise ValueError("无效的粘贴区域。")

        # 计算可用区域（考虑 padding）
        region_w = max(1, (x2 - x1) - 2 * padding)
        region_h = max(1, (y2 - y1) - 2 * padding)

        # 验证内容图像尺寸
        cw, ch = content_image.size
        if cw <= 0 or ch <= 0:
            raise ValueError("content_image 尺寸无效。")

        # 计算缩放比例
        scale_w = region_w / cw
        scale_h = region_h / ch
        scale = min(scale_w, scale_h)

        if not allow_upscale:
            scale = min(1.0, scale)

        # 调整图像尺寸
        new_w = max(1, int(round(cw * scale)))
        new_h = max(1, int(round(ch * scale)))
        resized = content_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 计算粘贴坐标
        px, py = ImageProcessor._calculate_position(
            x1, y1, x2, y2, new_w, new_h, padding, align, valign
        )

        # 粘贴图像
        if keep_alpha and ("A" in resized.getbands()):
            img.paste(resized, (px, py), resized)
        else:
            img.paste(resized, (px, py))

        # 添加覆盖图层
        if overlay_image is not None and img_overlay is not None:
            img.paste(img_overlay, (0, 0), img_overlay)

        # 输出 PNG bytes
        return ImageProcessor._image_to_bytes(img)

    @staticmethod
    def _calculate_position(
            x1: int, y1: int, x2: int, y2: int,
            content_w: int, content_h: int, padding: int,
            align: Align, valign: VAlign
    ) -> Tuple[int, int]:
        """计算粘贴位置"""
        region_w = (x2 - x1) - 2 * padding
        region_h = (y2 - y1) - 2 * padding

        # 水平对齐
        if align == "left":
            px = x1 + padding
        elif align == "center":
            px = x1 + padding + (region_w - content_w) // 2
        else:  # "right"
            px = x2 - padding - content_w

        # 垂直对齐
        if valign == "top":
            py = y1 + padding
        elif valign == "middle":
            py = y1 + padding + (region_h - content_h) // 2
        else:  # "bottom"
            py = y2 - padding - content_h

        return px, py

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        """将图像转换为字节流"""
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def is_vertical_image(image: Image.Image, ratio_threshold: float = 1.0) -> bool:
        """判断图像是否为竖图"""
        return image.height * ratio_threshold > image.width