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

from os import join

import yali.partitionrequest
import yali.constants
import yali.gui.stages
import yali.gui.screens
import yali.gui.iconfactory


# gui constants
consts = yali.constants.Constants()

# bind some constant values
# There are more values defined in yali/constants.py!
consts.pics_dir = join(consts.data_dir, "pics")
consts.helps_dir = join(consts.data_dir, "helps")

stages = yali.gui.stages.Stages()
screens = yali.gui.screens.Screens()

# partition requests
partrequests = yali.partitionrequest.RequestList()

# icon factory
iconfactory = yali.gui.iconfactory.IconFactory(consts.pics_dir)

# current language
# FIXME: default language will be Turkish after localization support
lang = "en"

