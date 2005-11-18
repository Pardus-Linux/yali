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
    filesystem = yali.filesystem.Ext3FileSystem()
    mountpoint = "/"
    mountoptions = "noatime"
    parted_type = 0

class HomePartitionType(PartitionType):
    name = _("Users's Files")
    filesystem = yali.filesystem.Ext3FileSystem()
    mountpoint = "/home"
    mountoptions = "noatime"
    parted_type = 0

class SwapPartitionType(PartitionType):
    name = _("Swap")
    filesystem = yali.filesystem.SwapFileSystem()
    mountpoint = None
    mountoptions = "sw"
    parted_type = parted.PARTITION_SWAP

