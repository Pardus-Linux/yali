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
import yali.sysutils as sysutils
import yali.parteddata as parteddata

class FSError(YaliError):
    pass



def get_filesystem(name):

    # Hardcoding available filesystems like this is TOO
    # dirty... should revisit this module (and others using this)
    # later on.
    if name == "ext3":
        return Ext3FileSystem()
    elif name == "swap" or name == "linux-swap":
        return SwapFileSystem()
    elif name == "ntfs":
        return NTFSFileSystem()
    elif name == "reiserfs":
        return ReiserFileSystem()

    return None

##
# abstract file system class
class FileSystem:

    _name = None
    _filesystems = []
    _implemented = False
    _resizeable = False
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

        # append swap manually
        self._filesystems.append("swap")
        

    ##
    # chek if file system is supported by kernel
    def isSupported(self):
        if self.name() in self._filesystems:
            return True
        return False

    ##
    # necessary checks before formatting
    def preFormat(self, partition):
        e = ""
        if not self.isSupported():
            e = "%s file system is not supported by kernel." %(self.name())

        if not self.isImplemented():
            e = "%s file system is not fully implemented." %(self.name())
        
        if e:
            raise YaliException, e

        #FIXME: use logging system
        print "format %s: %s" %(partition.getPath(), self.name())

    ##
    # set if file system is implemented
    def setImplemented(self, bool):
        self._implemented = bool

    ##
    # check if filesystem is implemented
    def isImplemented(self):
        return self._implemented


    ##
    # set if filesystem is resizeable
    def setResizeable(self, bool):
        self._resizeable = bool

    ##
    # check if filesystem is resizeable
    def isResizeable(self):
        return self._resizeable


##
# ext3 file system
class Ext3FileSystem(FileSystem):

    _name = "ext3"
    
    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)
        self.setResizeable(True)

    def format(self, partition):
        self.preFormat(partition)

        cmd_path = sysutils.find_executable("mke2fs")
        if not cmd_path:
            cmd_path = sysutils.find_executable("mkfs.ext3")

        
        if not cmd_path:
            e = "Command not found to format %s filesystem" %(self.name())
            raise FSError, e

        cmd = "%s -j %s" %(cmd_path, partition.getPath())

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "ext3 format failed: %s" % partition.getPath()

    def minResizeMB(self, partition):
        cmd_path = sysutils.find_executable("dumpe2fs")

        if not cmd_path:
            e = "Command not found to get information about %s" %(partition)
            raise FSError, e 

        lines = os.popen("%s -h %s" % (cmd_path, partition)).readlines()

        total_blocks = long(filter(lambda line: line.startswith('Block count'), lines)[0].split(':')[1].strip('\n').strip(' '))
        free_blocks  = long(filter(lambda line: line.startswith('Free blocks'), lines)[0].split(':')[1].strip('\n').strip(' '))
        block_size   = long(filter(lambda line: line.startswith('Block size'), lines)[0].split(':')[1].strip('\n').strip(' '))

        return (((total_blocks - free_blocks) * block_size) / parteddata.MEGABYTE) + 150

    def resize(self, size_mb, partition):
        if size_mb < minResizeMB(partition):
            return False

        cmd_path = sysutils.find_executable("resize2fs")

        if not cmd_path:
            e = "Command not found to format %s filesystem" %(self.name())
            raise FSError, e 
        
        cmd = "%s %s %sM" % (cmd_path, partition, str(size_mb)) 
        
        try:
            p = os.popen(cmd)
            p.close()
        except:
            return False

        return True
       

##
# reiserfs
class ReiserFileSystem(FileSystem):

    _name = "reiserfs"
    
    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

    def format(self, partition):
        self.preFormat(partition)

        cmd_path = sysutils.find_executable("mkreiserfs")
        
        if not cmd_path:
            e = "Command not found to format %s filesystem" %(self.name())
            raise FSError, e

        cmd = "%s  %s" %(cmd_path, partition.getPath())

        p = os.popen(cmd, "w")
        p.write("y\n")
        if p.close():
            raise YaliException, "reiserfs format failed: %s" % partition.getPath()


##
# linux-swap
class SwapFileSystem(FileSystem):

    _name = "linux-swap"

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

        # override name: system wants "swap" whereas parted needs
        # linux-swap
        self._name = "swap"

    def format(self, partition):
        self.preFormat(partition)

        cmd_path = sysutils.find_executable("mkswap")
        cmd = "%s %s" %(cmd_path, partition.getPath())

        if not cmd_path:
            e = "Command not found to format %s filesystem" %(self.name())
            raise FSError, e

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "swap format failed: %s" % partition.getPath()


##
# ntfs
class NTFSFileSystem(FileSystem):

    _name = "ntfs"

    def __init__(self):
        FileSystem.__init__(self)

        self.setResizeable(True)


    def resize(self, size_mb, partition):

        if size_mb < self.minResizeMB(partition):
            return False

        s = "/usr/sbin/ntfsresize -f -s %dM %s" %(size_mb,
                                                  partition.getPath())
        try:
            p = os.popen(s, "w")
            p.write("y\n")
            p.close()
        except:
            return False

        return True


    def minResizeMB(self, partition):

        s = "/usr/sbin/ntfsresize -f -i %s" % partition.getPath()
        lines = os.popen(s).readlines()
        
        MB = parteddata.MEGABYTE
        min = 0
        for l in lines:
            if l.startswith("You might resize"):
                min = int(l.split()[4]) / MB + 140

        return min
