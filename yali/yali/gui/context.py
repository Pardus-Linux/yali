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

from os.path import join
from qt import *

import yali.gui.stages
import yali.gui.screens
import yali.gui.iconfactory

# singletons from yali.*
from yali.constants import consts
from yali.options import options
from yali.partitionrequest import partrequests


# bind some constant values
# There are more values defined in yali/constants.py!
consts.pics_dir = join(consts.data_dir, "pics")
consts.slidepics_dir = join(consts.data_dir, "slideshow")
consts.helps_dir = join(consts.data_dir, "helps")

# colors
consts.bg_color = QColor(255,255,255)
consts.fg_color = QColor(0,0,0)

stages = yali.gui.stages.Stages()
screens = yali.gui.screens.Screens()

# icon factory
iconfactory = yali.gui.iconfactory.IconFactory(consts.pics_dir)

# auto partitioning
use_autopart = False

# keydata
keydata = None
