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

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.gui.context as ctx
import yali.partitiontype as parttype
import yali.parteddata as parteddata
import yali.partitionrequest as request
import yali.filesystem as filesystem

from yali.gui.GUIException import *
from yali.gui.Ui.parteditbuttons import PartEditButtons
from yali.gui.Ui.parteditwidget import PartEditWidget

editState, createState, deleteState, resizeState = range(4)
  
##
# Edit partition widget
class PartEdit(QWidget):

    _d = None
    _state = None

    ##
    # Initialize PartEdit
    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.vbox = QVBoxLayout(self)

        self.edit = PartEditWidgetImpl(self)
        self.vbox.addWidget(self.edit)

        self.warning = QLabel(self)
        self.vbox.addWidget(self.warning, 0, self.vbox.AlignCenter)

        self.buttons = PartEditButtons(self)
        self.vbox.addWidget(self.buttons)

        self.connect(self.buttons.applyButton, SIGNAL("clicked()"),
                     self.slotApplyClicked)
        self.connect(self.buttons.cancelButton, SIGNAL("clicked()"),
                     self.slotCancelClicked)

        # use available
        self.connect(self.edit.use_available, SIGNAL("toggled(bool)"),
                     self.slotUseAvailable)


    def slotUseAvailable(self, b):
        if b:
            s = 0
            t = self._d.getType()
            if t == parteddata.deviceType:
                s = self._d.getLargestContinuousFreeMB()
            else:
                s = self._d.getMB()

            self.edit.size.setValue(s)
            self.edit.size.setEnabled(False)
        else:
            self.edit.size.setEnabled(True)

    ##
    # set up widget for use.
    def setState(self, state, dev):
        self._d = dev

        # Hacky: show only one widget for an action.
        self.warning.hide()
        self.edit.hide()
        self.show()

        t = self._d.getType()

        if t == parteddata.deviceType:
            if state == createState:
                self.edit.size.setMaxValue(self._d.getLargestContinuousFreeMB())
                self.edit.setState(state)
                self.edit.show()

            elif state == deleteState:
                self.warning.setText(
                    _("You are going to delete all partitions on device '%s'")
                    %(self._d.getModel()))
                self.warning.show()

        elif t ==  parteddata.partitionType:
            if state == createState and self._d.isExtended():
                self.edit.size.setMaxValue(self._d.getFreeMB())
                self.edit.setState(state, partition=self._d)
                self.edit.show()

            elif state == deleteState:
                self.warning.setText(
                    _("You are going to delete partition '%s' on device '%s'!")
                    % (self._d.getMinor(), self._d.getDevice().getModel()))
                self.warning.show()

            elif state == editState:
                self.edit.setState(state, partition=self._d)
                self.edit.show()

            elif state == resizeState:
                fs = filesystem.get_filesystem(self._d.getFSName())
                min_size = fs.minResizeMB(self._d)
                max_size = self._d.getMB()

                self.edit.size.setMinValue(min_size)
                self.edit.size.setMaxValue(max_size)

                self.edit.setState(state, partition=self._d)
                self.edit.show()

        elif t == parteddata.freeSpaceType:
            if state == createState:
                # get free space
                self.edit.size.setMaxValue(self._d.getMB())
                self.edit.setState(state)
                self.edit.show()


        self._state = state


    ##
    # Apply button is clicked, make the necessary modifications and
    # emit a signal.
    def slotApplyClicked(self):
        state = self._state
        t = self._d.getType()

        # get partition type from checked
        def get_part_type():
            if self.edit.root.isChecked():
                return parttype.root
            elif self.edit.home.isChecked():
                return parttype.home
            elif self.edit.swap.isChecked():
                return parttype.swap

            else:
                self.warning.setText(
                    _("You must select a partition type from the list below."))
                self.warning.show()
                return None


        def create_new_partition(device, type = parteddata.PARTITION_PRIMARY):
            t = get_part_type()
            if not t:
                return False

            if t == parttype.root:
                size = self.edit.size.text().toInt()[0]
                if size <= ctx.consts.min_root_size:
                    self.warning.setText(
                        _("'Install Root' size must be larger than %s MB.") % ctx.consts.min_root_size)
                    self.warning.show()
                    return False


            size = self.edit.size.text().toInt()[0]


            p = device.addPartition(type, t.filesystem, size, t.parted_flags)
#            device.commit()
            partition = device.getPartition(p.num)

            if not edit_requests(partition):
                return False

            return True

        def edit_requests(partition):
            t = get_part_type()
            if not t:
                return False

            if t == parttype.root:
                size = partition.getMB()
                if size < ctx.consts.min_root_size:
                    self.warning.setText(
                        _("'Install Root' size must be larger than %s MB.") % (
                            ctx.consts.min_root_size))
                    self.warning.show()
                    return False

            # edit partition. just set the filesystem and flags.
            if state == editState and self.edit.format.isChecked():
                partition.setPartedFlags(t.parted_flags)
                partition.setFileSystemType(t.filesystem)
