import subprocess


def exe_cmd(cmd, shell=True, raise_exception=False):
    p = subprocess.Popen(cmd, shell=shell, close_fds=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0 and raise_exception:
        raise Exception(err)

    return p.returncode, out, err
