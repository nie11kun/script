import platform
import os
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

site = 'niekun.net'

windows_path = 'C:\\Users\\HJ_NK\\Documents'
macOS_path = '/usr/marconie/download'

if platform.system() == 'Windows':
    path = windows_path
elif platform.system() == 'Darwin':
    path = macOS_path
else:
    path = macOS_path

logger.info('start mirror site: {}, output directory is {}'.format(site, path))

try:
    os.system('wget -o {0} -m -p -k {1}'.format(path, site))
except:
    logger.info('error')
else:
    logger.info('finished')

