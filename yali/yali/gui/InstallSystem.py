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

from qt import *

import yali.pisiiface
from yali.gui.installwidget import InstallWidget


##
# Partitioning screen.
class Widget(InstallWidget):

    def __init__(self, *args):
        apply(InstallWidget.__init__, (self,) + args)
        
    def execute(self):
        # TESTING
        yali.pisiiface.initialize()
        pkg_list = ["bash"]
        yali.pisiiface.install(pkg_list)
        yali.pisiiface.finalize()

        pass
