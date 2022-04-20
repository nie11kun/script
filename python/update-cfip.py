from subprocess import Popen, PIPE
import logging
import re

# --------------------------------------------------

log_path = 'C:\\Users\\Marco Nie\\log\\update-cfip.log'
cloudflareIPListDir = 'C:\\Users\\Marco Nie\\Development\\VPN\\cloudflare\\'
cloudflareIPFile = 'Google Cloud.txt'
cloudflareSTDir = 'C:\\Users\\Marco Nie\\Application\\CloudflareST_windows_amd64'
cloudflareResultFile = 'C:\\Users\\Marco Nie\\Application\\CloudflareST_windows_amd64\\result.csv'
v2rayDir = 'C:\\Users\\Marco Nie\\Application\\v2ray\\'
v2rayDnsFile = 'conf.d\\dns.json'

reloadService = '''
taskkill /f /im v2ray.exe 
cd "{}".format(v2rayDir)
v2ray -confdir conf.d'
'''

lossLimit = 0.25
delayLimit = 500
dlspeedLimit = 0.5

# --------------------------------------------------

open(log_path,'a+')

logging.basicConfig(filename=log_path, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('update ip list')
print('update ip list')

cmd = 'cd "{}" && git reset --soft HEAD^ && git reset && git checkout . && git pull'.format(cloudflareIPListDir)
out, err = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
print(out.decode("utf-8", 'ignore'))

logger.info('start testing cf ip, please wait a while...')
print('start testing cf ip, please wait a while...')

ips = []

cmd = 'cd "{}" && "./CloudflareST" -f "{}{}" -o "{}" -p 0'.format(cloudflareSTDir, cloudflareIPListDir, cloudflareIPFile, cloudflareResultFile)

out, err = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()

f = open(cloudflareResultFile, 'rb')
s = f.read()
f.close()

it = iter(s.decode("utf-8", 'ignore').split('\n'))

# print(s.decode("utf-8", 'ignore'))

while True:
    try:
        line = next(it)
        if len(line.strip().split(',')) != 6:
            continue
    except StopIteration:
        break
    else:
        ip, send, recive, loss, delay, dlspeed = line.strip().split(',')# strip() Remove spaces at the beginning and at the end of the string
        if send.isdigit() == True:
            if float(loss) <= lossLimit and float(delay) <= delayLimit and float(dlspeed) >= dlspeedLimit:
                ips.append(ip)
                logger.info('foud ip: {}'.format(ip))
                print('foud ip: ', ip)

if len(ips) == 0:
    logger.info('not have good ips')
    print('not have good ips')
else:
    newip = '"domain:niekun.net": ["{}"]'.format(ips[0])
    try:
        logger.info('updating config')
        print('updating config')
        with open('{}{}'.format(v2rayDir, v2rayDnsFile), "rb") as f:
            s = f.read().decode("gbk", 'ignore')
            s = re.sub('("domain:niekun\.net": \[")\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}("])', newip, s, flags = re.M)
        with open('{}{}'.format(v2rayDir, v2rayDnsFile), "w") as f:
            f.write(s)
            f.close()

            logger.info('restarting service')
            print('restarting service')
            out, err = Popen(reloadService, shell=True, stdout=PIPE, stderr=PIPE).communicate()
            print(out.decode("utf-8", 'ignore'))
    except FileNotFoundError as f:
        print("Could not find the file you are trying to read.")
