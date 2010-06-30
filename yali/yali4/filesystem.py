# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009 TUBITAK/UEKAE
# Copyright 2001-2008 Red Hat, Inc.
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

# we need i18n
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import os
import resource
import string
import parted
import math

from yali.exception import *
import yali.sysutils as sysutils
import yali.parteddata as parteddata
import yali.storage

def getLabel(partition):
    if not os.path.exists("/dev/disk/by-label"):
        return None
    base = os.walk("/dev/disk/by-label/").next()
    path = partition.getPath()
    for part in base[2]:
        if os.path.realpath("%s%s" % (base[0],part)) == path:
            return part
    return None

def requires(command):
    cmd_path = sysutils.find_executable(command)
    if not cmd_path:
        raise FSError, "Command not found: %s " % command
    return cmd_path

class FileSystem:
    """ Abstract fileSystem class for other implementations """
    _name = None
    _sysname = None
    _filesystems = []
    _implemented = False
    _resizable = False
    _mountoptions = "defaults"
    _fs_type = None  # parted fs type
    _linux_supported = True
    _is_ready_to_use = True

    def __init__(self):
        self._fs_type = parted.file_system_type_get(self._name)

    def openPartition(self, partition):
        """ Checks if partition exists or not;
            If not,it causes YaliException """
        try:
            fd = os.open(partition.getPath(), os.O_RDONLY)
            return fd
        except OSError, e:
            err = "error opening partition %s: %s" % (partition.getPath(), e)
            raise YaliException, err

    def name(self):
        """ Get file system name """
        return self._name

    def mountOptions(self):
        """ Get default mount options for file system """
        return self._mountoptions

    def getFSType(self):
        """ Get parted file system type """
        return self._fs_type

    def getLabel(self, partition):
        """ Read file system label and return """
        cmd_path = requires("e2label")
        cmd = "%s %s" % (cmd_path, partition.getPath())
        label = sysutils.run(cmd, capture=True)
        if not label:
            return False
        return label.strip()

    def setLabel(self, partition, label):
        label = self.availableLabel(label)
        cmd_path = requires("e2label")
        cmd = "%s %s %s" % (cmd_path, partition.getPath(), label)
        if not sysutils.run(cmd):
            return False
        # Check label consistency
        if not self.getLabel(partition) == label:
            return False
        return label

    def labelExists(self, label):
        """ Check label for existence """
        if not yali.storage.devices:
            yali.storage.initDevices()

        for dev in yali.storage.devices:
            for part in dev.getPartitions():
                if label == part.getFSLabel():
                    return True
        return False

    def availableLabel(self, label):
        """ Check if label is available and try to find one if not """
        count = 1
        new_label = label
        while self.labelExists(new_label):
            new_label = "%s%d" % (label, count)
            count += 1
        return new_label

    def preFormat(self, partition):
        """ Necessary checks before formatting """
        if not self.isImplemented():
            raise YaliException, "%s file system is not fully implemented." % (self.name())

        import yali.gui.context as ctx
        ctx.debugger.log("Format %s: %s" %(partition.getPath(), self.name()))

    def setImplemented(self, bool):
        """ Set if file system is implemented """
        self._implemented = bool

    def isImplemented(self):
        """ Check if filesystem is implemented """
        return self._implemented

    def isReadyToUse(self):
        return self._is_ready_to_use

    def setResizable(self, bool):
        """ Set if filesystem is resizable """
        self._resizable = bool

    def isResizable(self):
        """ Check if filesystem is resizable """
        return self._resizable

    def preResize(self, partition):
        """ Routine operations before resizing """
        cmd_path = requires("e2fsck")

        res = sysutils.execClear(cmd_path,
                                ["-y", "-f", "-C", "0", partition.getPath()],
                                stdout="/tmp/resize.log",
                                stderr="/tmp/resize.log")

        if res == 2:
            raise FSCheckError, _("""FSCheck found some problems on partition %s and fixed them. \
                                     You should restart the machine before starting the installation process !""" % (partition.getPath()))
        elif res > 2:
            raise FSCheckError, _("FSCheck failed on %s" % (partition.getPath()))

        return True

    def format(self, partition):
        """ Format the given partition """
        self.preFormat(partition)

        cmd_path = requires("mkfs.%s" % self.name())

        # bug 5616: ~100MB reserved-blocks-percentage
        reserved_percentage = int(math.ceil(100.0 * 100.0 / partition.getMB()))

        # Use hashed b-trees to speed up lookups in large directories
        cmd = "%s -O dir_index -q -j -m %d %s" % (cmd_path,
                                                  reserved_percentage,
                                                  partition.getPath())

        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "%s format failed: %s" % (self.name(), partition.getPath())

        # for Disabling Lengthy Boot-Time Checks
        self.tune2fs(partition)

    def tune2fs(self, partition):
        """ Runs tune2fs for given partition """
        cmd_path = requires("tune2fs")
        # Disable mount count and use 6 month interval to fsck'ing disks at boot
        cmd = "%s -c 0 -i 6m %s" % (cmd_path, partition.getPath())
        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "tune2fs tuning failed: %s" % partition.getPath()

    def minResizeMB(self, partition):
        """ Get minimum resize size (mb) for given partition """
        cmd_path = requires("dumpe2fs")

        def capture(lines, param):
            return long(filter(lambda line: line.startswith(param), lines)[0].split(':')[1].strip('\n').strip(' '))

        lines = os.popen("%s -h %s" % (cmd_path, partition.getPath())).readlines()

        try:
            total_blocks = capture(lines, 'Block count')
            free_blocks  = capture(lines, 'Free blocks')
            block_size   = capture(lines, 'Block size')
            return (((total_blocks - free_blocks) * block_size) / parteddata.MEGABYTE) + 140
        except Exception:
            return 0

    def resize(self, size_mb, partition):
        """ Resize given partition as given size """
        minsize = self.minResizeMB(partition)
        if size_mb < minsize:
            size_mb = minsize
        cmd_path = requires("resize2fs")

        # Check before resize
        self.preResize(partition)

        res = sysutils.run("resize2fs",[partition.getPath(), "%sM" %(size_mb)])
        if not res:
            raise FSError, "Resize failed on %s" % (partition.getPath())
        return True

