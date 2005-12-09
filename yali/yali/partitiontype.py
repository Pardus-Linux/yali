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

# partition types that will be used in installation process

import os
import parted

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.filesystem


class PartitionType:
    ##
    # is equal
    # @param rhs: PartitionType
    def __eq__(self, rhs):
        return self.filesystem == rhs.filesystem

class RootPartitionType(PartitionType):
    name = _("Install Root")
    mountpoint = "/"
    mountoptions = "noatime"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = [ parted.PARTITION_BOOT ]

    def __init__(self):
        # check cmdline for reiserfs support
        cmdline = open("/proc/cmdline", "r").read()
        if cmdline.find("enable_reiserfs") >= 0:
            self.filesystem = yali.filesystem.ReiserFileSystem()
        else:
            self.filesystem = yali.filesystem.Ext3FileSystem()

class HomePartitionType(PartitionType):
    name = _("Users' Files")
    filesystem = yali.filesystem.Ext3FileSystem()
    mountpoint = "/home"
    mountoptions = "noatime"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = []

class SwapPartitionType(PartitionType):
    name = _("Swap")
    filesystem = yali.filesystem.SwapFileSystem()
    mountpoint = None
    mountoptions = "sw"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = []


root = RootPartitionType()
home = HomePartitionType()
swap = SwapPartitionType()
