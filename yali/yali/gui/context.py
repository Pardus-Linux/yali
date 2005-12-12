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

from yali.log import logger
import yali.partitionrequest
import yali.constants
import yali.gui.stages
import yali.gui.screens
import yali.gui.iconfactory


# gui constants
consts = yali.constants.consts

# bind some constant values
# There are more values defined in yali/constants.py!
consts.pics_dir = join(consts.data_dir, "pics")
consts.slidepics_dir = join(consts.data_dir, "slideshow")
consts.helps_dir = join(consts.data_dir, "helps")

stages = yali.gui.stages.Stages()
screens = yali.gui.screens.Screens()

# partition requests
partrequests = yali.partitionrequest.RequestList()

# icon factory
iconfactory = yali.gui.iconfactory.IconFactory(consts.pics_dir)

# auto partitioning
use_autopart = False

# colors
consts.bg_color = QColor(36,68,80)
consts.fg_color = QColor(255,255,255)
