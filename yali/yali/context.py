# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import os
import yali.installdata

# singletons from yali.*
from yali.installdata import installData
from yali.constants import consts
from yali.options import options

# style sheet
import yali.sysutils
consts.stylesheet = os.path.join(consts.data_dir, "data/%s.qss" % (yali.sysutils.checkYaliOptions("theme") or options.theme))
consts.alternatestylesheet = os.path.join(consts.data_dir, "data/oxygen.qss")

# lock for format request
requestsCompleted = False

# debugger variables
debugger = None
debugEnabled = False

# edd check
isEddFailed = False

# auto partitioning
use_autopart = False

# auto installation
autoInstall = False

# keydata
keydata = None

# Bus
bus = None

# Selected disk for manual partitioning screen
selectedDisk = None
