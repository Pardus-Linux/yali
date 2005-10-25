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

# filesystem.py defines file systems used in YALI. Individual classes
# also define actions, like format...

import os

from yali.exception import *


filesystems = []

##
# abstract file system class
class FileSystem:

    _filesystems = []

    def __init__(self):
        self.name = None

        self.readSupportedFilesystems()

    def readSupportedFilesystems(self):
        f = open("/proc/filesystems", 'r')
        for line in f.readline():
            line = line.split()
            if line[0] == "nodev":
                self._filesystems.append(line[1])
            else:
                self._filesystems.append(line[0])

    def format(self, device, partition):
        raise YaliError, "format() is not implemented!"



##
# ext3 file system
class Ext3FileSystem(FileSystem):
    
    _name = "ext3"

    def __init__(self):
        super(Ext3FileSystem, self).__init__(self)
        self.name = self._name
        

    def format(self, partition):
        device_path = partition.get_device_name() + partition.get_minor()

        cmd = "/sbin/mke2fs.ext3 %s" %(device_path)

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "ext3 format failed: %s" % device_path

filesystems.append(Ext3FileSystem())

##
# linux-swap
class SwapFileSystem(FileSystem):

    _name = "swap"

    def __init__(self):
        super(SwapFileSystem, self).__init__(self)
        self.name = self._name
        

    def format(self, partition):
        device_path = partition.get_device_name() + partition.get_minor()

        cmd = "/sbin/mkswap %s" %(device_path)

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "swap format failed: %s" % device_path

filesystems.append(SwapFileSystem())
