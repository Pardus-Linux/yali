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


import os
import codecs
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *
import yali.gui.context as ctx
from yali.postinstall import *
from yali.exception import *
from yali.gui.GUIException import *
from yali.gui.YaliDialog import InfoDialog
from yali.gui.Ui.partresize import Ui_PartResizeWidget
from yali.gui.Ui.autopartquestion import Ui_autoPartQuestion
from yali.gui.Ui.connectionlist import Ui_connectionWidget

class ResizeWidget(QtGui.QWidget):

    def __init__(self, dev, part, rootWidget):
        QtGui.QWidget.__init__(self, ctx.mainScreen)
        self.ui = Ui_PartResizeWidget()
        self.ui.setupUi(self)
        self.rootWidget = rootWidget
        self.setStyleSheet("""
                 QSlider::groove:horizontal {
                     border: 1px solid #999999;
                     height: 12px;
                     background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                     margin: 2px 0;
                 }

                 QSlider::handle:horizontal {
                     background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                     border: 1px solid #5c5c5c;
                     width: 18px;
                     margin: 0 0;
                     border-radius: 2px;
                 }

                QFrame#mainFrame {
                    background-image: url(:/gui/pics/transBlack.png);
                    border: 1px solid #BBB;
                    border-radius:8px;
                }

                QWidget#PartResizeWidget {
                    background-image: url(:/gui/pics/trans.png);
                }
        """)

        self.resize(ctx.mainScreen.size())
        self.dev = dev
        self.part = part
        minSize = self.part.getMinResizeMB() + 40

        if minSize == 0:
            self.ui.resizeMB.setVisible(False)
            self.ui.resizeMBSlider.setVisible(False)
            self.ui.resizeButton.setVisible(False)
            self.ui.label.setText(_("""<p><span style="color:#FFF"><b>It seems that this partition is not ready for resizing.</b></span></p>"""))
        else:
            maxSize = self.part.getMB()
            self.ui.resizeMB.setMaximum(maxSize)
            self.ui.resizeMBSlider.setMaximum(maxSize)
            self.ui.resizeMB.setMinimum(minSize)
            self.ui.resizeMBSlider.setMinimum(minSize)
            self.connect(self.ui.resizeButton, SIGNAL("clicked()"), self.slotResize)

        self.connect(self.ui.cancelButton, SIGNAL("clicked()"), self.hide)

    def slotResize(self):
        self.hide()
        ctx.yali.info.updateAndShow(_("Resizing to %s MB...") % (self.ui.resizeMB.value()))
        ctx.debugger.log("Resize started on partition %s " % self.part.getPath())
        QTimer.singleShot(500,self.res)

    def res(self):
        resizeTo = int(self.ui.resizeMB.value())
        try:
            self.dev.resizePartition(self.part._fsname, resizeTo,self.part)
        except FSCheckError, message:
            InfoDialog(unicode(message), title = _("Filesystem Error"))
            return

        _sum = {"partition":self.part.getName(),
                "currentSize":self.part.getMB(),
                "resizeTo":resizeTo,
                "fs":self.part._fsname}
        ctx.partSum.append(_("Partition <b>%(partition)s</b> (%(fs)s) has been resized to <b>%(resizeTo)s MB</b> (Old size: %(currentSize)s MB)") % _sum)

        self.rootWidget.update()
        ctx.yali.info.hide()

class AutoPartQuestionWidget(QtGui.QWidget):

    def __init__(self, rootWidget, partList):
        QtGui.QWidget.__init__(self, ctx.mainScreen)
        self.ui = Ui_autoPartQuestion()
        self.ui.setupUi(self)
        self.setStyleSheet("""
                QFrame#mainFrame {
                    background-image: url(:/gui/pics/transBlack.png);
                    border: 1px solid #BBB;
                    border-radius:8px;
                }
                QWidget#autoPartQuestion {
                    background-image: url(:/gui/pics/trans.png);
                }
        """)

        self.rootWidget = rootWidget

        self.connect(self.ui.bestChoice, SIGNAL("clicked()"), self.slotDisableList)
        self.connect(self.ui.cancelButton, SIGNAL("clicked()"), self.slotCancelSelected)
        self.connect(self.ui.userChoice, SIGNAL("clicked()"), self.slotEnableList)
        self.connect(self.ui.useSelectedButton, SIGNAL("clicked()"), self.slotUseSelected)

        for part in partList:
            pi = PartitionItem(self.ui.partition_list, part)

        self.ui.partition_list.setCurrentRow(0)
        self.ui.bestChoice.toggle()
        self.slotDisableList()
        self.resize(ctx.mainScreen.size())

    def slotEnableList(self):
        self.ui.partition_list.setEnabled(True)

    def slotDisableList(self):
        self.rootWidget.autoPartPartition = self.ui.partition_list.item(0).getPartition()
        self.ui.partition_list.setEnabled(False)

    def slotUseSelected(self):
        self.hide()
        if self.ui.partition_list.isEnabled():
            self.rootWidget.autoPartPartition = self.ui.partition_list.currentItem().getPartition()
        ctx.mainScreen.processEvents()
        self.rootWidget.execute_(True)

    def slotCancelSelected(self):
        self.hide()
        ctx.mainScreen.enableNext()


