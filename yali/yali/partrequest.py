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

class FormatRequest:
    
    def __init__(self, partition, filesystem):
        self._part = partition
        self._fs = filesystem

    def apply_request(self):
        fsobj = get_fs_obj(self._fs)
        fs.format(self._part)
