# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import time
from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.storage
import yali.partitionrequest as request
import yali.partitiontype as parttype
import yali.parteddata as parteddata

from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.autopartwidget import AutoPartWidget
from yali.gui.YaliDialog import WarningDialog
from yali.gui.InformationWindow import InformationWindow
from yali.gui.GUIException import *
import yali.gui.context as ctx


class Widget(AutoPartWidget, ScreenWidget):

    help = _('''
<font size="+2">Automatic Partitioning</font>

<font size="+1">
<p>
Pardus can be installed on a variety of hardware. You can install Pardus
on an empty disk or hard disk partition. <b>An installation will automatically
destroy the previously saved information on selected partitions. </b>
</p>
<p>
Automatic partitioning use your entire disk for Pardus installation. From 
this screen you can select to automatically partition one of you disks, or
you can skip this screen and try manual partitioning.
</p>
<p>
Please refer to Pardus Installing and Using Guide for more information
about disk partitioning.
</p>
</font>
''')

    def __init__(self, *args):
        apply(AutoPartWidget.__init__, (self,) + args)

        self.device = None
        self.enable_next = False

        self.device_list.setPaletteBackgroundColor(ctx.consts.bg_color)
        self.device_list.setPaletteForegroundColor(ctx.consts.fg_color)

        # initialize all storage devices
        if not yali.storage.init_devices():
            raise GUIException, _("Can't find a storage device!")

        # fill device list
        for dev in yali.storage.devices:
            if dev.getTotalMB() >= ctx.consts.min_root_size:
                DeviceItem(self.device_list, dev)
        # select the first disk by default
        self.device_list.setSelected(0, True)

        if not self.device_list.count():
            raise YaliExceptionInfo, _("It seems that you don't have the required disk space (min. %s) for Pardus installation." % ctx.consts.min_root_size)

        self.connect(self.accept_auto, SIGNAL("clicked()"),
                     self.slotSelectAuto)
        self.connect(self.manual, SIGNAL("clicked()"),
                     self.slotSelectManual)

        self.connect(self.device_list, SIGNAL("selectionChanged(QListBoxItem*)"),
                     self.slotDeviceChanged)

    def shown(self):
        from os.path import basename
        ctx.debugger.log("%s loaded" % basename(__file__))
        ctx.screens.disableNext()

        self.updateUI()

    def execute(self):

        def autopartDevice():
            dev = self.device

            # first delete partitions on device
            dev.deleteAllPartitions()
            dev.commit()

            p = dev.addPartition(parttype.root.parted_type,
                                 parttype.root.filesystem,
                                 dev.getFreeMB(),
                                 parttype.root.parted_flags)
            p = dev.getPartition(p.num) # get partition.Partition
            dev.commit()

            ctx.partrequests.append(
                request.MountRequest(p, parttype.root))
            ctx.partrequests.append(
                request.FormatRequest(p, parttype.root))
            ctx.partrequests.append(
                request.LabelRequest(p, parttype.root))
            ctx.partrequests.append(
                request.SwapFileRequest(p, parttype.root))


        if self.accept_auto.isChecked():

            # show confirmation dialog
            #w = WarningWidget(self)
            #self.dialog = WarningDialog(w, self)
            #if not self.dialog.exec_loop():
            #    # disabled by weaver
            #    ctx.screens.enablePrev()
            #    self.updateUI()
            #    return False

            # show information window...
            info_window = InformationWindow(self, _("Please wait while formatting!"))

            # inform user
            self.info.setText(_('<font color="#FF6D19">Preparing your disk for installation!</font>'))
            ctx.screens.processEvents()

            # remove all other requests (if there are any).
            ctx.partrequests.remove_all()

            ctx.use_autopart = True
            autopartDevice()
            # need to wait for devices to be created
            time.sleep(1)
            ctx.partrequests.applyAll()

            # skip next screen()
            num = ctx.screens.getCurrentIndex() + 1
            ctx.screens.goToScreen(num)

            # close window
            info_window.close(True)

        return True

    def slotDeviceChanged(self, i):
        self.device = i.getDevice()

    def slotSelectAuto(self):
        self.enable_next = True
        self.device = self.device_list.selectedItem().getDevice()
        self.updateUI()

    def slotSelectManual(self):
        self.enable_next = True
        self.updateUI()

    def updateUI(self):
        if self.enable_next:
            ctx.screens.enableNext()
        else:
            ctx.screens.disableNext()


class DeviceItem(QListBoxText):

    def __init__(self, parent, dev):
        text = u"%s - %s (%s)" %(dev.getModel(),
                                dev.getName(),
                                dev.getSizeStr())
        apply(QListBoxText.__init__, (self,parent,text))
        self._dev = dev

    def getDevice(self):
        return self._dev






class WarningWidget(QWidget):

    def __init__(self, *args):
        QWidget.__init__(self, *args)

        l = QVBoxLayout(self)
        l.setSpacing(20)
        l.setMargin(10)

        warning = QLabel(self)
#        warning.setTextFormat(warning.RichText)
        warning.setText(_('''<b>
<p>This action will use your entire disk for Pardus installation and
all your present data on the selected disk will be lost.</p>

<p>After being sure you had your backup this is generally a safe
and easy way to install Pardus.</p>
</b>
'''))

        self.cancel = QPushButton(self)
        self.cancel.setText(_("Cancel"))

        self.ok = QPushButton(self)
        self.ok.setText(_("O.K. Go Ahead"))

        buttons = QHBoxLayout(self)
        buttons.setSpacing(10)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel)
        buttons.addWidget(self.ok)

        l.addWidget(warning)
        l.addLayout(buttons)


        self.connect(self.ok, SIGNAL("clicked()"),
                     self.slotOK)
        self.connect(self.cancel, SIGNAL("clicked()"),
                     self.slotCancel)

    def slotOK(self):
        self.emit(PYSIGNAL("signalOK"), ())

    def slotCancel(self):
        self.emit(PYSIGNAL("signalCancel"), ())
