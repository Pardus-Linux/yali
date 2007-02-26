# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 - 2007 TUBITAK/UEKAE
# Copyright 2001 - 2004 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# As of 26/02/2007, getLabel methods are (mostly) lifted from Anaconda.

# filesystem.py defines file systems used in YALI. Individual classes
# also define actions, like format...


import os
import resource
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
    elif name == "xfs":
        return XFSFileSystem()

    return None

##
# abstract file system class
class FileSystem:

    _name = None
    _filesystems = []
    _implemented = False
    _resizeable = False
    _mountoptions = "defaults"
    _fs_type = None  # parted fs type

    def __init__(self):
        self.readSupportedFilesystems()

        self._fs_type = parted.file_system_type_get(self._name)

    ##
    # Open partition
    def openPartiton(self, partition):
        try:
            fd = os.open(partition.getPath(), os.O_RDONLY)
            return fd
        except:
            e = "error opening partition %s: %s" % (partition.getPath(), e)
            raise YaliException, e

    ##
    # get file system name
    def name(self):
        return self._name

    ##
    # get default mount options for file system
    def mountOptions(self):
        return self._mountoptions

    ##
    # get parted filesystem type.
    def getFSType(self):
        return self._fs_type

    ##
    # read filesystem label and return
    def getLabel(self, partition):
        return None

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
    _mountoptions = "defaults,user_xattr"
    
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

        # Use hashed b-trees to speed up lookups in large directories
        cmd = "%s -O dir_index -j %s" %(cmd_path, partition.getPath())

        p = os.popen(cmd)
        o = p.readlines()
        if p.close():
            raise YaliException, "ext3 format failed: %s" % partition.getPath()

    def minResizeMB(self, partition):
        cmd_path = sysutils.find_executable("dumpe2fs")

        if not cmd_path:
            e = "Command not found to get information about %s" %(partition)
            raise FSError, e 

        lines = os.popen("%s -h %s" % (cmd_path, partition.getPath())).readlines()

        total_blocks = long(filter(lambda line: line.startswith('Block count'), lines)[0].split(':')[1].strip('\n').strip(' '))
        free_blocks  = long(filter(lambda line: line.startswith('Free blocks'), lines)[0].split(':')[1].strip('\n').strip(' '))
        block_size   = long(filter(lambda line: line.startswith('Block size'), lines)[0].split(':')[1].strip('\n').strip(' '))

        return (((total_blocks - free_blocks) * block_size) / parteddata.MEGABYTE) + 150

    def resize(self, size_mb, partition):
        if size_mb < self.minResizeMB(partition):
            return False

        cmd_path = sysutils.find_executable("resize2fs")

        if not cmd_path:
            e = "Command not found to format %s filesystem" %(self.name())
            raise FSError, e 
        
        cmd = "%s %s %sM" % (cmd_path, partition.getPath(), str(size_mb)) 
        
        try:
            p = os.popen(cmd)
            p.close()
        except:
            return False

        return True
       
    def getLabel(self, partition):
        return sysutils.e2fslabel(partition.getPath())

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


    def getLabel(self, partition):
        label = None
        fd = self.openPartiton(partiton)

        # valid block sizes in reiserfs are 512 - 8192, powers of 2
        # we put 4096 first, since it's the default
        # reiserfs superblock occupies either the 2nd or 16th block
        for blksize in (4096, 512, 1024, 2048, 8192):
            for start in (blksize, (blksize*16)):
                try:
                    os.lseek(fd, start, 0)
                    # read 120 bytes to get s_magic and s_label
                    buf = os.read(fd, 120)

                    # see if this block is the superblock
                    # this reads reiserfs_super_block_v1.s_magic as defined
                    # in include/reiserfs_fs.h in the reiserfsprogs source
                    m = string.rstrip(buf[52:61], "\0x00")
                    if m == "ReIsErFs" or m == "ReIsEr2Fs" or m == "ReIsEr3Fs":
                        # this reads reiserfs_super_block.s_label as
                        # defined in include/reiserfs_fs.h
                        label = string.rstrip(buf[100:116], "\0x00")
                        os.close(fd)
                        return label
                except OSError, e:
                    # [Error 22] probably means we're trying to read an
                    # extended partition. 
                    e = "error reading reiserfs label on %s: %s" %(partition.getPath(), e)
                    raise YaliException, e

        os.close(fd)
        return label


##
# xfs
class XFSFileSystem(FileSystem):

    _name = "xfs"
    
    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

    def format(self, partition):
        self.preFormat(partition)

        cmd_path = sysutils.find_executable("mkfs.xfs")
        
        if not cmd_path:
            e = "Command not found to format %s filesystem" %(self.name())
            raise FSError, e

        cmd = "%s -f %s" %(cmd_path, partition.getPath())

        p = os.popen(cmd)
        if p.close():
            raise YaliException, "%s format failed: %s" % (self.name(), partition.getPath())

    def getLabel(self, partition):
        label = None
        fd = self.openPartiton(partition)
        try:
            buf = os.read(fd, 128)
            os.close(fd)
        except OSError, e:
            e = "error reading xfs label on %s: %s" %(partition.getPath(), e)
            raise YaliException, e

        if len(buf) == 128 and buf[0:4] == "XFSB":
            label = string.rstrip(buf[108:120],"\0x00")

        return label


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


    def getLabel(self, partition):
        label = None
        fd = self.openPartiton(partition)
        
        pagesize = resource.getpagesize()
        try:
            buf = os.read(fd, pagesize)
            os.close(fd)
        except OSError, e:
            e = "error reading swap label on %s: %s" %(partition.getPath(), e)
            raise YaliException, e

        if ((len(buf) == pagesize) and (buf[pagesize - 10:] == "SWAPSPACE2")):
            label = string.rstrip(buf[1052:1068], "\0x00")
        return label


##
# ntfs
class NTFSFileSystem(FileSystem):

    _name = "ntfs"

    def __init__(self):
        FileSystem.__init__(self)

        self.setResizeable(True)

    def check_resize(self, size_mb, partition):
        #don't do anything, just check
        cmd = "/usr/sbin/ntfsresize -n -f -s %dM %s" %(size_mb, partition.getPath())

        p = os.popen(cmd)
        if p.close():
            return False
        return True


    def resize(self, size_mb, partition):

        if size_mb < self.minResizeMB(partition):
            return False

        cmd = "/usr/sbin/ntfsresize -f -s %dM %s" %(size_mb, partition.getPath())

        try:
            p = os.popen(cmd, "w")
            p.write("y\n")
            p.close()
        except:
            return False

        return True


    def minResizeMB(self, partition):

        cmd = "/usr/sbin/ntfsresize -f -i %s" % partition.getPath()
        lines = os.popen(cmd).readlines()
        
        MB = parteddata.MEGABYTE
        _min = 0
        for l in lines:
            if l.startswith("You might resize"):
                _min = int(l.split()[4]) / MB + 140

        return _min
