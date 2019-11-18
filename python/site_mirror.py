import platform
import os
import logging
import datetime
from os.path import dirname

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

site = 'niekun.net'

windows_path = 'C:\\Users\\HJ_NK\\Documents\\GitHub\\nie11kun.github.io\\'
windows_slash = '\\'

macOS_path = '/Users/marconie/Public/GitHub/nie11kun.github.io/'
linux_path = '/home/github/nie11kun.github.io/'
linux_slash = '/'

if platform.system() == 'Windows':
    path = windows_path
    slash = windows_slash
elif platform.system() == 'Darwin':
    path = macOS_path
    slash = linux_slash
elif platform.system() == 'Linux':
    path = linux_path
    slash = linux_slash
else
    path = linux_path
    slash = linux_slash

tempPath = dirname(path)

logger.info('start mirror site: {}, output directory is {}'.format(site, path))

logger.info('sync remote github io')
os.system('cd {} && git checkout . && git pull'.format(path))

try:
    logger.info('download start')
    os.system('cd {} && wget -m -p -k {}'.format(tempPath, site))
except:
    logger.info('error')
finally:
    logger.info('download finished')
    
    logger.info('moving new files')
    tempPath = tempPath + slash + site
    os.system('cp -r {} {}'.format(tempPath + slash + '.', path))
    os.system('rm -r {}'.format(tempPath))

    logger.info('pushing to github io')
    os.system('cd {} && git add . && git commit -m "{}" && git push'.format(path, datetime.datetime.now()))

    logger.info('push finished')