#                device.commit()

            try:
                ctx.partrequests.append(
                    request.MountRequest(partition, t))
            
                ctx.partrequests.append(
                    request.LabelRequest(partition, t))
                
                if self.edit.format.isChecked():
                    ctx.partrequests.append(
                        request.FormatRequest(partition, t))
                else:
                    # remove previous format requests for partition (if
                    # there are any)
                    ctx.partrequests.removeRequest(
                        partition, request.formatRequestType)
            except request.RequestException, e:
                self.warning.setText("%s" % e)
                self.warning.show()
                return False

            return True

        if t == parteddata.deviceType:
            if state == createState:
                device = self._d
                if not create_new_partition(device):
                    return False

            elif state == deleteState:
                # delete requests
                for p in self._d.getPartitions():
                    ctx.partrequests.removeRequest(p, request.mountRequestType)
                    ctx.partrequests.removeRequest(p, request.formatRequestType)
                    ctx.partrequests.removeRequest(p, request.labelRequestType)
                self._d.deleteAllPartitions()

        elif t ==  parteddata.partitionType:
            if state == createState and self._d.isExtended():
                device = self._d.getDevice()
                if not create_new_partition(device, parteddata.PARTITION_LOGICAL):
                    return False

            elif state == deleteState:
                device = self._d.getDevice()
                device.deletePartition(self._d)
                # delete requests
                ctx.partrequests.removeRequest(self._d, request.mountRequestType)
                ctx.partrequests.removeRequest(self._d, request.formatRequestType)
                ctx.partrequests.removeRequest(self._d, request.labelRequestType)

            elif state == editState:
                partition = self._d
                if not edit_requests(partition):
                    return

            elif state == resizeState:
                partition = self._d
                device = partition.getDevice()
                fs = filesystem.get_filesystem(partition.getFSName())
                
                size_mb = self.edit.size.text().toInt()[0]

                # check resize for NTFS before performing action.
                if fs.name() == "ntfs":
                    if not fs.check_resize(size_mb, partition):
                        self.warning.setText(_("ntfsresize check failed! Won't proceed action!"))
                        self.warning.show()
                        return False

                device.resizePartition(fs, size_mb, partition)

        elif t == parteddata.freeSpaceType:
            if state == createState:
                device = self._d.getDevice()
                if not create_new_partition(device):
                    return False

        else:
            raise GUIError, "unknown action called (%s)" %(self._action)

        self.hide()
        self.emit(PYSIGNAL("signalApplied"), ())

    ##
    # Cancel button clicked.
    def slotCancelClicked(self):
        self.emit(PYSIGNAL("signalCanceled"), ())


class PartEditWidgetImpl(PartEditWidget):
    def __init__(self, *args):
        apply(PartEditWidget.__init__, (self,) + args)

        self.connect(self.root, SIGNAL("toggled(bool)"),
                     self.slotRootToggled)

    def slotRootToggled(self, b):
        # allways format root partition!
        if b:
            self.format.setChecked(True)
            self.format.setEnabled(False)
        else:
            self.format.setEnabled(True)

    def setState(self, state, partition=None):
        # unset buttons
        self.root.setOn(False)
        self.home.setOn(False)
        self.swap.setOn(False)

        # enable all 
        self.root.setEnabled(True)
        self.home.setEnabled(True)
        self.swap.setEnabled(True)

        # just to (set || disable) the ones already used
        for r in ctx.partrequests.searchReqTypeIterate(request.mountRequestType):
            pt = r.partitionType()
            part = r.partition()
            for ptype, item in ((parttype.root, self.root),
                                (parttype.home, self.home),
                                (parttype.swap, self.swap)):
                if pt == ptype:
                    if partition and part == partition:
                        item.setOn(True)
                    else:
                        item.setEnabled(False)

        # State specific jobs.
        if state == editState:
            self.buttonGroup.show()
            self.format.show()
            self.format.setChecked(True)

            self.size.hide()
            self.use_available.hide()
            self.size_label.hide()

        elif state == resizeState:
            self.size.show()
            self.size_label.show()
            self.size.setValue(self.size.minValue())

            self.buttonGroup.hide()
            self.use_available.hide()
            self.format.hide()

        elif state == createState:
            self.buttonGroup.show()
            self.size.show()
            self.use_available.show()
            self.size_label.show()
            self.format.show()

            # set the first available partition type on.
            for i in (self.root, self.home, self.swap):
                if i.isEnabled():
                    i.setOn(True)
                    break

            self.size.setValue(0)
            self.format.setChecked(True)
            self.use_available.setChecked(False)
