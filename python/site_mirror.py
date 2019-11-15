import platform
import os
import logging
import datetime
from os.path import dirname

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

site = 'niekun.net'

windows_path = 'C:\\Users\\HJ_NK\\Documents\\'

macOS_path = '/Users/marconie/Public/GitHub/nie11kun.github.io/'

if platform.system() == 'Windows':
    path = windows_path
    fileInFolder = '\\.'
elif platform.system() == 'Darwin':
    path = macOS_path
    fileInFolder = '/.'
else:
    path = macOS_path
    fileInFolder = '/.'

tempPath = dirname(path)

logger.info('start mirror site: {}, output directory is {}'.format(site, path))

try:
    os.system('cd {} && wget -m -p -k {}'.format(tempPath, site))
except:
    logger.info('error')
else:
    tempPath = tempPath + site
    os.system('cp -r {} {}'.format(tempPath + fileInFolder, path))
    os.system('rm -r {}'.format(tempPath))

    logger.info('download finished, pushing to github io')

    os.system('cd {} && git add . && git commit -m "{}" && git push'.format(path, datetime.datetime.now()))

    logger.info('push finished')