class DriveItem(QtGui.QListWidgetItem):
    def __init__(self, parent, text, drive):
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self._drive = drive

    @property
    def drive(self):
        return self._drive

class DeviceTreeItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent, device=None):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        self.device = device

    def setDevice(self, device):
        self.device = device

    def setName(self, device):
        self.setText(0, device)

    def setMountpoint(self, mountpoint):
        self.setText(1, mountpoint)

    def setLabel(self, label):
        self.setText(2, label)

    def setType(self, type):
        self.setText(3, type)

    def setFormattable(self, formattable):
        self.setCheckState(4, formattable)

    def setFormat(self, format):
        self.setCheckState(5, format)

    def setSize(self, size):
        self.setText(6, size)

class DeviceItem(QtGui.QListWidgetItem):
    def __init__(self, parent, dev):
        self.text = u"%s on %s (%s)" %(dev.getModel(),
                                       dev.getPath(),
                                       dev.getSizeStr())
        QtGui.QListWidgetItem.__init__(self, self.text, parent)
        self._dev = dev

    def setBootable(self):
        self.setText(_("%s (Boot Disk)" % self.text))

    def getDevice(self):
        return self._dev

class PartItem(QtGui.QListWidgetItem):
    def __init__(self, parent, partition, label, icon):
        QtGui.QListWidgetItem.__init__(self, QtGui.QIcon(":/gui/pics/%s.png" % icon), label, parent)
        self._part = partition

    def getPartition(self):
        return self._part

class ConnectionItem(QtGui.QListWidgetItem):
    def __init__(self, parent, connection, package):
        QtGui.QListWidgetItem.__init__(self, QtGui.QIcon(":/gui/pics/%s.png" % package), connection, parent)
        self._connection = [connection, package]

    def getConnection(self):
        return self._connection[0]

    def getPackage(self):
        return self._connection[1]

    def connect(self):
        connectTo(self.getPackage(), self.getConnection())

class ConnectionWidget(QtGui.QWidget):

    def __init__(self, rootWidget):
        QtGui.QWidget.__init__(self, ctx.mainScreen)
        self.ui = Ui_connectionWidget()
        self.ui.setupUi(self)
        self.setStyleSheet("""
                QFrame#mainFrame {
                    background-image: url(:/gui/pics/transBlack.png);
                    border: 1px solid #BBB;
                    border-radius:8px;
                }
                QWidget#autoPartQuestion {
                    background-image: url(:/gui/pics/trans.png);
                }
        """)

        self.rootWidget = rootWidget
        self.needsExecute = False
        self.connect(self.ui.buttonCancel, SIGNAL("clicked()"), self.hide)
        self.connect(self.ui.buttonConnect, SIGNAL("clicked()"), self.slotUseSelected)

        self.connections = getConnectionList()
        if self.connections:
            for package in self.connections.keys():
                for connection in self.connections[package]:
                    ci = ConnectionItem(self.ui.connectionList, unicode(str(connection)), package)

            self.ui.connectionList.setCurrentRow(0)
            self.resize(ctx.mainScreen.size())

    def slotUseSelected(self):
        current = self.ui.connectionList.currentItem()
        if current:
            ctx.yali.info.updateAndShow(_("Connecting to network %s...") % current.getConnection())

            try:
                ret = current.connect()
            except:
                ret = True
                self.rootWidget.ui.labelStatus.setText(_("Connection failed"))
                ctx.yali.info.updateAndShow(_("Connection failed"))

            if not ret:
                self.rootWidget.ui.labelStatus.setText(_("Connected"))
                ctx.yali.info.updateAndShow(_("Connected"))

            self.hide()
            ctx.mainScreen.processEvents()
            ctx.yali.info.hide()

            if self.needsExecute:
                self.rootWidget.execute_(True)


class TextBrowser(QtGui.QTextBrowser):

    def __init__(self, *args):
        apply(QtGui.QTextBrowser.__init__, (self,) + args)

        self.setStyleSheet("background:white;color:black;")

        try:
            self.setText(codecs.open(self.load_file(), "r", "UTF-8").read())
        except Exception, e:
            raise GUIException, e

    def load_file(self):
        pass

class Gpl(TextBrowser):

    def load_file(self):
        f = os.path.join(ctx.consts.source_dir, "license/license-" + ctx.consts.lang + ".txt")

        if not os.path.exists(f):
            f = os.path.join(ctx.consts.source_dir, "license/license-en.txt")
        if os.path.exists(f):
            return f
        raise GUIException, _("License text could not be found.")

class ReleaseNotes(TextBrowser):

    def load_file(self):
        rel_path = os.path.join(ctx.consts.source_dir,"release-notes/releasenotes-" + ctx.consts.lang + ".html")

        if not os.path.exists(rel_path):
            rel_path = os.path.join(ctx.consts.source_dir, "release-notes/releasenotes-en.html")
        if os.path.exists(rel_path):
            return rel_path
        raise GUIException, _("Release notes could not be loaded.")
