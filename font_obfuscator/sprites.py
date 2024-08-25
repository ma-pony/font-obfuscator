from base64 import b64encode
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def create_image_with_text(
        text,
        font_path="default.ttf",
        font_size=40,
        padding=0,
        bg_color=(255, 255, 255, 0),
        text_color=(0, 0, 0, 255),
        max_width=800
):
    # 加载字体
    font = ImageFont.truetype(font_path, font_size)

    # 创建一个临时的绘制对象，用于计算文本尺寸
    temp_image = Image.new('RGBA', (1, 1), bg_color)
    draw = ImageDraw.Draw(temp_image)

    # 将文本分割成多行，确保每行宽度不超过 max_width
    lines = []
    words = list(text)
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    # 计算每一行的宽度和文本的总高度
    total_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines)
    max_line_width = max(draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0] for line in lines)

    # 根据文本尺寸和 padding 计算图像尺寸
    width = max_line_width + 2 * padding
    height = total_height + 2 * padding + len(lines) * 5

    # 创建适当大小的图像
    image = Image.new('RGBA', (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # 绘制每一行文本
    y = padding
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill=text_color)
        y += line_height

    image_io = BytesIO()

    # 保存图片
    image.save(image_io, 'PNG')
    image.show()

    image_binary_data = image_io.getvalue()

    base64_image = b64encode(image_binary_data).decode()

    return base64_image,

# 示例使用
create_image_with_text("This is a sample text that will be automatically wrapped into multiple lines based on the maximum width provided.")
