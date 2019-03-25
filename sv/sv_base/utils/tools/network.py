import logging
import socket
import subprocess
import time
import re

from typing import Callable, Optional


logger = logging.getLogger(__name__)


def cport(ip: str, port: int, timeout: int = 2) -> bool:
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


def ping(ip: str, timeout: int = 2, count: int = 2) -> bool:
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


def get_ping(ip: str) -> int:
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


def probe(ip: str,
          port: Optional[int] = None,
          timeout: int = 2,
          step_time: int = 2,
          limit_time: int = 300,
          stop_check_len: int = 5,
          stop_check: Optional[Callable] = None,
          callback: Optional[Callable] = None,
          timeout_callback: Optional[Callable] = None,
          log_prefix: str = 'probe') -> None:
    """探测地址连通状况

    :param ip: ip地址
    :param port: 进程端口
    :param timeout: 超时时间
    :param step_time: 探测间隔时间
    :param limit_time:
    :param stop_check_len:
    :param stop_check:
    :param callback:
    :param timeout_callback:
    :param log_prefix:
    :return:
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
