"""
zipfile补丁

"""
from zipfile import (ZipFile, ZipInfo, _SharedFile, sizeFileHeader, BadZipFile, structFileHeader, _FH_SIGNATURE,
                     stringFileHeader, _FH_FILENAME_LENGTH, _FH_EXTRA_FIELD_LENGTH, _ZipDecrypter, ZipExtFile)

import struct


def _zipfile_open(self, name, mode="r", pwd=None, *, force_zip64=False):
    """Return file-like object for 'name'.

    name is a string for the file name within the ZIP file, or a ZipInfo
    object.

    mode should be 'r' to read a file already in the ZIP file, or 'w' to
    write to a file newly added to the archive.

    pwd is the password to decrypt files (only used for reading).

    When writing, if the file size is not known in advance but may exceed
    2 GiB, pass force_zip64 to use the ZIP64 format, which can handle large
    files.  If the size is known in advance, it is best to pass a ZipInfo
    instance for name, with zinfo.file_size set.
    """
    if mode not in {"r", "w"}:
        raise ValueError('open() requires mode "r" or "w"')
    if pwd and not isinstance(pwd, bytes):
        raise TypeError("pwd: expected bytes, got %s" % type(pwd).__name__)
    if pwd and (mode == "w"):
        raise ValueError("pwd is only supported for reading files")
    if not self.fp:
        raise ValueError(
            "Attempt to use ZIP archive that was already closed")

    # Make sure we have an info object
    if isinstance(name, ZipInfo):
        # 'name' is already an info object
        zinfo = name
    elif mode == 'w':
        zinfo = ZipInfo(name)
        zinfo.compress_type = self.compression
        zinfo._compresslevel = self.compresslevel
    else:
        # Get info object for name
        zinfo = self.getinfo(name)

    if mode == 'w':
        return self._open_to_write(zinfo, force_zip64=force_zip64)

    if self._writing:
        raise ValueError("Can't read from the ZIP file while there "
                         "is an open writing handle on it. "
                         "Close the writing handle before trying to read.")

    # Open for reading:
    self._fileRefCnt += 1
    zef_file = _SharedFile(self.fp, zinfo.header_offset,
                           self._fpclose, self._lock, lambda: self._writing)
    try:
        # Skip the file header:
        fheader = zef_file.read(sizeFileHeader)
        if len(fheader) != sizeFileHeader:
            raise BadZipFile("Truncated file header")
        fheader = struct.unpack(structFileHeader, fheader)
        if fheader[_FH_SIGNATURE] != stringFileHeader:
            raise BadZipFile("Bad magic number for file header")

        fname = zef_file.read(fheader[_FH_FILENAME_LENGTH])
        if fheader[_FH_EXTRA_FIELD_LENGTH]:
            zef_file.read(fheader[_FH_EXTRA_FIELD_LENGTH])

        if zinfo.flag_bits & 0x20:
            # Zip 2.7: compressed patched data
            raise NotImplementedError("compressed patched data (flag bit 5)")

        if zinfo.flag_bits & 0x40:
            # strong encryption
            raise NotImplementedError("strong encryption (flag bit 6)")

        if zinfo.flag_bits & 0x800:
            # UTF-8 filename
            try:
                fname_str = fname.decode("utf-8")
            except UnicodeDecodeError:
                fname_str = fname.decode("cp437")
        else:
            fname_str = fname.decode("cp437")

        if fname_str != zinfo.orig_filename:
            raise BadZipFile(
                'File name in directory %r and header %r differ.'
                % (zinfo.orig_filename, fname))

        # check for encrypted flag & handle password
        is_encrypted = zinfo.flag_bits & 0x1
        zd = None
        if is_encrypted:
            if not pwd:
                pwd = self.pwd
            if not pwd:
                raise RuntimeError("File %r is encrypted, password "
                                   "required for extraction" % name)

            zd = _ZipDecrypter(pwd)
            # The first 12 bytes in the cypher stream is an encryption header
            #  used to strengthen the algorithm. The first 11 bytes are
            #  completely random, while the 12th contains the MSB of the CRC,
            #  or the MSB of the file time depending on the header type
            #  and is used to check the correctness of the password.
            header = zef_file.read(12)
            h = zd(header[0:12])
            if zinfo.flag_bits & 0x8:
                # compare against the file type from extended local headers
                check_byte = (zinfo._raw_time >> 8) & 0xff
            else:
                # compare against the CRC otherwise
                check_byte = (zinfo.CRC >> 24) & 0xff
            if h[11] != check_byte:
                raise RuntimeError("Bad password for file %r" % name)

        return ZipExtFile(zef_file, mode, zinfo, zd, True)
    except:
        zef_file.close()
        raise


def monkey_patch():
    """打补丁

    """
    ZipFile.open = _zipfile_open
