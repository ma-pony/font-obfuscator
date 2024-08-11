# font-obfuscator

## 项目简介

字体混淆工具是一个开源的 Python 库，旨在通过混淆字体文件中的字符到字形映射，防止网页内容被爬虫轻松提取。该工具允许您在 TrueType Font (TTF) 文件中打乱或加密字符映射，从而增加网站文本的安全性。

## 功能特点

- 字符混淆: 打乱或加密 TTF 字体文件中的字符到字形映射。
- 字符集筛选: 只保留字体文件中的指定字符，移除所有其他字符。
- 易于集成: 作为独立的 Python 函数使用，可集成到现有项目中。

## 环境要求

Python 3.10+
FontTools

## 安装步骤

```shell

pip install font-obfuscator
```

## 使用方法

###基本示例

```python
from font_obfuscator import obfuscator_text

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
```