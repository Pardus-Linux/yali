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
    title = _("Setup Disk Partitions")
    icon = "iconPartition"
    help = _("""
<font size="+2">Manual Partitioning</font>
<font size="+1">
<p>
With manual partitioning, you can freely create, resize, delete partitions
visually according to your needs.
</p>
<p>
While it is possible to install Pardus into a single partition, you may also
prefer to create a separate partition for /home directory which contains the
personal files of all the users available on the system.
</p>
<p>
Swap space is used when the amount of physical memory (RAM) is full. If the
system needs more memory resources and the physical memory is full, inactive
sections of memory are moved to this space. By default, YALI creates a swap
file on your root partition but you may prefer to dedicate a separate disk
partition for swap space which is recommended.
</p>
<p>
Swap space is generally recommended for people with less than 1GB of RAM,
but becomes more a matter preference on computers with more memory.
</p>
<p>
NOTE: If you don't create a separate disk partition for the swap space,
suspending the computer to disk (Hibernation) will not work.
</p>
<p>
The changes made in this section, will not be applied until you proceed
with the installation which means that you can freely undo/redo any operation.
</p>
</font>
""")


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
                               _("All changes that you have made will be lost. Are you sure you want to continue?"))

        if reply == "yes":
            self.diskList.reinitDevices()
            return True
        return False

