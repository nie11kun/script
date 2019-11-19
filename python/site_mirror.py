import platform
import os
import logging
import datetime
from os.path import dirname
from subprocess import Popen, PIPE

site = 'niekun.net'

windows_path = 'C:\\Users\\HJ_NK\\Documents\\GitHub\\nie11kun.github.io\\'
windows_log_path = 'C:\\Users\\HJ_NK\\log\\site_mirror.log'
windows_slash = '\\'

macOS_path = '/Users/marconie/Public/GitHub/nie11kun.github.io/'
linux_path = '/home/github/nie11kun.github.io/'
linux_log_path = '/var/log/site_morror.log'
linux_slash = '/'

if platform.system() == 'Windows':
    path = windows_path
    slash = windows_slash
    log_path = windows_log_path
elif platform.system() == 'Darwin':
    path = macOS_path
    slash = linux_slash
    log_path = linux_log_path
elif platform.system() == 'Linux':
    path = linux_path
    slash = linux_slash
    log_path = linux_log_path
else:
    path = linux_path
    slash = linux_slash
    log_path = linux_log_path

tempPath = dirname(path)

logging.basicConfig(filename=log_path, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('start mirror site: {}, output directory is {}'.format(site, path))

logger.info('sync remote github io')
print('sync remote github io')

cmd = 'cd {} && git checkout . && git pull'.format(path)
p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
it = iter(str(p[0], 'utf-8').split('\n'))

try:
    while "Already up-to-date" not in next(it): pass
except StopIteration:
    logger.error('pull error')
    print('pull error')
else:
    logger.info('start download site data')
    print('start download site data')

    cmd = 'cd {} && wget -m -p -k {}'.format(tempPath, site)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
    it = iter(str(p[0], 'utf-8').split('\n'))

    logger.info('moving new files')
    print('moving new files')
    tempPath = tempPath + slash + site
    os.system('cp -r {} {}'.format(tempPath + slash + '.', path))
    os.system('rm -r {}'.format(tempPath))

    logger.info('pushing to github io')
    print('pushing to github io')

    cmd = 'cd {} && git add . && git commit -m "{}" && git push'.format(path, datetime.datetime.now())
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
    it = iter(str(p[0], 'utf-8').split('\n'))

    logger.info('push finished')
    print('push finished')
    
    '''
    try:
        while "Everything up-to-date" not in next(str(p[0])): pass
    except StopIteration:
        logger.error('push error')
        print('push error')
    else:
        logger.info('push finished')
        print('push finished')
    '''