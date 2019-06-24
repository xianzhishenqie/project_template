import logging
import socket
import subprocess
import time
import random
import re


logger = logging.getLogger(__name__)


def cport(ip, port, timeout=2):
    """检查端口是否连通

    :param ip: ip地址
    :param port: 进程端口
    :param timeout: 超时时间
    :return: 是否连通
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
        sk.settimeout(timeout)
        try:
            sk.connect((ip, port))
        except Exception:
            result = False
        else:
            result = True
    return result


def ping(ip, timeout=2, count=2):
    """检查ip是否ping通

    :param ip: ip地址
    :param timeout: 超时时间
    :param count: 尝试次数
    :return: 是否ping通
    """
    try:
        res = subprocess.check_output('ping -c %s -w %s %s' % (count, timeout, ip), shell=True)
    except Exception:
        return False
    if res.find('icmp_'):
        return True
    else:
        return False


def get_ping(ip):
    """获取ip延迟时间

    :param ip: ip地址
    :return: 延迟时间 ms
    """
    try:
        p = subprocess.getoutput("ping -c 1 {}".format(ip))
        pattern = re.compile(r"rtt min/avg/max/mdev = .*/(.*?)/.*/0.000 ms")
        delay = int(float(pattern.findall(p)[0]))
    except Exception:
        delay = 0
    return delay


def probe(ip,
          port=None,
          timeout=2,
          step_time=2,
          limit_time=300,
          stop_check_len=5,
          stop_check=None,
          callback=None,
          timeout_callback=None,
          log_prefix='probe'):
    """探测地址连通状况

    :param ip: ip地址
    :param port: 进程端口
    :param timeout: 超时时间
    :param step_time: 探测间隔时间
    :param limit_time: 总超时时间
    :param stop_check_len: 停止检查间隔次数
    :param stop_check: 停止检查
    :param callback: 连通回调
    :param timeout_callback: 超时回调
    :param log_prefix: 日志前缀
    """
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


def get_idle_port(ip='0.0.0.0',
                  start_port=10000,
                  end_port=60000,
                  max_attempt_time=10):
    """获取空闲端口

    :param ip: ip地址
    :param start_port: 端口范围最小值
    :param end_port: 端口范围最大值
    :param max_attempt_time: 最大尝试次数
    :return:
    """
    port = random.randint(start_port, end_port)

    attempt_time = 0
    while cport(ip, port):
        attempt_time = attempt_time + 1
        if attempt_time >= max_attempt_time:
            return None
        port = random.randint(start_port, end_port)

    return port
