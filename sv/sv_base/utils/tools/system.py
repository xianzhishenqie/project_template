import re

import psutil


def get_pid(name):
    """获取进程pid

    :param name: 进程名称
    :return: pid
    """
    procs = list(psutil.process_iter())
    regex = r"pid=(\d+),\sname=\'" + name + r"\'"

    for line in procs:
        process_info = str(line)
        ini_regex = re.compile(regex)
        result = ini_regex.search(process_info)
        if result is not None:
            pid = int(result.group(1))
            return pid