class Ext4FileSystem(FileSystem):
    """ Implementation of ext4 file system """

    _name = "ext4"
    _mountoptions = "defaults,user_xattr"

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)
        self.setResizable(True)

class Ext3FileSystem(FileSystem):
    """ Implementation of ext3 file system """

    _name = "ext3"
    _mountoptions = "defaults,user_xattr"

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)
        self.setResizable(True)

##
# reiserfs
class ReiserFileSystem(FileSystem):

    _name = "reiserfs"

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

    def format(self, partition):
        self.preFormat(partition)

        cmd_path = requires("mkreiserfs")
        cmd = "%s %s" % (cmd_path, partition.getPath())

        p = os.popen(cmd, "w")
        p.write("y\n")
        if p.close():
            raise YaliException, "reiserfs format failed: %s" % partition.getPath()

    def setLabel(self, partition, label):
        label = self.availableLabel(label)
        cmd_path = requires("reiserfstune")
        cmd = "%s --label %s %s" % (cmd_path, label, partition.getPath())
        if not sysutils.run(cmd):
            return False
        return label

    def getLabel(self, partition):
        getLabel(partition)

##
# xfs
class XFSFileSystem(FileSystem):

    _name = "xfs"

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

    def format(self, partition):
        self.preFormat(partition)
        cmd_path = requires("mkfs.xfs")
        cmd = "%s -f %s" %(cmd_path, partition.getPath())
        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "%s format failed: %s" % (self.name(), partition.getPath())

    def setLabel(self, partition, label):
        label = self.availableLabel(label)
        cmd_path = requires("xfs_admin")
        cmd = "%s -L %s %s" % (cmd_path, label, partition.getPath())
        if not sysutils.run(cmd):
            return False
        return label

    def getLabel(self, partition):
        getLabel(partition)

