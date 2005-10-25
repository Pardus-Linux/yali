# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# partrequest.py defines requests (format, mount) on the partitions.

from yali.exception import *
from yali.filesystem import filesystems

def get_fs_obj(fs):
    for i in filesystems:
        if i.name == fs:
            return i

class PartRequest:
    _part = None

    def __init__(self, partition):
        self._part = partition

    def get_partition(self):
        return self._part

class FormatRequest(PartRequest):
    
    def __init__(self, partition, filesystem):
        PartRequest.__init__(self, partition)
        self._fs = filesystem

    def apply_request(self):
        fsobj = get_fs_obj(self._fs)
        fs.format(self._part)

    def get_fs(self):
        return self._fs

class MountRequest(PartRequest):
    def __init__(self, partition, filesystem, mountpoint, options=None):
        PartRequest.__init__(self, partition)
        self._fs = filesystem
        self._mp = mountpoint
        self._options = options

    def apply_request(self):
        raise YaliException, "Not Implemented yet!"

    def get_fs(self):
        return self._fs

    def get_mountpoint(self):
        return self._mp

