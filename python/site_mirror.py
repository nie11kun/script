import platform
import os
import shutil
import logging
import datetime
from os.path import dirname
from subprocess import run, PIPE

site = 'blog.niekun.net'

windows_path = 'C:\\Users\\HJ_NK\\Documents\\GitHub\\nie11kun.github.io\\'
windows_log_path = 'C:\\Users\\HJ_NK\\log\\site_mirror.log'
windows_slash = '\\'

macOS_path = '/Users/marconie/Public/GitHub/nie11kun.github.io/'
linux_path = '/home/www/nie11kun.github.io/'
linux_log_path = '/var/log/site_mirror.log'
linux_slash = '/'

if platform.system() == 'Windows':
    path = windows_path
    slash = windows_slash
    log_path = windows_log_path
elif platform.system() == 'Darwin':
    path = macOS_path
    slash = linux_slash
    log_path = linux_log_path
else:
    path = linux_path
    slash = linux_slash
    log_path = linux_log_path

# download outside the repo: parent directory of the repo
tempPath = dirname(path.rstrip(slash))
sitePath = tempPath + slash + site

logging.basicConfig(filename=log_path, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def log(msg, error=False):
    (logger.error if error else logger.info)(msg)
    print(msg)


def git(*args):
    p = run(['git', '-C', path] + list(args), stdout=PIPE, stderr=PIPE)
    if p.returncode != 0:
        log('git {} failed: {}'.format(' '.join(args), p.stderr.decode('utf-8', 'ignore').strip()), True)
    return p.returncode == 0


log('start mirror site: {}, output directory is {}'.format(site, path))

# remove leftovers from an interrupted run
shutil.rmtree(sitePath, ignore_errors=True)
shutil.rmtree(path + site, ignore_errors=True)

log('start download site data')
p = run('cd {} && wget -m -p -k --no-check-certificate {}'.format(tempPath, site), shell=True, stdout=PIPE, stderr=PIPE)

if 'FINISHED' not in p.stderr.decode('utf-8', 'ignore'):
    log('download error', True)
else:
    log('moving new files')
    os.system('cp -r {} {}'.format(sitePath + slash + '.', path))
    shutil.rmtree(sitePath, ignore_errors=True)

    # keep no history: commit a single snapshot on a fresh orphan branch and force push it
    log('pushing to github io')
    run(['git', '-C', path, 'branch', '-D', 'snapshot'], stdout=PIPE, stderr=PIPE)
    ok = git('checkout', '-q', '--orphan', 'snapshot') \
        and git('add', '-A') \
        and git('commit', '-q', '-m', str(datetime.datetime.now())) \
        and git('branch', '-M', 'master') \
        and git('push', '-f', 'origin', 'master')

    if not ok:
        log('push error', True)
    else:
        log('push finished')

        # drop the old snapshots from the local repo
        log('cleaning local history')
        git('reflog', 'expire', '--expire=now', '--all')
        git('-c', 'pack.threads=1', '-c', 'pack.windowMemory=64m', 'gc', '-q', '--prune=now')
        log('clean finished')