# -*- coding: utf-8 -*-
import hashlib
import os
import re
import uuid

from django.conf import settings
from django.utils import six
from django.utils.encoding import force_text


def ec(t):
    return t.encode(settings.ENCODING)


def dc(t):
    return t.decode(settings.ENCODING)


def md5(t):
    return hashlib.md5(ec(t)).hexdigest()


def sha1(t):
    return hashlib.sha1(ec(t)).hexdigest()


def rk():
    return md5(str(uuid.uuid4()))


def rk_filename(filename):
    return '{}{}'.format(rk(), os.path.splitext(filename)[-1])


zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')

def contain_zh(word):
    word = word.decode()
    global zh_pattern
    match = zh_pattern.search(word)

    return match


class Txt(six.text_type):
    pass


class Trans(Txt):

    source = set()

    code = None

    p = None

    def __new__(cls, s, code=None):
        txt = force_text(s)
        self = super(Trans, cls).__new__(cls, txt)
        self.txt = txt
        self.code = code
        cls.source.add(self)
        return self

    def __call__(self, **kwargs):
        self.p = kwargs
        return self

    def __eq__(self, other):
        r = super(Trans, self).__eq__(other)
        try:
            return r and self.code == other.code
        except AttributeError:
            return r

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self, *args, **kwargs):
        return hash(self.txt)

    def __repr__(self):
        return ec('Trans(string=%r, params=%r code=%r)' % (
            six.text_type(self),
            self.p,
            self.code,
        ))


trans = Trans
