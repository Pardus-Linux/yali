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
import parted

from yali.exception import *


filesystems = {}

def registerFSType(f):
    filesystems[f.name()] = f

##
# abstract file system class
class FileSystem:

    _name = None
    _filesystems = []
    _implemented = False
    _fs_type = None  # parted fs type

    def __init__(self):
        self.readSupportedFilesystems()

        self._fs_type = parted.file_system_type_get(self._name)


    ##
    # get file system name
    def name(self):
        return self._name

    ##
    # get parted filesystem type.
    def getFSType(self):
        return self._fs_type

    ##
    # check the supported file systems by kernel
    def readSupportedFilesystems(self):
        f = open("/proc/filesystems", 'r')
        for line in f.readlines():
            line = line.split()
            if line[0] == "nodev":
                self._filesystems.append(line[1])
            else:
                self._filesystems.append(line[0])

    ##
    # chek if file system is supported by kernel
    def isSupported(self):
        if self.name() in self._filesystems:
            return True
        return False

    ##
    # necessary checks before formatting
    def preFormat(self):
        e = ""
        if not self.isSupported():
            e = "%s file system is not supported by kernel." %(self.name())

        if not self.isImplemented():
            e = "%s file system is not fully implemented." %(self.name())
        
        if e:
            raise YaliException, e

    ##
    # empty funtion for implementors.
    def format(self, partition):
        pass

    ##
    # set if file system is implemented
    def setImplemented(self, bool):
        self._implemented = bool

    ##
    # check if filesystem is implemented
    def isImplemented(self):
        return self._implemented


##
# ext3 file system
class Ext3FileSystem(FileSystem):

    _name = "ext3"
    
    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

    def format(self, partition):
        self.preFormat()

        cmd = "/sbin/mke2fs.ext3 %s" %(partition.getPath())

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "ext3 format failed: %s" % partition.getPath()

registerFSType(Ext3FileSystem())


##
# linux-swap
class SwapFileSystem(FileSystem):

    _name = "linux-swap"

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

    def format(self, partition):
        self.preFormat()

        cmd = "/sbin/mkswap %s" %(partition.getPath())

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "swap format failed: %s" % partition.getPath()

registerFSType(SwapFileSystem())
