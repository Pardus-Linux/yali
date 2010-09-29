#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.context as ctx
from yali.gui import storageGuiHelpers
from yali.gui.YaliDialog import Dialog
from yali.storage.operations import OperationResizeDevice, OperationResizeFormat
from yali.storage.formats.filesystem import FilesystemError

class ShrinkEditor:
    def __init__(self, parent, storage):
        self.storage = storage
        self.intf = parent.intf
        self.parent = parent
        self.dialog = Dialog(_("Volume to Shrink"), closeButton=False)
        self.dialog.addWidget(ShrinkWidget(self))
        self.dialog.resize(QSize(350, 150))

    def run(self):
        if self.dialog is None:
            return []

        while 1:
            rc = self.dialog.exec_()
            operations = []

            if not rc:
                self.destroy()
                return (rc, operations)

            widget = self.dialog.content

            request = widget.partitions.itemData(widget.partitions.currentIndex()).toPyObject()
            newsize = widget.sizeSpin.value()

            try:
                operations.append(OperationResizeFormat(request, newsize))
            except ValueError as e:
                self.intf.messageWindow(_("Resize FileSystem Error"),
                                        _("%(device)s: %(msg)s") %
                                        {'device': request.format.device, 'msg': e.message},
                                        type="warning", customIcon="error")
                continue

            try:
                operations.append(OperationResizeDevice(request, newsize))
            except ValueError as e:
                self.intf.messageWindow(_("Resize Device Error"),
                                              _("%(name)s: %(msg)s") %
                                               {'name': request.name, 'msg': e.message},
                                               type="warning", customIcon="error")
                continue

            # everything ok, fall out of loop
            break

        self.dialog.destroy()

        return (rc, operations)

    def destroy(self):
        if self.dialog:
            self.dialog = None


class ShrinkWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent.parent)
        self.parent = parent
        self.operations = []
        self.storage = parent.storage
        self.layout = QtGui.QGridLayout(self)
        row = 0

        label = QtGui.QLabel(_("Which partition would you like to shrink to make room for your installation?"), self)
        self.layout.addWidget(label, row, 0, 1, 2)
        row += 1

        self.partitions = storageGuiHelpers.createShrinkablePartitionMenu(self, self.storage)
        QObject.connect(self.partitions, SIGNAL("currentIndexChanged(int)"), self.updateSpin)
        self.layout.addWidget(self.partitions,row, 0, 1, 2)
        row += 1

        label = QtGui.QLabel(_("Shrink partition to size (in MB)"), self)
        self.layout.addWidget(label, row, 0, 1, 2)
        row += 1

        self.sizeSlider = QtGui.QSlider(Qt.Horizontal, self)
        self.layout.addWidget(self.sizeSlider, row, 0, 1, 1)
        self.sizeSpin = QtGui.QSpinBox(self)
        self.layout.addWidget(self.sizeSpin, row, 1, 1, 1)
        QObject.connect(self.sizeSlider, SIGNAL("valueChanged(int)"), self.sizeSpin.setValue);
        row += 1

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.layout.addWidget(self.buttonBox, row, 0, 1, 2)
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.parent.dialog.accept)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.parent.dialog.reject)

        #Force to show max, min values
        self.partitions.setCurrentIndex(0)

    def updateSpin(self, index):
        request = self.partitions.itemData(index).toPyObject()
        try:
            requestlower = long(math.ceil(request.format.minSize))
            requestupper = long(math.floor(request.format.currentSize))
        except FilesystemError, msg:
            ctx.logger.error("Shrink Widget update spin gives error:%s" % msg)
        else:
            self.sizeSpin.setMinimum(max(1, requestlower))
            self.sizeSpin.setMaximum(requestupper)
            self.sizeSlider.setMinimum(max(1, requestlower))
            self.sizeSlider.setMaximum(requestupper)
            self.sizeSpin.setValue(requestlower)
