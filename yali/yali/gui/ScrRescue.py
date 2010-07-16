# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 TUBITAK/UEKAE
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

import yali.sysutils
#import yali.storage
#import yali.partitiontype as parttype
#import yali.partitionrequest as request

from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.GUIAdditional import PartItem
from yali.gui.Ui.rescuewidget import Ui_RescueWidget
import yali.gui.context as ctx

class Widget(QtGui.QWidget, ScreenWidget):
    title = _("System Repair")
    icon = ""
    help = _("""
<font size="+2">System Repair</font>
<font size="+1">
<p>
This is a rescue mode help document.
</p>
</font>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RescueWidget()
        self.ui.setupUi(self)
        self.ui.info.hide()
        self.radios = [self.ui.useGrub, self.ui.usePisiHs, self.ui.usePassword]
        self.isSuitableForRescue = True

        # initialize all storage devices
        if not yali.storage.initDevices():
            raise GUIException, _("No storage device found.")

        # Get usable partitions for rescue
        self.partitionList = PardusPartitions(self)

        # Set Radio actions
        for radio in self.radios:
            if not self.isSuitableForRescue:
                radio.hide()
            else:
                self.connect(radio, SIGNAL("toggled(bool)"), ctx.mainScreen.enableNext)

        # Reboot Button
        self.connect(self.ui.rebootButton, SIGNAL("clicked()"), yali.sysutils.reboot)

    def updateNext(self):
        for radio in self.radios:
            if radio.isChecked():
                ctx.mainScreen.enableNext()
                return
        ctx.mainScreen.disableNext()
        ctx.mainScreen.processEvents()

    def shown(self):
        ctx.mainScreen.disableBack()
        self.updateNext()
        if not self.isSuitableForRescue:
            self.ui.solutionLabel.hide()
            ctx.mainScreen.disableNext()
        else:
            self.ui.rebootButton.hide()

    def execute(self):
        if self.ui.usePisiHs.isChecked():
            ctx.rescueMode = "pisi"
            ctx.mainScreen.moveInc = 2
        elif self.ui.usePassword.isChecked():
            ctx.rescueMode = "pass"
            ctx.mainScreen.moveInc = 3
        elif self.ui.useGrub.isChecked():
            ctx.rescueMode = "grub"

        ctx.installData.rescuePartition = self.ui.partitionList.currentItem().getPartition()
        ctx.debugger.log("Selected Partition for rescue is %s" % ctx.installData.rescuePartition.getPath())

        ctx.yali.info.updateAndShow(_("Mounting disk partition..."))
        # Mount selected partition
        ctx.partrequests.append(request.MountRequest(ctx.installData.rescuePartition, parttype.root))
        ctx.partrequests.applyAll()
        ctx.yali.info.hide()

        return True

class PardusPartitions:
    def __init__(self, parentWidget):
        partitionList, pardusPartitions = self.scanDisks()
        if len(partitionList) == 0:
            parentWidget.ui.infoLabel.setText(_("YALI could not locate a suitable disk partition on this computer."))
            parentWidget.ui.info.show()
            parentWidget.ui.partitionList.hide()
            parentWidget.isSuitableForRescue = False
        else:
            for partition in partitionList:
                if partition in pardusPartitions:
                    icon = "parduspart"
                else:
                    icon = "iconPartition"
                label = partition.getFSLabel() or ''
                _info = "%s on %s [%s]" % (partition.getDevice().getModel(),
                                           partition.getPath(),
                                           label)
                PartItem(parentWidget.ui.partitionList, partition, _info, icon)

            parentWidget.ui.partitionList.setCurrentItem(parentWidget.ui.partitionList.item(0))
            parentWidget.ui.infoLabel.setText(_("Please select a disk partition from the list below:"))

    def scanDisks(self):
        pardusPartitions = []
        linuxPartitions  = []
        ctx.debugger.log("Checking for Pardus ...")
        for disk in yali.storage.devices:
            for partition in disk.getPartitions():
                fs = partition.getFSName()
                label = partition.getFSLabel() or ''
                if fs in ("ext4", "ext3", "reiserfs", "xfs"):
                    ctx.debugger.log("Partition found which has usable fs (%s)" % partition.getPath())
                    linuxPartitions.append(partition)
                    if label.startswith("PARDUS_ROOT"):
                        ctx.debugger.log("Pardus Partition found (%s)" % partition.getPath())
                        pardus_release = yali.sysutils.pardusRelease(partition.getPath(), fs)
                        if pardus_release:
                            pardusPartitions.append(partition)
                        # If it is not a pardus installed partition skip it
                        yali.sysutils.umount_()

        return (linuxPartitions, pardusPartitions)

