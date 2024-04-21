# pip install googletrans==4.0.0-rc1
# pip install beautifulsoup4

# python .\translate_html.py -h 查看帮助信息

from googletrans import Translator
from bs4 import BeautifulSoup
from httpcore import SyncHTTPProxy
import re, os, argparse

# 定义命令行可用参数
parser = argparse.ArgumentParser(description='translate chinese to english in html', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--dir', '-d', help='需要翻译的 html 文件所在路径 包含子文件夹',required=True)
# parser.add_argument('--test', '-t', help='非必要参数，但是有默认值', default=2017)
args = parser.parse_args()

ext = ".html"

all_files = []

# 定义 https 代理服务
proxy = {"https": SyncHTTPProxy((b"http", b"127.0.0.1", 1082, b""))}

# 跳过需要翻译的字符串数组中的特殊字符 防止报错
blacklist = ["\ufeff", "\ufeff\n", "\n", "\r", ""]

# 获取目录下的所有文件 包括子文件夹
def get_files(path):
    lsdir = os.listdir(path)
    dirs = [i for i in lsdir if os.path.isdir(os.path.join(path, i))]
    files = [i for i in lsdir if os.path.isfile(os.path.join(path, i))]
    if files:
        for f in files:
            all_files.append(os.path.join(path, f))
    if dirs:
        for d in dirs:
            get_files(os.path.join(path, d)) # 递归查找

get_files(args.dir)
for file in all_files:
    if os.path.splitext(file)[1] == ext: # 过滤指定扩展名的文件
        # 打开源HTML文件，读取内容
        with open(file, "r", encoding="utf-8") as f:
            html = f.read()

            # 将HTML内容传递给BeautifulSoup对象
            soup = BeautifulSoup(html, features="html.parser")

            # 获取HTML内容中所有需要翻译的文本
            elements_to_translate = soup.find_all(string=True)

            # 初始化一个谷歌翻译对象
            translator = Translator(service_urls=["translate.google.com"], proxies=proxy)

            # 对每一个需要翻译的文本进行翻译
            for element in elements_to_translate:
                if element not in blacklist:
                    pattern = re.compile(r"[\u4e00-\u9fa5]")  # 只翻译包含中文字符的字符串 否则可能出现 indexError 报错
                    match = pattern.search(element)  # 判断字符串中是否有中文
                    if match:
                        element.replace("\n", "").replace("\r", "")
                        try:
                            # 翻译文本
                            translated_text = translator.translate(
                                element, src="zh-cn", dest="en"
                            ).text
                        except TypeError:
                            continue  # 遇到类型错误 则跳过
                        except IndexError:
                            break  # 索引报错直接退出循环
                        else:
                            # 用翻译后的文本替换原始文本
                            element.replace_with(translated_text)

            # 将翻译后的HTML保存到文件
            with open(file, "w", encoding="utf-8") as new_file:
                new_file.write(soup.prettify())
