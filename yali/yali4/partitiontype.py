# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009, TUBITAK/UEKAE
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
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from yali4.filesystem import get_filesystem as fs

class PartitionType:
    filesystem = None
    needsmtab = True
    supportedFileSystems = [fs("ext4"),
                            fs("ext3"),
                            fs("reiserfs"),
                            fs("xfs")]
                            #fs("btrfs")]

    def setFileSystem(self, filesystem):
        self.filesystem = fs(filesystem)

class RootPartitionType(PartitionType):
    name = _("Install Root")
    mountpoint = "/"
    filesystem = fs("ext4")
    mountoptions = "noatime"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = [ parted.PARTITION_BOOT ]
    label = "PARDUS_ROOT"
    desc = _("as Pardus System Files (mandatory)")

class HomePartitionType(PartitionType):
    name = _("Users' Files")
    mountpoint = "/home"
    filesystem = fs("ext4")
    mountoptions = "noatime"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = []
    label = "PARDUS_HOME"
    desc = _("as User Files (optional)")

class SwapPartitionType(PartitionType):
    name = _("Swap")
    filesystem = fs("swap")
    mountpoint = None
    mountoptions = "sw"
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = []
    label = "PARDUS_SWAP"
    supportedFileSystems = [fs("swap")]
    desc = _("as Swap Space (optional)")

class ArchivePartitionType(PartitionType):
    name = _("Archive Partition")
    mountpoint = "/mnt/archive"
    filesystem = fs("ntfs")
    mountoptions = "noatime"
    needsmtab = False
    parted_type = parted.PARTITION_PRIMARY
    parted_flags = []
    label = "ARCHIVE"
    supportedFileSystems = [fs("ext4"),
                            fs("ext3"),
                            fs("reiserfs"),
                            fs("xfs"),
                            fs("ntfs"),
                            fs("fat32")]
                            #fs("btrfs")]
    desc = _("as Storage Area")

root = RootPartitionType()
home = HomePartitionType()
swap = SwapPartitionType()
archive = ArchivePartitionType()
