import os


def list_dir(path, deep=False):
    """目录包含子目录和文件信息

    :param path: 目录路径
    :param deep: 是否向下获取多级目录
    :return: 目录信息
    """
    file_list = os.listdir(path)
    data = []
    for filename in file_list:
        file_path = os.path.join(path, filename)
        file_info = {
            'name': filename,
            'suffix': get_file_suffix(filename),
            'isdir': os.path.isdir(file_path),
            'isfile': os.path.isfile(file_path),
            'islink': os.path.islink(file_path),
            'size': os.path.getsize(file_path),
            'time': os.path.getmtime(file_path),
        }

        if not file_info['isdir']:
            file_info['suffix'] = get_file_suffix(filename)
        else:
            file_info['suffix'] = ''

        if deep and file_info['isdir']:
            file_info['children'] = list_dir(file_path, deep)

        data.append(file_info)
    data.sort(key=lambda f: (not f['isdir'], f['suffix'], f['name']))
    return data


def list_files(path, deep=False):
    """目录包含的文件列表

    :param path: 目录路径
    :param deep: 是否向下获取多级目录
    :return: 包含的文件列表
    """
    file_list = os.listdir(path)
    files = []
    for filename in file_list:
        file_path = os.path.join(path, filename)
        if os.path.isdir(file_path):
            if deep:
                files.extend(list_files(file_path, deep=deep))
        else:
            files.append(file_path)
    return files


def get_file_suffix(name):
    """获取文件后缀名

    :param name: 文件名
    :return: 文件后缀名
    """
    return os.path.splitext(name)[-1].replace('.', '')
