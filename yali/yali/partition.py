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

import yali.parteddata as parteddata

##
# Class representing a single partition within a Device object
class Partition:

    def __init__(self, device, parted_part, minor, mb, start, end, fs_type):
        self._device = device
        self._partition = parted_part
        self._minor = minor
        self._mb = mb
        self._start = start
        self._end = end
        self._fstype = fs_type or _("unknown")
        self._parted_type = parteddata.partitionType

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

    def getFSType(self):
        return self._fstype

    def getStart(self):
        return self._start

    def getEnd(self):
        return self._end

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

    def __init__(self, device, part, mb, start, end):
        Partition.__init__(self, device,
                           part,
                           -1,
                           mb,
                           start,
                           end,
                           "free space")

        self._parted_type = parteddata.freeSpaceType

