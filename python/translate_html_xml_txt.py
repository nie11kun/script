import asyncio
import aiohttp
from bs4 import BeautifulSoup, NavigableString
from pathlib import Path
import re
import argparse
import logging
from typing import List, Dict
from lxml import etree

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义命令行参数
parser = argparse.ArgumentParser(description='将中文文本翻译成指定语言的 HTML、XML 或 TXT 文件。', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--dir', '-d', help='包含 HTML、XML 或 TXT 文件的目录路径，包括子文件夹', required=False)
parser.add_argument('--file', '-f', help='单个 HTML、XML 或 TXT 文件的路径', required=False)
parser.add_argument('--lang', '-l', help='翻译目标语言（例如 "en" 为英文，"ru" 为俄文，"fr" 为法文等）', required=True)
args = parser.parse_args()

EXT_HTML = ".html"
EXT_XML = ".xml"
EXT_TXT = ".txt"
BLACKLIST = ["\ufeff", "\ufeff\n", "\n", "\r", ""]
PROXY = "http://127.0.0.1:1082"
BATCH_SIZE = 100  # 批量翻译的文本数量

async def translate_text(session: aiohttp.ClientSession, texts: List[str], target_lang: str) -> List[tuple]:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "zh-CN",
        "tl": target_lang,
        "dt": "t",
        "q": "\n".join(texts)
    }
    try:
        async with session.get(url, params=params, proxy=PROXY) as response:
            data = await response.json()
            return list(zip(texts, [item[0] for item in data[0]]))
    except Exception as e:
        logger.error(f"翻译错误: {e}")
        return list(zip(texts, texts))  # 出错时返回原文

async def process_html_file(file_path: Path, session: aiohttp.ClientSession, translation_cache: Dict[str, str], target_lang: str):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()

        # 使用正则表达式找到所有中文文本
        chinese_pattern = re.compile(r'([\u4e00-\u9fa5]+)')
        matches = chinese_pattern.findall(content)

        texts_to_translate = list(set(matches))
        texts_to_translate = [text for text in texts_to_translate if text not in BLACKLIST and text not in translation_cache]

        # 翻译新的文本
        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch = texts_to_translate[i:i+BATCH_SIZE]
            translations = await translate_text(session, batch, target_lang)
            for original, translated in translations:
                translation_cache[original] = translated

        # 替换原文中的中文
        def replace_chinese(match):
            text = match.group(1)
            return translation_cache.get(text, text).replace('\n', '')

        translated_content = chinese_pattern.sub(replace_chinese, content)

        # 使用 BeautifulSoup 来格式化 HTML
        soup = BeautifulSoup(translated_content, 'lxml')
        pretty_html = soup.prettify()

        # 移除额外的空行，保持原有的缩进结构
        lines = pretty_html.split('\n')
        cleaned_lines = [line for line in lines if line.strip()]

        # 写入文件
        with file_path.open("w", encoding="utf-8") as new_file:
            new_file.write('\n'.join(cleaned_lines))

        logger.info(f"处理 HTML 文件: {file_path}")
    except Exception as e:
        logger.error(f"处理 HTML 文件 {file_path} 时出错: {e}")

async def process_xml_file(file_path: Path, session: aiohttp.ClientSession, translation_cache: Dict[str, str], target_lang: str):
    try:
        # 读取 XML 文件
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()

        # 使用正则表达式找到所有需要翻译的文本（包括属性值和文本内容）
        chinese_pattern = re.compile(r'([\u4e00-\u9fa5]+)')
        matches = chinese_pattern.findall(content)

        texts_to_translate = list(set(matches))
        texts_to_translate = [text for text in texts_to_translate if text not in BLACKLIST and text not in translation_cache]

        # 翻译新的文本
        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch = texts_to_translate[i:i+BATCH_SIZE]
            translations = await translate_text(session, batch, target_lang)
            for original, translated in translations:
                translation_cache[original] = translated

        # 替换原文中的中文
        def replace_chinese(match):
            text = match.group(1)
            return translation_cache.get(text, text).replace('\n', '')

        translated_content = chinese_pattern.sub(replace_chinese, content)

        # 解析翻译后的 XML
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(translated_content.encode('utf-8'), parser)

        # 写入文件
        with file_path.open("wb") as f:
            f.write(etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True))

        logger.info(f"处理 XML 文件: {file_path}")
    except Exception as e:
        logger.error(f"处理 XML 文件 {file_path} 时出错: {e}")

async def process_txt_file(file_path: Path, session: aiohttp.ClientSession, translation_cache: Dict[str, str], target_lang: str):
    try:
        # 读取 TXT 文件
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()

        # 使用正则表达式找到所有中文文本
        chinese_pattern = re.compile(r'([\u4e00-\u9fa5]+)')
        matches = chinese_pattern.findall(content)

        texts_to_translate = list(set(matches))
        texts_to_translate = [text for text in texts_to_translate if text not in BLACKLIST and text not in translation_cache]

        # 翻译新的文本
        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch = texts_to_translate[i:i+BATCH_SIZE]
            translations = await translate_text(session, batch, target_lang)
            for original, translated in translations:
                translation_cache[original] = translated

        # 替换原文中的中文
        def replace_chinese(match):
            text = match.group(1)
            return translation_cache.get(text, text).replace('\n', '')

        translated_content = chinese_pattern.sub(replace_chinese, content)

        # 写入文件
        with file_path.open("w", encoding="utf-8") as f:
            f.write(translated_content)

        logger.info(f"处理 TXT 文件: {file_path}")
    except Exception as e:
        logger.error(f"处理 TXT 文件 {file_path} 时出错: {e}")

async def main():
    translation_cache = {}

    async with aiohttp.ClientSession() as session:
        if args.file:
            # 如果指定了单个文件路径，则处理该文件
            file_path = Path(args.file)
            if file_path.suffix == EXT_HTML:
                await process_html_file(file_path, session, translation_cache, args.lang)
            elif file_path.suffix == EXT_XML:
                await process_xml_file(file_path, session, translation_cache, args.lang)
            elif file_path.suffix == EXT_TXT:
                await process_txt_file(file_path, session, translation_cache, args.lang)
            else:
                logger.error("不支持的文件类型，请提供 .html、.xml 或 .txt 文件。")
        elif args.dir:
            # 如果指定了目录，则处理目录下所有 HTML、XML 和 TXT 文件
            dir_path = Path(args.dir)
            html_files = list(dir_path.rglob(f"*{EXT_HTML}"))
            xml_files = list(dir_path.rglob(f"*{EXT_XML}"))
            txt_files = list(dir_path.rglob(f"*{EXT_TXT}"))
            tasks = [process_html_file(file, session, translation_cache, args.lang) for file in html_files]
            tasks.extend([process_xml_file(file, session, translation_cache, args.lang) for file in xml_files])
            tasks.extend([process_txt_file(file, session, translation_cache, args.lang) for file in txt_files])
            await asyncio.gather(*tasks)
        else:
            logger.error("请指定目录路径 (--dir) 或单个文件路径 (--file)。")

if __name__ == "__main__":
    asyncio.run(main())
