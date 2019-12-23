import os

from django.utils import six
from django.http.response import FileResponse

from sv_base.utils.base.text import ec


def tmp_file_iter(file_path, block_size=4096):
    with open(file_path, 'rb') as f:
        while True:
            c = f.read(block_size)
            if c:
                yield c
            else:
                f.close()
                os.remove(file_path)
                break


class TemporaryFileResponse(FileResponse):
    """
        临时文件返回，文件下载完毕会被立马删除
        请勿传重要文件
    """

    def _set_streaming_content(self, value):
        if isinstance(value, six.string_types) and os.path.exists(value):
            self['Content-Length'] = os.path.getsize(value)
            self['Content-Type'] = 'application/octet-stream'
            self['Content-Disposition'] = 'attachment;filename="%s"' % os.path.basename(ec(value))
            value = tmp_file_iter(value, self.block_size)

        super(TemporaryFileResponse, self)._set_streaming_content(value)
