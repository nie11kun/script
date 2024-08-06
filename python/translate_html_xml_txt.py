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

async def translate_text(session: aiohttp.ClientSession, texts: List[str], target_lang: str) -> List[str]:
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
            return [item[0] for item in data[0]]
    except Exception as e:
        logger.error(f"翻译错误: {e}")
        return texts

async def process_html_file(file_path: Path, session: aiohttp.ClientSession, translation_cache: Dict[str, str], target_lang: str):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml')

        # 找到所有需要翻译的文本
        elements_to_translate = soup.find_all(string=lambda text: isinstance(text, NavigableString) and re.search(r"[\u4e00-\u9fa5]", text))

        texts_to_translate = []
        for element in elements_to_translate:
            text = element.strip()
            if text and text not in BLACKLIST and text not in translation_cache:
                texts_to_translate.append(text)

        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch = texts_to_translate[i:i+BATCH_SIZE]
            translated_texts = await translate_text(session, batch, target_lang)
            for original, translated in zip(batch, translated_texts):
                translation_cache[original] = translated

        # 替换文本内容
        for element in elements_to_translate:
            text = element.strip()
            if text in translation_cache:
                element.replace_with(translation_cache[text])

        # 使用 BeautifulSoup 保存时规范缩进
        pretty_html = soup.prettify()

        with file_path.open("w", encoding="utf-8") as new_file:
            new_file.write(pretty_html)

        logger.info(f"处理 HTML 文件: {file_path}")
    except Exception as e:
        logger.error(f"处理 HTML 文件 {file_path} 时出错: {e}")

async def process_xml_file(file_path: Path, session: aiohttp.ClientSession, translation_cache: Dict[str, str], target_lang: str):
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()

        # 提取需要翻译的 title 属性值
        def extract_and_translate_title_attributes(element: etree.Element) -> List[str]:
            texts = []
            if 'title' in element.attrib and re.search(r"[\u4e00-\u9fa5]", element.attrib['title']):
                texts.append(element.attrib['title'].strip())
            for child in element:
                texts.extend(extract_and_translate_title_attributes(child))
            return texts

        # 更新 title 属性值
        def update_title_attributes(element: etree.Element):
            if 'title' in element.attrib and element.attrib['title'] in translation_cache:
                element.attrib['title'] = translation_cache[element.attrib['title']]
            for child in element:
                update_title_attributes(child)

        title_texts = extract_and_translate_title_attributes(root)
        texts_to_translate = [text for text in title_texts if text not in BLACKLIST and text not in translation_cache]

        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch = texts_to_translate[i:i+BATCH_SIZE]
            translated_texts = await translate_text(session, batch, target_lang)
            for original, translated in zip(batch, translated_texts):
                translation_cache[original] = translated

        update_title_attributes(root)

        # 保存 XML 文档
        with file_path.open('wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True, pretty_print=True)

        logger.info(f"处理 XML 文件: {file_path}")
    except Exception as e:
        logger.error(f"处理 XML 文件 {file_path} 时出错: {e}")

async def process_txt_file(file_path: Path, session: aiohttp.ClientSession, translation_cache: Dict[str, str], target_lang: str):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # 提取需要翻译的行
        texts_to_translate = [line.strip() for line in lines if re.search(r"[\u4e00-\u9fa5]", line)]

        # 翻译文本
        translated_lines = []
        for i in range(0, len(texts_to_translate), BATCH_SIZE):
            batch = texts_to_translate[i:i+BATCH_SIZE]
            translated_texts = await translate_text(session, batch, target_lang)
            for original, translated in zip(batch, translated_texts):
                translation_cache[original] = translated

        # 生成翻译后的内容
        for line in lines:
            stripped_line = line.strip()
            if stripped_line in translation_cache:
                translated_line = line.replace(stripped_line, translation_cache[stripped_line])
                # 保留原有的换行符
                translated_lines.append(translated_line)
            else:
                translated_lines.append(line)

        # 写回翻译后的内容
        with file_path.open("w", encoding="utf-8") as f:
            # 使用 "\n".join(translated_lines) 保证每行之间有换行符，避免多余的空行
            f.write("".join(translated_lines).replace("\n\n", "\n"))

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
