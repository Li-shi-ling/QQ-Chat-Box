import os
from io import BytesIO
from typing import List, Literal, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont
from src.core.image_processor import ImageProcessor

RGBColor = Tuple[int, int, int]
Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]


class TextProcessor:
    """文本处理核心类"""

    @staticmethod
    def _load_font(font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        """加载字体"""
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def wrap_lines(
            draw: ImageDraw.ImageDraw,
            text: str,
            font: ImageFont.FreeTypeFont,
            max_width: int
    ) -> List[str]:
        """文本换行（原始算法）"""
        lines: List[str] = []

        for paragraph in text.splitlines() or [""]:
            has_space = " " in paragraph
            units = paragraph.split(" ") if has_space else list(paragraph)
            buffer = ""

            def join_units(a: str, b: str) -> str:
                if not a:
                    return b
                return (a + " " + b) if has_space else (a + b)

            for unit in units:
                trial = join_units(buffer, unit)
                width = draw.textlength(trial, font=font)

                if width <= max_width:
                    buffer = trial
                    continue

                if buffer:
                    lines.append(buffer)

                if has_space and len(unit) > 1:
                    temp = ""
                    for char in unit:
                        if draw.textlength(temp + char, font=font) <= max_width:
                            temp += char
                            continue

                        if temp:
                            lines.append(temp)
                        temp = char
                    buffer = temp
                    continue

                if draw.textlength(unit, font=font) <= max_width:
                    buffer = unit
                else:
                    lines.append(unit)
                    buffer = ""

            if buffer:
                lines.append(buffer)

        return lines

    @staticmethod
    def _is_bracket_token(token: str) -> bool:
        """判断是否为括号token"""
        return token.startswith("【") and token.endswith("】")

    @staticmethod
    def _split_long_token(
            draw: ImageDraw.ImageDraw,
            token: str,
            font: ImageFont.FreeTypeFont,
            max_width: int
    ) -> List[str]:
        """分割过长的token"""
        if draw.textlength(token, font=font) <= max_width:
            return [token]

        # 处理括号token
        if TextProcessor._is_bracket_token(token) and len(token) > 2:
            inner = token
            chunks = []
            buffer = ""

            for char in inner:
                trial = buffer + char
                if draw.textlength(trial, font=font) <= max_width:
                    buffer = trial
                else:
                    if buffer:
                        chunks.append(buffer)
                    buffer = char
            if buffer:
                chunks.append(buffer)

            return chunks

        # 普通token分割
        parts = []
        buffer = ""
        for char in token:
            trial = buffer + char
            if draw.textlength(trial, font=font) <= max_width:
                buffer = trial
            else:
                if buffer:
                    parts.append(buffer)
                buffer = char
        if buffer:
            parts.append(buffer)

        return parts

    @staticmethod
    def tokenize(
            draw: ImageDraw.ImageDraw,
            text: str,
            font: ImageFont.FreeTypeFont,
            max_width: int
    ) -> List[str]:
        """文本分词"""
        tokens = []
        buffer = ""
        in_bracket = False

        for char in text:
            if char in "【[":
                if buffer:
                    tokens.append(buffer)
                buffer = "【"
                in_bracket = True
            elif char in "】]":
                buffer += "】"
                tokens.append(buffer)
                buffer = ""
                in_bracket = False
            elif in_bracket:
                buffer += char
            elif char.isspace():
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                tokens.append(char)
            else:
                if char.isascii() and char.isalpha():
                    buffer += char
                else:
                    if buffer:
                        tokens.append(buffer)
                        buffer = ""
                    tokens.append(char)

        if buffer:
            tokens.append(buffer)

        # 分割过长的token
        final_tokens = []
        for token in tokens:
            if not token:
                continue
            if draw.textlength(token, font=font) <= max_width:
                final_tokens.append(token)
            else:
                splits = TextProcessor._split_long_token(draw, token, font, max_width)
                final_tokens.extend(splits)

        return final_tokens

    @staticmethod
    def wrap_lines_knuth_plass(
            draw: ImageDraw.ImageDraw,
            text: str,
            font: ImageFont.FreeTypeFont,
            max_width: int
    ) -> List[str]:
        """Knuth-Plass换行算法"""
        tokens = TextProcessor.tokenize(draw, text, font, max_width)
        n = len(tokens)
        widths = [draw.textlength(t, font=font) for t in tokens]

        # 累积宽度
        cumulative = [0.0] * (n + 1)
        for i in range(n):
            cumulative[i + 1] = cumulative[i] + widths[i]

        INF = float("inf")
        dp = [INF] * (n + 1)
        prev = [-1] * (n + 1)
        dp[0] = 0.0

        # 动态规划计算最优换行
        for i in range(1, n + 1):
            for j in range(i - 1, -1, -1):
                line_width = cumulative[i] - cumulative[j]
                if line_width > max_width:
                    break

                remaining = max_width - line_width
                badness = remaining ** 2
                if i == n:  # 最后一行
                    badness = 0.0

                cost = dp[j] + badness
                if cost < dp[i]:
                    dp[i] = cost
                    prev[i] = j

        # 回溯构建行
        if prev[n] == -1:
            return TextProcessor.wrap_lines(draw, text, font, max_width)

        lines = []
        idx = n
        while idx > 0:
            j = prev[idx]
            lines.append("".join(tokens[j:idx]))
            idx = j

        lines.reverse()
        return lines

    @staticmethod
    def parse_color_segments(
            text: str,
            in_bracket: bool,
            bracket_color: RGBColor,
            default_color: RGBColor
    ) -> Tuple[List[Tuple[str, RGBColor]], bool]:
        """解析颜色分段"""
        segments = []
        buffer = ""

        for char in text:
            if char in "【[":
                if buffer:
                    segments.append((buffer, bracket_color if in_bracket else default_color))
                    buffer = ""
                segments.append((char, bracket_color))
                in_bracket = True
            elif char in "】]":
                if buffer:
                    segments.append((buffer, bracket_color))
                    buffer = ""
                segments.append((char, bracket_color))
                in_bracket = False
            else:
                buffer += char

        if buffer:
            segments.append((buffer, bracket_color if in_bracket else default_color))

        return segments, in_bracket

    @staticmethod
    def measure_text_block(
            draw: ImageDraw.ImageDraw,
            lines: List[str],
            font: ImageFont.FreeTypeFont,
            line_spacing: float,
    ) -> Tuple[int, int, int]:
        """测量文本块尺寸"""
        ascent, descent = font.getmetrics()
        line_height = int((ascent + descent) * (1 + line_spacing))
        max_width = 0

        for line in lines:
            max_width = max(max_width, int(draw.textlength(line, font=font)))

        total_height = max(line_height * max(1, len(lines)), 1)
        return max_width, total_height, line_height

    @staticmethod
    def draw_text_auto(
            base_image: Union[str, Image.Image],
            top_left: Tuple[int, int],
            bottom_right: Tuple[int, int],
            text: str,
            color: RGBColor = (0, 0, 0),
            max_font_height: Optional[int] = None,
            font_path: Optional[str] = None,
            align: Align = "center",
            valign: VAlign = "middle",
            line_spacing: float = 0.15,
            bracket_color: RGBColor = (128, 0, 128),
            overlay_image: Union[str, Image.Image, None] = None,
            wrap_algorithm: str = "original"
    ) -> bytes:
        """在指定区域内自适应绘制文本"""
        # 加载底图
        img = ImageProcessor.load_image(base_image)
        draw = ImageDraw.Draw(img)

        # 加载覆盖图层
        img_overlay = None
        if overlay_image is not None:
            img_overlay = ImageProcessor.load_image(overlay_image)

        # 验证区域
        x1, y1 = top_left
        x2, y2 = bottom_right
        if not (x2 > x1 and y2 > y1):
            raise ValueError("无效的文字区域。")

        region_width, region_height = x2 - x1, y2 - y1

        # 二分查找最佳字体大小
        hi = min(region_height, max_font_height) if max_font_height else region_height
        lo, best_size, best_lines, best_line_height, best_block_height = 1, 0, [], 0, 0

        while lo <= hi:
            mid = (lo + hi) // 2
            font = TextProcessor._load_font(font_path, mid)

            # 选择换行算法
            if wrap_algorithm == "knuth_plass":
                lines = TextProcessor.wrap_lines_knuth_plass(draw, text, font, region_width)
            else:
                lines = TextProcessor.wrap_lines(draw, text, font, region_width)

            width, height, line_height = TextProcessor.measure_text_block(
                draw, lines, font, line_spacing
            )

            if width <= region_width and height <= region_height:
                best_size, best_lines, best_line_height, best_block_height = mid, lines, line_height, height
                lo = mid + 1
            else:
                hi = mid - 1

        # 使用最佳配置或回退到最小配置
        if best_size == 0:
            font = TextProcessor._load_font(font_path, 1)
            if wrap_algorithm == "knuth_plass":
                best_lines = TextProcessor.wrap_lines_knuth_plass(draw, text, font, region_width)
            else:
                best_lines = TextProcessor.wrap_lines(draw, text, font, region_width)
            best_block_height, best_line_height = 1, 1
            best_size = 1
        else:
            font = TextProcessor._load_font(font_path, best_size)

        # 计算垂直起始位置
        if valign == "top":
            y_start = y1
        elif valign == "middle":
            y_start = y1 + (region_height - best_block_height) // 2
        else:
            y_start = y2 - best_block_height

        # 绘制文本
        y_pos = y_start
        in_bracket = False

        for line in best_lines:
            line_width = int(draw.textlength(line, font=font))

            # 计算水平位置
            if align == "left":
                x_pos = x1
            elif align == "center":
                x_pos = x1 + (region_width - line_width) // 2
            else:
                x_pos = x2 - line_width

            # 绘制带颜色的分段文本
            segments, in_bracket = TextProcessor.parse_color_segments(
                line, in_bracket, bracket_color, color
            )

            for segment_text, segment_color in segments:
                if segment_text:
                    draw.text((x_pos, y_pos), segment_text, font=font, fill=segment_color)
                    x_pos += int(draw.textlength(segment_text, font=font))

            y_pos += best_line_height
            if y_pos - y_start > region_height:
                break

        # 添加覆盖图层
        if overlay_image is not None and img_overlay is not None:
            img.paste(img_overlay, (0, 0), img_overlay)

        # 输出为字节流
        return ImageProcessor._image_to_bytes(img)