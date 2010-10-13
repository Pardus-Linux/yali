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
import sys
import math
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.context as ctx
from yali.gui.ScreenWidget import ScreenWidget, GUIError
from yali.gui.Ui.autopartwidget import Ui_AutoPartWidget
from yali.gui.shrink_gui import ShrinkEditor
from yali.storage.partitioning import CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE, doAutoPartition, defaultPartitioning

useAllSpace, replaceExistingLinux, shrinkCurrent, useFreeSpace, createCustom = range(5)

class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Select Partitioning Method")
    icon = "iconPartition"
    helpSummary = _("Partitioning summary")
    help = _('''
<p>
You can install Pardus if you have an unpartitioned-unused disk space 
of 4GBs (10 GBs recommended) or an unused-unpartitioned disk. 
The disk area or partition selected for installation will automatically 
be formatted. Therefore, it is advised to backup your data to avoid future problems.
</p>
<p>Auto-partitioning will automatically format the select disk part/partition 
and install Pardus. If you like, you can do the partitioning manually or make 
Pardus create a new partition for installation.</p>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_AutoPartWidget()
        self.ui.setupUi(self)
        self.storage = ctx.storage
        self.intf = ctx.interface
        self.shrinkOperations = None
        self.connect(self.ui.autopartType, SIGNAL("currentRowChanged(int)"), self.typeChanged)

    def typeChanged(self, index):
        if index == shrinkCurrent:
            resizablePartitions = [partition for partition in self.storage.partitions if partition.exists and
                                                                                         partition.resizable and
                                                                                         partition.format.resizable]
            if not len(resizablePartitions):
                self.intf.messageWindow(_("Warning"),
                                        _("No partitions are available to resize.Only physical\n"
                                          "partitions with specific filesystems can be resized."),
                                        type="warning", customIcon="error")
                ctx.mainScreen.disableNext()
        else:
            ctx.mainScreen.enableNext()

    def setPartitioningType(self):
        if self.storage.clearPartType is None or self.storage.clearPartType == CLEARPART_TYPE_LINUX:
            self.ui.autopartType.setCurrentRow(replaceExistingLinux)
        elif self.storage.clearPartType == CLEARPART_TYPE_NONE:
            self.ui.autopartType.setCurrentRow(useFreeSpace)
        elif self.storage.clearPartType == CLEARPART_TYPE_ALL:
            self.ui.autopartType.setCurrentRow(useAllSpace)

    def shown(self):
        self.setPartitioningType()

    def execute(self):
        rc = self.nextCheck()
        if rc is None:
            #FIXME:Unknown bug
            #sys.exit(0)
            return True
        else:
            return rc

    def nextCheck(self):
        if self.ui.autopartType.currentRow() == createCustom:
            self.storage.clearPartType = CLEARPART_TYPE_NONE
            self.storage.doAutoPart = False
            #If user return back next screen or choose not permitted
            #option(like chosing free space installation however not
            #enough free space to install), we have to reset increment
            ctx.mainScreen.stepIncrement = 1
            return True
        else:
            self.storage.doAutoPart = True
            if self.ui.autopartType.currentRow() == shrinkCurrent:
                shrinkeditor = ShrinkEditor(self, self.storage)
                rc, operations = shrinkeditor.run()
                if rc:
                    for operation in operations:
                        self.storage.devicetree.addOperation(operation)
                else:
                    return False
                self.storage.clearPartType = CLEARPART_TYPE_NONE
            elif self.ui.autopartType.currentRow() == useAllSpace:
                self.storage.clearPartType = CLEARPART_TYPE_ALL
            elif self.ui.autopartType.currentRow() == replaceExistingLinux:
                self.storage.clearPartType = CLEARPART_TYPE_LINUX
            elif self.ui.autopartType.currentRow() == useFreeSpace:
                self.storage.clearPartType = CLEARPART_TYPE_NONE

            ctx.mainScreen.stepIncrement = 2
            self.storage.autoPartitionRequests = defaultPartitioning(self.storage, quiet=0)
            return doAutoPartition(self.storage)

        return False