##
# btrfs
class BtrfsFileSystem(FileSystem):

    _name = "btrfs"
    _is_ready_to_use = yali.sysutils.checkYaliParams("wowbtrfs")

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)
        self.setResizable(True)

    def format(self, partition):
        self.preFormat(partition)
        cmd_path = requires("mkfs.btrfs")
        cmd = "%s %s" % (cmd_path, partition.getPath())
        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "%s format failed: %s" % (self.name(), partition.getPath())

    def minResizeMB(self, partition):
        cmd_path = requires("btrfs-show")
        cmd = "%s %s" % (cmd_path, partition.getPath())
        lines = os.popen(cmd).readlines()
        _min = 0
        _safety = 10
        for l in lines:
            if l.find("bytes used"):
                _size = l[-2:]
                _used = int(l[l.find("bytes used")+len("bytes used "):-5])
                if _size == 'KB':
                    return 1 + _safety
                elif _size == 'GB':
                    return int(_used * parteddata.MEGABYTE) + _safety
                elif _size == 'MB':
                    return _used + _safety
        return _safety

    def setLabel(self, partition, label):
        # FIXME It formats the device twice for setting label
        # Find a better way for it...
        label = self.availableLabel(label)
        cmd_path = requires("mkfs.btrfs")
        cmd = "%s -L %s %s" % (cmd_path, label, partition.getPath())
        if not sysutils.run(cmd):
            return False
        return label

    def getLabel(self, partition):
        getLabel(partition)

    def preResize(self, partition):
        """ Routine operations before resizing """
        cmd_path = requires("fsck.btrfs")
        cmd = "%s %s" % (cmd_path, partition.getPath())
        return sysutils.run(cmd)

    def resize(self, size_mb, partition):
        minsize = self.minResizeMB(partition)
        if size_mb < minsize:
            size_mb = minsize

        if not self.preResize(partition):
            raise FSCheckError, _("Partition is not ready for resizing. Check it before installation.")

        cmd_path = requires("btrfsctl")
        cmd = "%s -r %dm -A %s" % (cmd_path, size_mb, partition.getPath())
        if not sysutils.run(cmd):
            raise FSError, "Resize failed on %s " % (partition.getPath())

        return True

##
# linux-swap
class SwapFileSystem(FileSystem):

    _name = "linux-swap"
    _sysname = "swap"
    _linux_supported = False

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

        # override name: system wants "swap" whereas parted needs linux-swap
        self._name = "swap"

    def format(self, partition):
        self.preFormat(partition)
        cmd_path = requires("mkswap")
        cmd = "%s %s" %(cmd_path, partition.getPath())
        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "Swap format failed: %s" % partition.getPath()

    def getLabel(self, partition):
        label = None
        fd = self.openPartition(partition)

        pagesize = resource.getpagesize()
        try:
            buf = os.read(fd, pagesize)
            os.close(fd)
        except:
            return False

        if ((len(buf) == pagesize) and (buf[pagesize - 10:] == "SWAPSPACE2")):
            label = string.rstrip(buf[1052:1068], "\0x00")
        return label

    def setLabel(self, partition, label):
        label = self.availableLabel(label)
        cmd_path = requires("mkswap")
        cmd = "%s -v1 -L %s %s" % (cmd_path, label, partition.getPath())
        if not sysutils.run(cmd):
            return False

        # Swap on
        sysutils.swapOn(partition.getPath())

        return label

