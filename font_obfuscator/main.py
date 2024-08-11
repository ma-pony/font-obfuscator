import random
from base64 import b64encode
from os import path

from fontTools.ttLib import TTFont, newTable, BytesIO
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable


def filter_font_characters(font: "TTFont", required_chars: str):
    """
    从字体文件中提取所需字符，生成新的字体文件
    :param font:
    :param required_chars:
    :return:
    """
    # 创建新的字体文件
    new_font = TTFont()
    new_font['head'] = font['head']

    # 设置 name 表

    new_font['name'] = newTable("name")

    # 设置 OS/2 表
    new_font["OS/2"] = font["OS/2"]

    # 设置 post 表
    new_font["post"] = font["post"]

    # 获取 cmap 表
    cmap = font['cmap']
    tables = cmap.tables

    # 提取所需字符的编码
    required_codepoints = {ord(char) for char in required_chars}
    best_cmap = cmap.getBestCmap()
    required_glyphs = {best_cmap.get(codepoint) for codepoint in required_codepoints if best_cmap.get(codepoint)}

    # 获取所有字形名称
    glyf_table = font['glyf']

    # 移除不需要的字形
    for glyph_name in list(glyf_table.glyphs.keys()):
        if glyph_name not in required_glyphs:
            glyf_table.glyphs.pop(glyph_name, None)
    glyf_table.glyphOrder = list(glyf_table.glyphs.keys())

    new_font['glyf'] = glyf_table

    # 创建并设置 loca 表
    new_loca = newTable('loca')

    offsets = []
    offset = 0

    for glyph_name in glyf_table.glyphOrder:
        offsets.append(offset)
        glyph = glyf_table.glyphs[glyph_name]
        if glyph is not None:
            glyph_data = glyph.compile(font)
            offset += len(glyph_data)
        else:
            offsets.append(offset)

    offsets.append(offset)

    if new_font['head'].indexToLocFormat == 0:
        new_loca.locations = [int(o / 2) for o in offsets]
    else:
        new_loca.locations = offsets

    new_font['loca'] = new_loca

    # 重新构建glyphOrder
    new_font.setGlyphOrder(list(required_glyphs))

    # 重建 hmtx 表
    hmtx_table = font['hmtx']
    hmtx_table.metrics = {glyph_name: hmtx_table.metrics[glyph_name] for glyph_name in required_glyphs}
    new_font['hmtx'] = hmtx_table

    # 重建 maxp 和 hhea 表
    new_font['maxp'] = font['maxp']
    new_font['maxp'].numGlyphs = len(required_glyphs)

    new_font['hhea'] = font['hhea']
    new_font['hhea'].numOfHMetrics = len(required_glyphs)

    new_font['fvar'] = font['fvar']

    gvar = font['gvar']
    gvar.variations = {glyph_name: gvar.variations[glyph_name] for glyph_name in required_glyphs}
    new_font['gvar'] = gvar

    new_cmap = newTable('cmap')
    new_cmap.tableVersion = 0

    # 更新 cmap 表
    new_tables = []
    for table in tables:
        if table.format in (4, 12):  # 只处理 Unicode 格式的 cmap 表
            new_table = CmapSubtable.newSubtable(table.format)
            new_table.platformID = table.platformID
            new_table.platEncID = table.platEncID
            new_table.language = table.language
            new_table.cmap = {
                codepoint: glyph_name for codepoint, glyph_name in table.cmap.items() if codepoint in required_codepoints
            }
            new_tables.append(new_table)

    new_cmap.tables = new_tables

    new_font['cmap'] = new_cmap

    return new_font


def shuffle_font(
        font: "TTFont",
        start_codepoint: int,
        end_codepoint: int,
):
    """
    混淆字体文件，将指定范围内的字符映射到非指定范围内的字符
    :param font:
    :param start_codepoint:
    :param end_codepoint:
    :return:
    """
    # 提取 Unicode 字符和字形映射
    cmap_table = font['cmap']
    unicode_mappings = {}

    for table in cmap_table.tables:
        if table.format in (4, 12):  # 处理 Unicode 格式的 cmap 表
            unicode_mappings.update(table.cmap)

    # 提取所有字符和字形映射
    chars = list(unicode_mappings.keys())

    # 创建非常用汉字的字符集
    obf_codepoints = list(range(start_codepoint)) + list(range(end_codepoint, 65535))
    random.shuffle(obf_codepoints)
    obf_codepoints = obf_codepoints[0:(end_codepoint - start_codepoint + 1)]

    obf_codepoints_map = {}

    for codepoint in chars:
        if start_codepoint <= codepoint <= end_codepoint:
            obf_codepoints_map[codepoint] = obf_codepoints.pop()

    # 更新 cmap 表
    for table in font['cmap'].tables:
        if table.format in (4, 12):  # 确保是 Unicode 格式的 cmap 表
            new_table_cmap = {}
            for old_codepoint, glyph_id in table.cmap.items():
                if start_codepoint <= old_codepoint <= end_codepoint:
                    new_codepoint = obf_codepoints_map.get(old_codepoint)
                    new_table_cmap[new_codepoint] = glyph_id
                elif old_codepoint in obf_codepoints:
                    continue
                else:
                    new_table_cmap[old_codepoint] = glyph_id
            table.cmap = new_table_cmap

    return font, obf_codepoints_map


def obfuscator_text(
        input_text: str,
        font_path: str = path.join(path.dirname(__file__), "default.ttf"),
        codepoint_range: tuple[int, int] = (19968, 40959),
        only_return_input_chars: bool = True,
        b64encode_output: bool = True,
):
    """
    混淆字体文件，将指定范围内的字符映射到非指定范围内的字符

    返回混淆后的文本和字体文件

    :param input_text: 输入文本
    :param font_path: 字体文件路径
    :param codepoint_range: 混淆字符区间
    :param only_return_input_chars: 仅返回包含输入文本中的字符文件
    :param b64encode_output: 是否对输出文件进行 base64 编码
    :return:
    """
    obf_io = BytesIO()
    # 读取字体文件
    font = TTFont(font_path)

    # 混淆字体
    font, obf_codepoints_map = shuffle_font(
        font,
        codepoint_range[0],
        codepoint_range[1],
    )

    # 返回输入文本在新字体中的映射
    obf_text = ''
    for char in input_text:
        old_codepoint = ord(char)
        obf_codepoint = obf_codepoints_map.get(old_codepoint, old_codepoint)
        obf_text += chr(obf_codepoint)

    if only_return_input_chars:
        # 仅返回输入文本中的字符文件
        obf_font = filter_font_characters(font, obf_text)
        obf_font.save(obf_io)
    else:
        obf_font = font
        obf_font.save(obf_io)
    if b64encode_output:
        return obf_text, b64encode(obf_io.getvalue()).decode()
    return obf_text, obf_io.getvalue()


if __name__ == '__main__':
    test_text = "这是一段测试文本"
    obf_text, obf_io = obfuscator_text(test_text)

    print(f"Origin Text: {test_text}")
    print(f"Obf Text: {obf_text}")
    print(f"Obf Font: {obf_io}")
    test_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Custom Font Example</title>
    <style>
        @font-face {
            font-family: 'ShuffledFont';
            src: url('data:font/ttf;base64,ObfFont') format('truetype');
        }
        .custom-font {
            font-family: 'ShuffledFont';
        }
    </style>
</head>
<body>
    <h1 class="custom-font">ObfText</h1>
</body>
</html>
""".replace("ObfFont", obf_io).replace("ObfText", obf_text)
    print(test_html)
