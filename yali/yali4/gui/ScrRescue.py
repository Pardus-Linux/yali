# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali4.storage
import yali4.sysutils
import yali4.partitiontype as parttype
import yali4.partitionrequest as request
from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.GUIAdditional import PartItem
from yali4.gui.Ui.rescuewidget import Ui_RescueWidget
import yali4.gui.context as ctx

class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Rescue Mode')
    desc = _('You can reinstall your Grub or you can take back your system by using Pisi History...')
    icon = ""
    help = _('''
<font size="+2">Rescue Mode</font>
<font size="+1"><p>This is a rescue mode help document.</p></font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RescueWidget()
        self.ui.setupUi(self)
        self.ui.info.hide()
        self.radios = [self.ui.useGrub, self.ui.usePisiHs, self.ui.usePassword]
        self.isSuitableForRescue = True

        # initialize all storage devices
        if not yali4.storage.initDevices():
            raise GUIException, _("Can't find a storage device!")

        # Get usable partitions for rescue
        self.partitionList = PardusPartitions(self)

        # Set Radio actions
        for radio in self.radios:
            if not self.isSuitableForRescue:
                radio.hide()
            else:
                self.connect(radio, SIGNAL("toggled(bool)"), ctx.mainScreen.enableNext)

        # Reboot Button
        self.connect(self.ui.rebootButton, SIGNAL("clicked()"), yali4.sysutils.reboot)

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

        ctx.yali.info.updateAndShow(_("Mounting selected partition..."))
        # Mount selected partition
        ctx.partrequests.append(request.MountRequest(ctx.installData.rescuePartition, parttype.root))
        ctx.partrequests.applyAll()
        ctx.yali.info.hide()

        return True

class PardusPartitions:
    def __init__(self, parentWidget):
        partitionList, pardusPartitions = self.scanDisks()
        if len(partitionList) == 0:
            parentWidget.ui.infoLabel.setText(_("Yali couldn't find a suitable partition on your system"))
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
                _info = "%s - %s %s" % (partition.getDevice().getModel(),
                                        partition.getPath(),
                                        label)
                PartItem(parentWidget.ui.partitionList, partition, _info, icon)

            parentWidget.ui.partitionList.setCurrentItem(parentWidget.ui.partitionList.item(0))
            parentWidget.ui.infoLabel.setText(_("Please select a partition from list"))

    def scanDisks(self):
        pardusPartitions = []
        linuxPartitions  = []
        ctx.debugger.log("Checking for Pardus ...")
        for disk in yali4.storage.devices:
            for partition in disk.getPartitions():
                fs = partition.getFSName()
                label = partition.getFSLabel() or ''
                if fs in ("ext4", "ext3", "reiserfs", "xfs"):
                    ctx.debugger.log("Partition found which has usable fs (%s)" % partition.getPath())
                    linuxPartitions.append(partition)
                    if label.startswith("PARDUS_ROOT"):
                        ctx.debugger.log("Pardus Partition found (%s)" % partition.getPath())
                        pardus_release = yali4.sysutils.pardusRelease(partition.getPath(), fs)
                        if pardus_release:
                            pardusPartitions.append(partition)
                        # If it is not a pardus installed partition skip it
                        yali4.sysutils.umount_()

        return (linuxPartitions, pardusPartitions)

