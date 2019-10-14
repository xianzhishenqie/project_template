# 运行: python compile.py build_ext --build-lib build/sv
# cython打包注意
#   1: 【兼容】__file__, __package__ 不可调用
#   2: 【逻辑】__init__.py 不会被编译, 尽量不包含逻辑
#   3: 【逻辑】代码中手动检测py模块的地方，同时要检测同名so模块
#   4: 【逻辑】在需要编译的包下存在不需要编译的包，要指出汇报（默认递归编译包内所有包）

import os
import shutil
import sys
import filecmp
from distutils.core import setup
from Cython.Build import cythonize
from Cython.Compiler import Options
from Cython.Distutils.extension import Extension
from Cython.Distutils import build_ext
from sv.settings import BASE_DIR


def _get_feature(name):
    import __future__
    return getattr(__future__, name, object())


def patch():
    from Cython.Compiler import Future
    Future.annotations = _get_feature("annotations")


patch()


Options.docstrings = False

setup_apps = []

project_name = os.path.split(BASE_DIR)[1]

dest_dir = os.path.join(BASE_DIR, f'build/{project_name}')

# 需要编译的目录:
#   ('sv_base', {
#       'is_dir': True,
#       'keep_dirs': (),
#       'keep_files': (),
#   }),
# 需要编译的文件:
#   ('sv_base/models.py', {}),
compile_configs = [
    ('sv_base', {
        'is_dir': True,
        'keep_dirs': (),
        'keep_files': (),
    }),
]

# 需要复制的文件列表
copy_file_list = []
# 需要编译的模块列表
ext_modules_list = []


def parse_ext_modules(dir_path, keep_dirs=None, keep_files=None):
    package_file = os.path.join(dir_path, '__init__.py')
    is_package = os.path.exists(package_file)
    is_migration_dir = dir_path.endswith('/migrations')
    package_compile_check = is_package and not is_migration_dir

    file_list = os.listdir(dir_path)
    for filename in file_list:
        if filename == '__pycache__':
            continue

        if is_migration_dir and not filename == '__init__.py':
            continue

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
        dst_file_path = os.path.join(dest_dir, relative_path)
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

execute_copy_files()

ext_modules = [
    Extension(ext_modules_item[0], ext_modules_item[1]) for ext_modules_item in ext_modules_list
]

setup(
    name=project_name,
    cmdclass={'build_ext': build_ext},
    ext_modules=cythonize(ext_modules, language_level='3', build_dir=f'build/{project_name}-build')
)


def copy_dir(src_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    file_list = os.listdir(src_dir)
    for filename in file_list:
        src_file_path = os.path.join(src_dir, filename)
        dest_file_path = os.path.join(dest_dir, filename)
        if os.path.isdir(src_file_path):
            copy_dir(src_file_path, dest_file_path)
        else:
            shutil.copy(src_file_path, dest_file_path)


for setup_app in setup_apps:
    setup_str = f'''
from setuptools import setup, find_packages

setup(
    name='{setup_app}',
    version='1.0',
    python_requires=">=3.7",
    install_requires=[
        # sv_base
        # 'django==2.2',
        # 'djangorestframework==3.9.2',
        # 'djangorestframework-xml==1.4.0',
        # 'django-redis==4.10.0',
        # 'mysqlclient==1.4.2.post1',
        # 'channels==2.2.0',
        # 'channels-redis==2.4.0',
        # 'Twisted[tls,http2]==19.2.0',
        # 'Pillow==6.0.0',
        # 'requests==2.21.0',
        # 'paramiko==2.4.2',
        # 'qrcode==6.1',
        # 'qrtools==0.0.2',
        # 'lxml==4.3.3',
        # 'pyminizip==0.2.4',

        # sv_cloud
        # 'python-openstackclient==3.14.1',
        # 'python-keystoneclient==3.15.0',
        # 'python-cinderclient==3.5.0',
        # 'python-ceilometerclient==2.9.0',
        # 'python-glanceclient==2.10.0 # modify',
        # 'python-novaclient==9.1.1 # modify',
        # 'python-neutronclient==6.7.0 # modify',
        # 'python-zunclient==1.1.0 # modify',
        # 'docker==3.7.2',

        # sv_scene
    ],
    packages=find_packages(),
    include_package_data=True,
    platforms=["all"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries'
    ],
)
'''
    manifest_in_str = '''
global-include *.so *.po *.mo
'''
    src_setup_app_path = os.path.join(dest_dir, setup_app)
    setup_path = os.path.join(dest_dir, 'setup')
    if not os.path.exists(setup_path):
        os.mkdir(setup_path)

    setup_app_path = os.path.join(setup_path, setup_app)
    copy_dir(src_setup_app_path, setup_app_path)
    setup_file_path = os.path.join(setup_path, 'setup.py')
    with open(setup_file_path, 'w') as f:
        f.write(setup_str)
    manifest_in_path = os.path.join(setup_path, 'MANIFEST.in')
    with open(manifest_in_path, 'w') as f:
        f.write(manifest_in_str)

    os.chdir(setup_path)
    os.system('{} {} bdist_wheel --universal'.format(sys.executable, setup_file_path))

    setup_app_egg_info_path = os.path.join(setup_path, f'{setup_app}.egg-info')
    setup_app_build_path = os.path.join(setup_path, 'build')
    shutil.rmtree(setup_app_build_path)
    shutil.rmtree(setup_app_egg_info_path)
    os.remove(setup_file_path)
    os.remove(manifest_in_path)
    shutil.rmtree(setup_app_path)
