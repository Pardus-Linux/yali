# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.gui.context as ctx
import yali.partitionrequest as request
import yali.partitiontype as parttype
from yali.gui.YaliDialog import Dialog, QuestionDialog
from yali.gui.GUIException import *
from yali.gui.DiskWidgets import *
from yali.gui.ScreenWidget import ScreenWidget

##
# Partitioning screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Manual Partitioning')
    desc = _('You can easily configure your partitions...')
    icon = "iconPartition"
    help = _('''
<font size="+2">Partitioning your hard disk</font>
<font size="+1">
<p>
In this screen, you can manually partition your disk. You can select 
existing partitions and resize or delete them. You can create new 
partition(s) in the empty parts, make Pardus use them for system files, 
users' home directories, swap space or general use. The changes that you 
make will not be applied until you go on with the installation, 
which means you can revert if you make any unwanted changes or change your configuration.
</p>
<p>
Please refer to Pardus Installing and Using Guide for more information
about disk partitioning.
</p>
</font>
''')


    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.diskList = DiskList(self)
        gridlayout = QtGui.QGridLayout(self)
        gridlayout.setContentsMargins(1,-1,11,-1)
        gridlayout.addWidget(self.diskList)

    def shown(self):
        ctx.mainScreen.disableNext()
        self.diskList.checkRootPartRequest()

        # Set current disk if selected in previous screen
        if not ctx.selectedDisk == None:
            self.diskList.setCurrent(ctx.selectedDisk)

    def update(self):
        self.diskList.updateEnabled = True

    ##
    # do the work and run requested actions on partitions.
    def execute(self):
        ctx.debugger.log("Manual Partitioning selected...")
        ctx.mainScreen.processEvents()
        return True

    def backCheck(self):
        reply = QuestionDialog(_("Warning"),
                               _("All changes that you made will be removed."))

        if reply == "yes":
            self.diskList.reinitDevices()
            return True
        return False

