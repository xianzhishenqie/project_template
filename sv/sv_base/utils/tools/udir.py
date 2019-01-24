import os


def list_dir(path, deep=False):
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


def get_file_suffix(name):
    return os.path.splitext(name)[-1].replace('.', '')