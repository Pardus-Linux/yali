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

import parted

MEGABYTE = 1024 * 1024
GIGABYTE = MEGABYTE * 1024

archinfo = {
    'x86': {'fixedparts': [],
            'disklabel': 'msdos',
            'extended': True},

    'amd64': {'fixedparts': [],
              'disklabel': 'msdos',
              'extended': True},

    'ppc': {'fixedparts':[{'minor': 1, 'type': "metadata"}],
            'disklabel': 'mac',
            'extended': False }
    }


filesystems = {
    'linux-swap': parted.file_system_type_get('linux-swap'),
    'ext3': parted.file_system_type_get('ext3'),
    'ext2': parted.file_system_type_get('ext2'),
    'reiserfs': parted.file_system_type_get('reiserfs'),
    'xfs': parted.file_system_type_get('xfs')
    }


partition_types = {0: ["Intall Root", "ext3", "/"],
                   1: ["Users's Files", "ext3", "/home"],
                   2: ["Swap", "linux-swap", None]
                   }


# magic minor number for representing free space
freespace_minor = -1
freespace_fstype = "free"
