import platform
import os
import logging
import datetime
from os.path import dirname

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

site = 'niekun.net'

windows_path = 'C:\\Users\\HJ_NK\\Documents\\'
windows_slash = '\\'

macOS_path = '/Users/marconie/Public/GitHub/nie11kun.github.io/'
macOS_slash = '/'

if platform.system() == 'Windows':
    path = windows_path
    slash = windows_slash
elif platform.system() == 'Darwin':
    path = macOS_path
    slash = macOS_slash
else:
    path = macOS_path
    slash = macOS_slash

tempPath = dirname(path)

logger.info('start mirror site: {}, output directory is {}'.format(site, path))

logger.info('sync remote github io')
os.system('cd {} && git checkout . && git pull'.format(path))

try:
    os.system('cd {} && wget -m -p -k {}'.format(tempPath, site))
except:
    logger.info('error')
else:
    logger.info('download finished, pushing to github io')

    tempPath = tempPath + slash + site
    os.system('cp -r {} {}'.format(tempPath + slash + '.', path))
    os.system('rm -r {}'.format(tempPath))

    os.system('cd {} && git add . && git commit -m "{}" && git push'.format(path, datetime.datetime.now()))

    logger.info('push finished')

