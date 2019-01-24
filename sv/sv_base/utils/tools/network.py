# -*- coding: utf-8 -*-
import logging
import socket
import subprocess
import time
import re


logger = logging.getLogger(__name__)


def cport(ip, port, timeout=2):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(timeout)
    try:
        sk.connect((ip, port))
    except Exception:
        result = False
    else:
        result = True

    sk.close()
    return result


def ping(ip, timeout=2, count=2):
    try:
        res = subprocess.check_output('ping -c %s -w %s %s' % (count, timeout, ip), shell=True)
    except:
        return False
    if res.find('icmp_'):
        return True
    return False


def get_ping(ip):
    try:
        p = subprocess.getoutput("ping -c 1 {}".format(ip))
        pattern = re.compile(r"rtt min/avg/max/mdev = .*/(.*?)/.*/0.000 ms")
        delay = int(float(pattern.findall(p)[0]))
    except:
        delay = 0
    return delay


# 结合check_port和ping
def probe(ip, port=None, timeout=2, step_time=2, limit_time=300, stop_check_len=5, stop_check=None, callback=None, timeout_callback=None, log_prefix='probe'):
    # 找不到端口则ping检查
    if port:
        checker = cport
        args = (ip, port, timeout)
        dst_info = '%s:%s' % (ip, port)
    else:
        checker = ping
        args = (ip, timeout)
        dst_info = ip

    if not ip:
        logger.error('[%s] %s check %s: no ip' % (log_prefix, checker.__name__, dst_info))
        return

    if stop_check:
        stop_check_time = 0
    all_time = 0

    while True:
        logger.info('[%s] %s check %s: %ss' % (log_prefix, checker.__name__, dst_info, all_time))
        enter_time = time.time()
        if checker(*args):
            logger.info('[%s] %s check %s ok' % (log_prefix, checker.__name__, dst_info))
            if callback:
                callback()
            break

        # 限制检查频率
        time_interval = round(time.time() - enter_time, 2)
        remain_time = step_time - time_interval
        if remain_time > 0:
            time.sleep(remain_time)
        # 超时不再检查
        all_time += step_time

        if all_time > limit_time:
            logger.info('[%s] %s check %s timeout' % (log_prefix, checker.__name__, dst_info))
            if timeout_callback:
                timeout_callback()
            break
        elif stop_check:
            stop_check_time += 1
            if stop_check_time == stop_check_len:
                if stop_check():
                    break
                stop_check_time = 0
