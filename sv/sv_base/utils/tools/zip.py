import os
import shutil
from io import BytesIO
import uuid
import zipfile


class Ziper(object):
    def __init__(self, raw_file_content=None):
        # Create the in-memory file-like object
        self.in_memory_zip = BytesIO()
        if raw_file_content:
            self.in_memory_zip.write(raw_file_content)

    def add(self, filename_in_zip, file_contents):
        """Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip."""
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)
        # 压缩包存在文件覆盖掉
        if filename_in_zip in zf.namelist():
            # 建立存放文件的临时文件夹
            tmp_zip_path_name = uuid.uuid4()
            tmp_zip_path = '/tmp/%s' % tmp_zip_path_name
            os.makedirs(tmp_zip_path)
            new_zip_path = None
            try:
                # 解压到临时文件夹
                for item in zf.namelist():
                    if not item == filename_in_zip:
                        zf.extract(item, tmp_zip_path)

                # 覆盖的解压文件夹中存在的该文件
                with open(os.path.join(tmp_zip_path, filename_in_zip), 'w') as adding_file:
                    adding_file.write(file_contents)

                # 构造新的压缩包文件
                new_zip_path = tmp_zip_path + '.zip'
                new_zip_file = zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED)
                # 压缩解压文件夹内容
                pre_len = len(tmp_zip_path)
                for dirpath, dirnames, filenames in os.walk(tmp_zip_path):
                    for filename in filenames:
                        pathfile = os.path.join(dirpath, filename)
                        arcname = pathfile[pre_len:].strip(os.path.sep)
                        new_zip_file.write(pathfile, arcname)
                new_zip_file.close()
                # 新的压缩文件读到内存中
                with open(new_zip_path, 'rb') as nzf:
                    self.in_memory_zip = BytesIO()
                    self.in_memory_zip.write(nzf.read())
            except Exception as e:
                raise e
            finally:
                # 删除临时文件夹和新的压缩文件
                shutil.rmtree(tmp_zip_path)
                if new_zip_path:
                    os.remove(new_zip_path)
        else:
            zf.writestr(filename_in_zip, file_contents)
            # Mark the files as having been created on Windows so that
            # Unix permissions are not inferred as 0000
            for zfile in zf.filelist:
                zfile.create_system = 0
        return self

    def read(self):
        """Returns a string with the contents of the in-memory zip."""
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def write_to_file(self, filename):
        """Writes the in-memory zip to a file."""
        with open(filename, "wb") as f:
            f.write(self.read())

    def read_file(self, filename):
        zf = zipfile.ZipFile(self.in_memory_zip, "r")
        return zf.open(filename)


class ZFile(object):
    def __init__(self, filename, mode='r', basedir=''):
        self.filename = filename
        self.mode = mode
        if self.mode in ('w', 'a'):
            self.zfile = zipfile.ZipFile(filename, self.mode, compression=zipfile.ZIP_DEFLATED)
        else:
            self.zfile = zipfile.ZipFile(filename, self.mode)
        self.basedir = basedir
        if not self.basedir:
            self.basedir = os.path.dirname(filename)

    def addfile(self, path, arcname=None):
        path = path.replace('//', '/')
        if not arcname:
            if path.startswith(self.basedir):
                arcname = path[len(self.basedir):]
            else:
                arcname = ''
        self.zfile.write(path, arcname)

    def addfiles(self, paths):
        for path in paths:
            if isinstance(path, tuple):
                self.addfile(*path)
            else:
                self.addfile(path)

    def close(self):
        self.zfile.close()

    def extract_to(self, path):
        self.zfile.extractall(path)

    def extract(self, filename, path):
        if not filename.endswith('/'):
            f = os.path.join(path, filename)
            dir = os.path.dirname(f)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(f, 'wb') as fp:
                fp.write(self.zfile.read(filename))

    # 压缩文件夹
    def putin(self, dir):
        # 压缩解压文件夹内容
        pre_len = len(dir)
        for dirpath, dirnames, filenames in os.walk(dir):
            for filename in filenames:
                pathfile = os.path.join(dirpath, filename)
                arcname = pathfile[pre_len:].strip(os.path.sep)
                self.zfile.write(pathfile, arcname)

    def setpw(self, pw):
        self.zfile.setpassword(pw)
