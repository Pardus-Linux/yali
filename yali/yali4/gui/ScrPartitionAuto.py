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
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import time
import yali4.storage
import yali4.partitionrequest as request
import yali4.partitiontype as parttype
import yali4.parteddata as parteddata

from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.Ui.autopartwidget import Ui_AutoPartWidget
from yali4.gui.GUIAdditional import AutoPartQuestionWidget
from yali4.gui.GUIException import *
import yali4.gui.context as ctx

from yali4.gui.installdata import *

##
# Partition Choice Widget
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Choose Partitioning')
    desc = _('Auto or Manual partitioning...')
    icon = "iconPartition"
    help = _('''
<font size="+2">Automatic Partitioning</font>
<font size="+1">
<p>
You can install Pardus if you have an unpartitioned-unused disk space 
of 4GBs (10 GBs recommended) or an unused-unpartitioned disk. 
The disk area or partition selected for installation will automatically 
be formatted. Therefore, it is advised to backup your data to avoid future problems.
</p>
<p>Auto-partitioning will automatically format the select disk part/partition 
and install Pardus 2009. If you like, you can do the partitioning manually or make 
Pardus 2009 create a new partition for installation.</p>
<p>
Please refer to Pardus Installing and Using Guide for more information
about disk partitioning.
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_AutoPartWidget()
        self.ui.setupUi(self)

        self.device = None
        self.enable_next = False
        self.isAutoResizeAvail = False
        self.lastChoice = self.ui.accept_auto_1

        # initialize all storage devices
        if not yali4.storage.initDevices():
            raise GUIException, _("Can't find a storage device!")

        # fill device list
        for dev in yali4.storage.devices:
            if dev.getTotalMB() >= ctx.consts.min_root_size:
                DeviceItem(self.ui.device_list, dev)

        if not self.ui.device_list.count():
            raise YaliExceptionInfo, _("It seems that you don't have the required disk space (min. %s) for Pardus installation." % ctx.consts.min_root_size)

        self.connect(self.ui.accept_auto_1, SIGNAL("toggled(bool)"),self.slotSelectAutoUseAvail)
        self.connect(self.ui.accept_auto_2, SIGNAL("toggled(bool)"),self.slotSelectAutoEraseAll)
        self.connect(self.ui.manual,        SIGNAL("clicked()"),self.slotSelectManual)
        self.connect(self.ui.manual,        SIGNAL("toggled(bool)"),self.slotToggleManual)
        self.connect(self.ui.accept_auto,   SIGNAL("clicked()"),self.slotSelectAuto)
        self.connect(self.ui.device_list,   SIGNAL("currentItemChanged(QListWidgetItem *, QListWidgetItem * )"),self.slotDeviceChanged)

    def fillDeviceList(self, limit=False):
        self.ui.device_list.clear()

        def _in(_list, _item):
            for item in _list:
                if item.getName() == _item.getName():
                    return True
            return False

        # fill device list
        for dev in yali4.storage.devices:
            if dev.getTotalMB() >= ctx.consts.min_root_size:
                if limit:
                    if _in(self.freeSpaceDisks, dev):
                        DeviceItem(self.ui.device_list, dev, forceToFirst = True)
                    elif _in(self.resizableDisks, dev):
                        DeviceItem(self.ui.device_list, dev)
                else:
                    DeviceItem(self.ui.device_list, dev)

        # select the first disk by default
        self.ui.device_list.setCurrentRow(0)

    def shown(self):

        ctx.partrequests.remove_all()

        # scan partitions for resizing
        self.toggleAll()
        ctx.yali.scanPartitions(self)
        self.toggleAll(True)
        self.fillDeviceList(self.ui.accept_auto_1.isChecked())

        self.arp = []
        self.autoPartPartition = None

        for partition in self.freeSpacePartitions:
            if partition["newSize"] >= ctx.consts.min_root_size:
                self.arp.append(partition)
        for partition in self.resizablePartitions:
            if partition["newSize"] / 2 >= ctx.consts.min_root_size:
                self.arp.append(partition)

        if len(self.arp) == 0:
            self.isAutoResizeAvail = False
            self.ui.accept_auto_1.setEnabled(self.isAutoResizeAvail)
            self.ui.accept_auto_2.toggle()
        elif len(self.arp) >= 1:
            self.isAutoResizeAvail = True
            self.autoPartPartition = self.arp[0]
            self.ui.accept_auto_1.toggle()

        ctx.mainScreen.disableNext()
        if ctx.installData.autoPartMethod == methodUseAvail:
            self.ui.accept_auto_1.toggle()
        if ctx.installData.autoPartMethod == methodEraseAll:
            self.ui.accept_auto_2.toggle()
        if ctx.installData.autoPartMethod == methodManual:
            self.slotSelectManual()

        self.update()

    def execute(self):
        ctx.installData.autoPartDev = None
        _tmp = []
        if len(self.arp) > 1:
            for part in self.arp:
                if part["partition"].getDevice().getPath() == self.device.getPath():
                    self.autoPartPartition = part
                    _tmp.append(part)
        if self.ui.accept_auto_1.isChecked() or self.ui.accept_auto_2.isChecked():
            if self.ui.accept_auto_1.isChecked() and len(_tmp) > 1:
                question = AutoPartQuestionWidget(self, _tmp)
                question.show()
                ctx.mainScreen.moveInc = 0
            else:
                self.execute_()
        else:
            ctx.installData.autoPartMethod = methodManual
        ctx.selectedDisk = self.ui.device_list.currentRow()
        return True

    def execute_(self, move=False):
        ctx.installData.autoPartDev = self.device
        ctx.installData.autoPartPartition = self.autoPartPartition
        ctx.autoInstall = True
        ctx.debugger.log("Automatic Partition selected..")
        ctx.debugger.log("Trying to use %s for automatic partitioning.." % self.device.getPath())
        if self.autoPartPartition:
            ctx.debugger.log("Trying to use %s for automatic partitioning.." % self.autoPartPartition["partition"].getPath())

        # We pass the Manual Partitioning screen
        ctx.mainScreen.moveInc = 2
        if move:
            ctx.mainScreen.slotNext(dryRun=True)

    def slotDeviceChanged(self, n, o):
        if n:
            self.device = n.getDevice()
            ctx.debugger.log("Install device selected as %s" % self.device.getPath())

    def slotSelectAutoEraseAll(self, state):
        ctx.installData.autoPartMethod = methodEraseAll
        self.fillDeviceList()
        self.enable_next = state
        self.device = self.ui.device_list.currentItem().getDevice()
        self.lastChoice = self.ui.accept_auto_2
        self.update()

    def slotSelectAutoUseAvail(self, state):
        ctx.installData.autoPartMethod = methodUseAvail
        self.fillDeviceList(state)
        self.enable_next = state
        self.device = self.ui.device_list.currentItem().getDevice()
        self.lastChoice = self.ui.accept_auto_1
        self.update()

    def slotSelectAuto(self):
        self.ui.accept_auto.setChecked(True)
        self.ui.manual.setChecked(False)
        self.setAutoExclusives()
        self.lastChoice.setChecked(True)

    def slotSelectManual(self):
        self.ui.manual.setChecked(True)
        self.ui.accept_auto.setChecked(False)
        self.setAutoExclusives(False)
        ctx.installData.autoPartMethod = methodManual
        self.enable_next = True
        self.update()

    def slotToggleManual(self):
        self.ui.accept_auto_1.setChecked(False)
        self.ui.accept_auto_2.setChecked(False)

    def setAutoExclusives(self, val=True):
        self.ui.accept_auto_1.setEnabled(self.isAutoResizeAvail)
        self.ui.accept_auto_1.setAutoExclusive(val)
        self.ui.accept_auto_2.setAutoExclusive(val)
        if not val:
            self.slotToggleManual()

    def update(self):
        if self.ui.manual.isChecked():
            self.enable_next = True
            self.ui.accept_auto_1.setEnabled(False)
            self.ui.accept_auto_2.setEnabled(False)
        if self.enable_next:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def toggleAll(self, state=False):
        widgets = ["manual", "accept_auto", "accept_auto_1", "accept_auto_2"]
        for widget in widgets:
            getattr(self.ui, widget).setEnabled(state)
        ctx.mainScreen.processEvents()

class DeviceItem(QtGui.QListWidgetItem):
    def __init__(self, parent, dev, forceToFirst=False):
        text = u"%s - %s (%s)" % (dev.getModel(),
                                  dev.getName(),
                                  dev.getSizeStr())
        QtGui.QListWidgetItem.__init__(self, text, None)
        self._dev = dev
        if forceToFirst:
            parent.insertItem(0, self)
        else:
            parent.addItem(self)

    def getDevice(self):
        return self._dev

