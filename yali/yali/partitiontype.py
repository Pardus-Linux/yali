# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# partition types that will be used in installation process

import parted

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.filesystem

class PartitionType:

    filesystem = None

    ##
    # is equal
    # @param rhs: PartitionType
    def __eq__(self, rhs):
        return self.filesystem == rhs.filesystem

##
# not an intuitive name but need group home and root :(
class __PartitionType(PartitionType):

    def __init__(self):
        # check cmdline for reiserfs support
        cmdline = open("/proc/cmdline", "r").read()
        if cmdline.find("enable_reiserfs") >= 0:
            self.filesystem = yali.filesystem.ReiserFileSystem()
        elif cmdline.find("enable_xfs") >= 0:
            self.filesystem = yali.filesystem.XFSFileSystem()
        else:
            self.filesystem = yali.filesystem.Ext3FileSystem()


class RootPartitionType(__PartitionType):
    name = _("Install Root")
    mountpoint = "/"
    mountoptions = "noatime"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = [ parted.PARTITION_BOOT ]
    label = "PARDUS_ROOT"


class HomePartitionType(__PartitionType):
    name = _("Users' Files")
    mountpoint = "/home"
    mountoptions = "noatime"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = []
    label = "PARDUS_HOME"


class SwapPartitionType(PartitionType):
    name = _("Swap")
    filesystem = yali.filesystem.SwapFileSystem()
    mountpoint = None
    mountoptions = "sw"
    parted_type = parted.PARTITION_SWAP
    parted_flags = []
    label = "PARDUS_SWAP"


root = RootPartitionType()
home = HomePartitionType()
swap = SwapPartitionType()
