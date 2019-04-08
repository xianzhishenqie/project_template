# 运行: python compile.py build_ext --build-lib build/sv
# cython打包注意
#   1: 【兼容】__file__, __package__ 不可调用
#   2: 【逻辑】__init__.py 不会被编译, 尽量不包含逻辑
#   3: 【逻辑】代码中手动检测py模块的地方，同时要检测同名so模块
#   4: 【逻辑】在需要编译的包下存在不需要编译的包，要指出汇报（默认递归编译包内所有包）

import os
import shutil
import filecmp
from distutils.core import setup
from Cython.Build import cythonize
from Cython.Compiler import Options
from Cython.Distutils.extension import Extension
from Cython.Distutils import build_ext

from sv.settings import BASE_DIR


Options.docstrings = False

# 需要编译的目录:
#   ('sv_base', {
#       'is_dir': True,
#       'keep_dirs': (),
#       'keep_files': (),
#   }),
# 需要编译的文件:
#   ('sv_base/models.py', {}),
compile_configs = [
    # ('sv_base', {
    #     'is_dir': True,
    #     'keep_dirs': (),
    #     'keep_files': (),
    # }),
    ('sv_base/models.py', {}),
]

# 需要复制的文件列表
copy_file_list = []
# 需要编译的模块列表
ext_modules_list = []


def parse_ext_modules(dir_path, keep_dirs=None, keep_files=None):
    package_file = os.path.join(dir_path, '__init__.py')
    is_package = os.path.exists(package_file)
    package_compile_check = is_package and not dir_path.endswith('migrations')

    file_list = os.listdir(dir_path)
    for filename in file_list:
        file_path = os.path.join(dir_path, filename)
        if os.path.isdir(file_path):
            relative_path = file_path.replace(BASE_DIR, '').lstrip('/')
            if keep_dirs and relative_path in keep_dirs:
                parse_original_path(file_path)
            else:
                parse_ext_modules(file_path, keep_dirs, keep_files)
        else:
            if file_path.endswith('.pyc'):
                continue

            relative_path = file_path.replace(BASE_DIR, '').lstrip('/')
            if (package_compile_check
                    and file_path.endswith('.py')
                    and (not keep_files or (keep_files and relative_path not in keep_files))):
                if file_path == package_file:
                    copy_file_list.append(file_path)
                else:
                    module_parts = relative_path[0: -3].split('/')
                    ext_modules_list.append(('.'.join(module_parts), [relative_path]))
            else:
                copy_file_list.append(file_path)


def parse_original_path(dir_path):
    file_list = os.listdir(dir_path)
    for filename in file_list:
        file_path = os.path.join(dir_path, filename)
        if os.path.isdir(file_path):
            parse_original_path(file_path)
        else:
            if file_path.endswith('.pyc'):
                continue

            copy_file_list.append(file_path)


def execute_copy_files():
    for src_file_path in copy_file_list:
        relative_path = src_file_path.replace(BASE_DIR, '').lstrip('/')
        dst_file_path = os.path.join(BASE_DIR, 'build/sv', relative_path)
        dir_dst_path = os.path.dirname(dst_file_path)
        if not os.path.exists(dir_dst_path):
            os.makedirs(dir_dst_path)

        if os.path.exists(dst_file_path) and filecmp.cmp(src_file_path, dst_file_path):
            continue

        print('copy file: %s to %s' % (src_file_path, dst_file_path))
        try:
            shutil.copyfile(src_file_path, dst_file_path)
        except Exception as e:
            print('copy file [%s] to [%s] error: %s' % (src_file_path, dst_file_path, e))


for name, config in compile_configs:
    is_dir = config.get('is_dir', False)
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        raise Exception('path[%s] not exist' % path)

    if is_dir:
        keep_dirs = config.get('keep_dirs', ())
        keep_files = config.get('keep_files', ())
        parse_ext_modules(path, keep_dirs, keep_files)
    else:
        if path.endswith('.py'):
            module_parts = name[0: -3].split('/')
            ext_modules_list.append(('.'.join(module_parts), [name]))
        else:
            copy_file_list.append(path)


for item in copy_file_list:
    print('prepare copy file: %s' % item)

for item in ext_modules_list:
    print('prepare compile module: %s' % item[0])

# execute_copy_files()

ext_modules = [
    Extension(ext_modules_item[0], ext_modules_item[1]) for ext_modules_item in ext_modules_list
]

setup(
    name='sv',
    cmdclass={'build_ext': build_ext},
    language_level=3,
    ext_modules=cythonize(ext_modules, build_dir='build/sv-build')
)
