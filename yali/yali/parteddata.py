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

KILOBYTE = 1024
MEGABYTE = KILOBYTE * KILOBYTE
GIGABYTE = MEGABYTE * KILOBYTE

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


# magic minor number for representing free space
freespace_minor = -1
freespace_fstype = "free"




