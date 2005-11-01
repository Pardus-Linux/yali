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


import yali.gui.stages
import yali.gui.screens
import yali.partitionrequest as request
import yali.gui.iconfactory

stages = yali.gui.stages.Stages()
screens = yali.gui.screens.Screens()

# partition requests
partrequests = request.RequestList()

# icon factory
iconfactory = yali.gui.iconfactory.IconFactory()


# current language
# FIXME: default language will be Turkish after localization support
lang = "en"
