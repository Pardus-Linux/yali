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

import os

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import parted
import yali.parteddata as parteddata
import yali.filesystem


##
# Class representing a single partition within a Device object
class Partition:

    def __init__(self, device, parted_part, minor, mb, start, end, fs_name, fs_ready=True):
        self._device = device
        self._partition = parted_part
        self._minor = minor
        self._mb = mb
        self._start = start
        self._end = end
        self._fsname = fs_name or _("unknown")
        self._parted_type = parteddata.partitionType
        self._fs_ready = fs_ready


    def getFormatted(self):
        return self.isFileSystemReady()

    def isFileSystemReady(self):
        return self._fs_ready

    def setFileSystemType(self, fs_type):
        if isinstance(fs_type, yali.filesystem.FileSystem):
            fs_type = fs_type.getFSType()

        self._partition.set_system(fs_type)


    def setPartedFlags(self, flags):
        for flag in flags:
            if self._partition.is_flag_available(flag):
                self._partition.set_flag(flag, 1)

    ##
    # check if partition is logical
    def isLogical(self):
        return self._partition.type == parted.PARTITION_LOGICAL

    ##
    # check if partition is extended
    def isExtended(self):
        return self._partition.type == parted.PARTITION_EXTENDED


    ##
    # get freespace on extended partition
    def getFreeBytes(self):
        if not self.isExtended():
            return 0

        total_bytes = self.getBytes()

        d = self.getDevice()
        # 8: magic number that all, even windows, use.
        # (OK not really ;)
        size = 8 * parteddata.MEGABYTE
        for p in d.getPartitions():
            if p.isLogical():
                size += p.getBytes()

        return total_bytes - size


    def getFreeMB(self):
        return long(self.getFreeBytes() / parteddata.MEGABYTE)


    def getType(self):
        return self._parted_type


    ##
    # get parted partition
    def getPartition(self):
        return self._partition

    ##
    # get parted device
    def getDevice(self):
        return self._device

    ##
    # device path (eg. /dev/sda)
    def getDevicePath(self):
        return self._device.getPath()

    ##
    # partition path (eg. /dev/sda1)
    def getPath(self):
        return "%s%d" %(self.getDevicePath(), self.getMinor())

    ##
    # partition name (eg. sda1)
    def getName(self):
        return os.path.basename(self.getPath())

    def getMinor(self):
        return self._minor

    def getFSName(self):
        return self._fsname

    def getFSLabel(self):
        fs = yali.filesystem.get_filesystem(self.getFSName())
        try:
            return fs.getLabel(self)
        except AttributeError, e:
            return None

    def getStart(self):
        return self._start

    def getEnd(self):
        return self._end

    def getBytes(self):
        return long(self.getPartition().geom.length *
                    self.getDevice()._sector_size)

    def getMB(self):
        return self._mb

    def getGB(self):
        return self.getMB() / parteddata.KILOBYTE

    def getSizeStr(self):
        gb = self.getGB()
        if gb > 1:
            return "%0.2f GB" % gb
        else:
            return "%0.2f MB" % self.getMB()

    ##
    # is equal? compare the partiton path
    # @param: Partition
    # returns: Boolean
    def __eq__(self, rhs):
        return self.getPath() == rhs.getPath()


##
# Class representing free space within a Device object
class FreeSpace(Partition):

    def __init__(self, device, parted_part, mb, start, end):
        Partition.__init__(self, device,
                           parted_part,
                           -1,
                           mb,
                           start,
                           end,
                           _("free space"))

        self._parted_type = parteddata.freeSpaceType