##
# ntfs
class NTFSFileSystem(FileSystem):

    _name = "ntfs"
    _sysname = "ntfs-3g"
    _mountoptions = "dmask=007,fmask=117,locale=tr_TR.UTF-8,gid=6"
    _linux_supported = False

    def __init__(self):
        FileSystem.__init__(self)
        self.setResizable(True)
        self.setImplemented(True)

    def resizeSilent(self, size_mb, partition):
        # don't do anything, just check
        cmd_path = requires("ntfsresize")
        cmd = "%s -P -n -ff -s %dM %s" % (cmd_path, size_mb, partition.getPath())
        return sysutils.run(cmd)

    def preResize(self, partition):
        """ Routine operations before resizing """
        cmd_path = requires("ntfsresize")
        cmd = "%s -P -c %s" % (cmd_path, partition.getPath())
        return sysutils.run(cmd)

    def resize(self, size_mb, partition):
        minsize = self.minResizeMB(partition)
        if size_mb < minsize:
            size_mb = minsize

        if not self.resizeSilent(size_mb, partition) or not self.preResize(partition):
            raise FSCheckError, _("The filesystem of '%s' partition is NTFS, and this partition \n " \
                                  "was not closed properly. Please restart your system and close \n " \
                                  "this partition properly! After this operation, start Pardus \n " \
                                  "installation again!" % partition.getPath())

        cmd_path = requires("ntfsresize")
        cmd = "%s -P -f -s %dM %s" % (cmd_path, size_mb, partition.getPath())

        if not sysutils.run(cmd):
            raise FSError, _("Resize failed on %s " % partition.getPath())

        return True

    def getLabel(self, partition):
        getLabel(partition)

    def setLabel(self, partition, label):
        label = self.availableLabel(label)
        cmd_path = requires("ntfslabel")
        cmd = "%s %s %s" % (cmd_path, partition.getPath(), label)
        if not sysutils.run(cmd):
            return False
        return label

    def format(self, partition):
        self.preFormat(partition)
        cmd_path = requires("mkfs.ntfs")
        cmd = "%s -f %s" % (cmd_path,partition.getPath())
        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "Ntfs format failed: %s" % partition.getPath()

    def minResizeMB(self, partition):
        cmd_path = requires("ntfsresize")
        cmd = "%s -P -f -i %s" % (cmd_path, partition.getPath())
        lines = os.popen(cmd).readlines()
        _min = 0
        for l in lines:
            if l.startswith("You might resize"):
                # ntfsresize bytes conversion to megabytes isn't as same as us. Huppps!
                # Shouldn't use own conversion, rely on ntfsresize information for megabytes
                _min = int(l.split()[7])

        return _min

##
# fat file system
class FatFileSystem(FileSystem):

    _name = "fat32"
    _sysname = "vfat"
    _mountoptions = "quiet,shortname=mixed,dmask=007,fmask=117,utf8,gid=6"
    _linux_supported = False

    def __init__(self):
        FileSystem.__init__(self)
        self.setImplemented(True)

        # FIXME I will do it later
        self.setResizable(False)

    def format(self, partition):
        self.preFormat(partition)
        cmd_path = requires("mkfs.vfat")
        cmd = "%s %s" %(cmd_path,partition.getPath())
        res = sysutils.run(cmd)
        if not res:
            raise YaliException, "vfat format failed: %s" % partition.getPath()

    def getLabel(self, partition):
        getLabel(partition)

    def setLabel(self, partition, label):
        label = self.availableLabel(label)
        cmd_path = requires("dosfslabel")
        cmd = "%s %s %s" % (cmd_path, partition.getPath(), label)
        if not sysutils.run(cmd):
            return False
        return label

knownFS = {"ext3":      Ext3FileSystem,
           "ext4":      Ext4FileSystem,
           "swap":      SwapFileSystem,
           "linux-swap":SwapFileSystem,
           "ntfs":      NTFSFileSystem,
           "reiserfs":  ReiserFileSystem,
           "xfs":       XFSFileSystem,
           "fat32":     FatFileSystem}
           # "btrfs":     BtrfsFileSystem}


def get_filesystem(name):
    """ Returns filesystem implementation for given filesystem name """
    global knownFS
    if knownFS.has_key(name):
        return knownFS[name]()

    return None

def getLinuxFileSystems():
    supported = []
    for key, value in knownFS.items():
        if value._linux_supported and value._is_ready_to_use:
            supported.append(key)
    return supported

