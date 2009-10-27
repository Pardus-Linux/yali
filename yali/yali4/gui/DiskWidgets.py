# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *

import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

import parted
import yali4.storage
import yali4.filesystem as filesystem
import yali4.partitionrequest as request
import yali4.partitiontype as parttype
import yali4.parteddata as parteddata

import yali4.gui.context as ctx

from yali4.gui.Ui.partedit import Ui_PartEdit
from yali4.gui.GUIException import *
from yali4.gui.GUIAdditional import ResizeWidget
from yali4.gui.YaliDialog import InfoDialog

partitionTypes = [None,
                  parttype.root,
                  parttype.home,
                  parttype.swap,
                  parttype.archive]

minimumSize = 40

class DiskList(QtGui.QWidget):

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.resize(QSize(QRect(0,0,600,80).size()).expandedTo(self.minimumSizeHint()))
        self.setAutoFillBackground(False)
        self.diskCount = 1
        self.updateEnabled = True
        self.setStyleSheet("""
            QTabWidget::pane { border-top: 2px solid #FFFFFF; }
            QTabWidget::tab-bar { left: 5px; }
            QTabBar::tab { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                       stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                                       stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
                           border-top: 2px solid #C4C4C3;
                           border-bottom-color: #FFFFFF;
                           border-top-left-radius: 4px;
                           border-top-right-radius: 4px;
                           min-width: 8ex;
                           padding: 2px;
                           padding-left:4px;
                           padding-right:4px;}
            QTabBar::tab:selected,
            QTabBar::tab:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                             stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                                             stop: 0.5 #e7e7e7, stop: 1.0 #fafafa); }
            QTabBar::tab:selected { border-color: #CCC; border-bottom-color: #FFFFFF; }
            QTabBar::tab:!selected { margin-top: 2px; }
            QRadioButton::indicator { width:1px;height:1px;border-color:white; }
            QRadioButton:checked { border:6px solid rgba(255,255,255,180); }
            QSplitter::handle { background-color:rgba(255,255,255,0); }
        """)
        self.vbox = QtGui.QVBoxLayout(self)

        self.tabWidget = QtGui.QTabWidget(self)
        self.tabWidget.setAutoFillBackground(False)

        self.partEdit = PartEdit(partitionTypes)
        self.partEdit.ui.fileSystem.setVisible(False)

        self.vbox.addWidget(self.tabWidget)
        self.vbox.addWidget(self.partEdit)

        # Summary
        ctx.partSum = []
        ctx.partSum.append(_("Manual Partitioning selected."))

        # Connections
        self.connect(self.tabWidget,QtCore.SIGNAL("currentChanged(int)"),self.updatePartEdit)
        self.connect(self.partEdit.ui.formatType,QtCore.SIGNAL("currentIndexChanged(int)"),self.formatTypeChanged)
        self.connect(self.partEdit.ui.deletePartition,QtCore.SIGNAL("clicked()"),self.slotDeletePart)
        self.connect(self.partEdit.ui.resizePartition,QtCore.SIGNAL("clicked()"),self.slotResizePart)
        self.connect(self.partEdit.ui.applyTheChanges,QtCore.SIGNAL("clicked()"),self.slotApplyPartitionChanges)
        self.connect(self.partEdit.ui.resetAllChanges,QtCore.SIGNAL("clicked()"),self.resetChanges)
        self.connect(self.partEdit.ui.refreshDisks,QtCore.SIGNAL("clicked()"),self.reinitDevices)
        self.connect(self.partEdit, SIGNAL("updateTheList"),self.update)

        self.initDevices()

    def resizeEvent(self, event):
        if self.updateEnabled:
            self.update()
            self.updateEnabled = False

    ##
    # GUI Operations
    #
    def updatePartEdit(self):
        cur = self.tabWidget.currentWidget()
        if cur:
            cur.updatePartEdit()

    def reinitDevices(self):
        self.resetChanges()
        self.initDevices(force=True)
        self.update()
        self.formatTypeChanged()

    def addDisk(self, dw):
        ni = self.tabWidget.addTab(dw,dw.name)
        self.tabWidget.setTabToolTip(ni,"%s - %s" % (dw.model,dw.name))
        self.diskCount+=1

    def update(self):
        _cur = self.tabWidget.currentIndex()
        if _cur==-1: _cur = 0
        self.tabWidget.clear()
        self.diskCount = 1

        for dev in self.devs:
            try:
                ctx.debugger.log("Device Found %s" % dev.getModel())
            except:
                pass
            self.addDevice(dev)

        self.tabWidget.setCurrentIndex(_cur)
        self.updatePartEdit()
        self.checkRootPartRequest()
        self.formatTypeChanged()

    def setCurrent(self, new):
        self.tabWidget.setCurrentIndex(new)

    def checkRootPartRequest(self):
        try:
            ctx.mainScreen.disableNext()
        except:
            pass
        for req in ctx.partrequests:
            if req.partitionType() == parttype.root:
                # root partition type. can enable next
                ctx.mainScreen.enableNext()

    def formatTypeChanged(self, cur=None):
        if not cur:
            cur = self.partEdit.ui.formatType.currentIndex()
            if cur < 0:
                cur = 0

        if cur == 0:
            self.partEdit.ui.applyTheChanges.setEnabled(False)
        else:
            self.partEdit.ui.applyTheChanges.setEnabled(True)

        def forceToFormat():
            self.partEdit.ui.formatCheck.setEnabled(False)
            self.partEdit.ui.formatCheck.setChecked(True)

        def updateFSList(partitionType):
            self.partEdit.ui.fileSystemBox.clear()
            if partitionType:
                for fs in partitionType.supportedFileSystems:
                    if fs.isReadyToUse():
                        self.partEdit.ui.fileSystemBox.addItem(fs.name())

            # Force to select ext4 by default for ext3 partitions
            key = self.partEdit.currentPart.getFSName()
            if key == 'ext3' and not self.partEdit.currentPart.isFileSystemTypeChanged():
                key = 'ext4'
            fsId = self.partEdit.ui.fileSystemBox.findText(key)
            if fsId < 0:
                fsId = 0
            self.partEdit.ui.fileSystemBox.setCurrentIndex(fsId)

        updateFSList(partitionTypes[cur])

        if partitionTypes[cur] == parttype.root:
            if self.partEdit.ui.partitionSize.maximum() < ctx.consts.min_root_size and not self.partEdit.isPartitionUsed:
                self.partEdit.ui.formatType.setCurrentIndex(0)
                self.partEdit.ui.information.setText(_("'Install Root' size must be larger than %s MB.") % (ctx.consts.min_root_size))
                self.partEdit.ui.information.show()
            else:
                self.partEdit.ui.partitionSize.setMinimum(ctx.consts.min_root_size + 40)
                self.partEdit.ui.partitionSlider.setMinimum(ctx.consts.min_root_size + 40)
                forceToFormat()
        else:
            self.partEdit.ui.information.setText("")
            self.partEdit.ui.partitionSize.setMinimum(10)
            self.partEdit.ui.partitionSlider.setMinimum(10)
            self.partEdit.ui.formatCheck.setEnabled(True)

        if partitionTypes[cur] == parttype.home:
            # if selected partition has different fs for userspace, forceToFormat
            if self.partEdit.currentPart:
                if not self.partEdit.currentPart.getFSName() in filesystem.getLinuxFileSystems():
                    forceToFormat()

        if partitionTypes[cur] == parttype.swap:
            forceToFormat()

        # if selected partition is freespace no matter what we have to format.
        if self.partEdit.currentPart:
            if self.partEdit.currentPart.isFreespace():
                forceToFormat()

    def initDevices(self, force=False):
        self.devs = []
        # initialize all storage devices
        if not yali4.storage.initDevices(force):
            raise GUIException, _("Can't find a storage device!")

        self.devs = [i for i in yali4.storage.devices]

    def resetChanges(self):
        ctx.partSum = []
        yali4.storage.clearDevices()
        self.initDevices()
        ctx.partrequests.remove_all()
        self.update()

    def addDevice(self, dev):

        # get the size as human readable
        def sizeStr(mb):
            if mb > 1024:
                return _("%0.1f GB free") % long(round(mb/1024.0))
            else:
                return _("%d MB free") % mb

        # add the device to the list
        devstr = u"Disk %d (%s)" % (self.diskCount, dev.getName())
        freespace = dev.getFreeMB()
        if freespace:
            size_str = dev.getSizeStr() + "  (%s)" % sizeStr(freespace)
        else:
            size_str = dev.getSizeStr()

        diskItem = DiskItem("%s - %s" % (devstr,size_str),dev.getModel(),self.partEdit,dev.getTotalMB())
        diskItem.setData(dev)
        self.addDisk(diskItem)

        # add partitions on device
        for part in dev.getOrderedPartitionList():
            # we dont need to show fu..in extended partition
            if part.isExtended():
                continue
            if part.getMinor() != -1:
                name = _("Partition %d") % part.getMinor()
                try:
                    name = part.getFSLabel() or name
                except:
                    ctx.debugger.log("GFSL: Failed for %s, not important " % name)
            else:
                if part.getMB() < minimumSize:
                    continue
                name = _("Free Space")
            if ctx.debugger:
                ctx.debugger.log("Partition added with %s mb" % part.getMB())
            diskItem.addPartition(name, part)

        diskItem.updateSizes(self.tabWidget.width())

    ##
    # Partition Operations
    #

    def slotDeletePart(self):
        """Creates delete request for selected partition"""
        dev = self.partEdit.currentPart.getDevice()
        currentPart = self.partEdit.currentPart
        ctx.partrequests.removeRequest(currentPart, request.mountRequestType)
        ctx.partrequests.removeRequest(currentPart, request.formatRequestType)
        ctx.partrequests.removeRequest(currentPart, request.labelRequestType)
        dev.deletePartition(currentPart)

        try:
            label = currentPart.getFSLabel()
        except YaliException, e:
            label = currentPart.getName()

        _sum = {"partition":label,
                "size":currentPart.getSizeStr(),
                "device":dev.getModel()}
        ctx.partSum.append(_("Partition <b>%(partition)s (%(size)s)</b> <b>deleted</b> from device <b>%(device)s</b>.") % _sum)

        # check for last logical partition
        if dev.numberOfLogicalPartitions() == 0 and dev.getExtendedPartition():
            # if there is no more logical partition we also dont need the extended one ;)
            dev.deletePartition(dev.getExtendedPartition())

        self.update()

    def slotResizePart(self):
        """Asks for resize for selected partition"""
        dev = self.partEdit.currentPart.getDevice()
        part = self.partEdit.currentPart
        resizeWidget = ResizeWidget(dev, part, self)
        resizeWidget.show()

    def slotApplyPartitionChanges(self):
        """Creates requests for changes in selected partition"""

        t = partitionTypes[self.partEdit.ui.formatType.currentIndex()]
        t.setFileSystem(str(self.partEdit.ui.fileSystemBox.currentText()))

        if not t:
            return False

        partition = self.partEdit.currentPart
        hasReq = ctx.partrequests.searchPartTypeAndReqType(t, 1)

        if hasReq:
            if not hasReq._partition.getPath() == partition.getPath():
                self.partEdit.ui.information.setText(_("There is a request for the same Partition Type."))
                self.partEdit.ui.information.show()
                return False

        def edit_requests(partition):
            """edit partition. just set the filesystem and flags."""
            if self.partEdit.ui.formatCheck.isChecked():
                disk = partition.getDevice()
                flags = t.parted_flags

                # There must be only one bootable partition on disk
                if (parted.PARTITION_BOOT in flags) and disk.hasBootablePartition():
                    flags = list(set(flags) - set([parted.PARTITION_BOOT]))
                partition.setPartedFlags(flags)
                partition.setFileSystemType(t.filesystem)

                # If selected partition's fs is different from the old one we need to commit this
                if not partition._fsname == t.filesystem._name:
                    disk._needs_commit = True
            try:
                if self.partEdit.ui.formatCheck.isChecked():
                    _sum = {"partition":partition.getName(),
                            "fsType":t.filesystem._name}
                    ctx.partSum.append(_("Partition <b>%(partition)s</b> will be <b>formatted</b> as <b>%(fsType)s</b>.") % _sum)
                    ctx.partrequests.append(request.FormatRequest(partition, t))
                else:
                    # remove previous format requests for partition (if there are any)
                    ctx.partrequests.removeRequest(partition, request.formatRequestType)

                ctx.partrequests.append(request.MountRequest(partition, t))
                ctx.partrequests.append(request.LabelRequest(partition, t))

            except request.RequestException, e:
                self.partEdit.ui.information.setText("%s" % e)
                self.partEdit.ui.information.show()
                return False
            _sum = {"partition":partition.getName(),
                    "type":t.name}
            ctx.partSum.append(_("Partition <b>%(partition)s</b> <b>selected</b> as <b>%(type)s</b>.") % _sum)
            return True

        # Get selected Partition and the other informations from GUI
        partitionNum = self.partEdit.currentPartNum
        device = partition.getDevice()
        size = self.partEdit.ui.partitionSize.value()

        # This is a new partition request
        if partition._parted_type & parteddata.freeSpaceType:
            type = parteddata.PARTITION_PRIMARY
            extendedPartition = device.getExtendedPartition()

            # GPT Disk tables doesnt support extended partitions
            # so we need to reach maximum limit with primary partitions
            if device._disk.type.name == "gpt":
                min_primary = 4
                if device.numberOfPrimaryPartitions() == 4:
                    InfoDialog(_("GPT Disk tables does not support for extended partitions.\n" \
                                 "You need to delete one of primary partition from your disk table !"),
                       title = _("Too many primary partitions !"))
                    return
            else:
                min_primary = 1

            if partitionNum == 0:
                type = parteddata.PARTITION_PRIMARY
            elif device.numberOfPrimaryPartitions() >= min_primary and device.numberOfPrimaryPartitions() <= 3 and not extendedPartition:
                # if three primary partitions exists on disk and no more extendedPartition
                # we must create new extended one for other logical partitions
                ctx.debugger.log("There is no extended partition, Yalı will create new one")
                type = parteddata.PARTITION_EXTENDED
                p = device.addPartition(partition._partition, type, None, partition.getMB(), t.parted_flags)

                # New Fresh logical partition
                partition = device.getPartition(p.num)
                ctx.debugger.log("Yalı created new extended partition as number of %d " % p.num)
                type = parteddata.PARTITION_LOGICAL
            elif device.numberOfPrimaryPartitions() == 4 or ( device.numberOfPrimaryPartitions() == 3 and extendedPartition and not(partition._partition.type and parteddata.PARTITION_LOGICAL)):
                # if four primary partitions or
                # three primary partitions and additionaly an extendedPartition
                # exists on the disk we can't create a new primary partition
                InfoDialog(_("You need to delete one of the primary or extended(if exists) partition from your disk table !"),
                   title = _("Too many primary partitions !"))
                return

            if extendedPartition and partition._partition.type & parteddata.PARTITION_LOGICAL:
                type = parteddata.PARTITION_LOGICAL

            try:
                # Let's create the partition
                p = device.addPartition(partition._partition, type, t.filesystem, size, t.parted_flags)
            except Exception, e:
                ctx.debugger.log("Exception : %s" % e)
                InfoDialog(unicode(e), title = _("Error !"))
                return

            # Get new partition meta
            partition = device.getPartition(p.num)

            _sum = {"partition":partition.getName(),
                    "size":size,
                    "device":device.getModel(),
                    "fs":t.filesystem.name()}
            ctx.partSum.append(_("Partition <b>%(partition)s</b> <b>added</b> to device <b>%(device)s</b> with <b>%(size)s MB</b> as <b>%(fs)s</b>.") % _sum)

        # Apply edit requests
        if not edit_requests(partition):
            return False

        device.update()
        self.update()

class DiskItem(QtGui.QWidget):
    # storage.Device or partition.Partition
    _data = None

    def __init__(self, name, model, partEdit, totalSize):
        QtGui.QWidget.__init__(self,None)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)

        self.vboxlayout = QtGui.QVBoxLayout(self)
        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.hboxlayout = QtGui.QHBoxLayout()
        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)

        self.deleteAllPartitions = QtGui.QPushButton(_("Delete All Partitions"),self)
        self.hboxlayout.addWidget(self.deleteAllPartitions)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.diskGroup = QtGui.QGroupBox(self)
        self.diskGroup.setMinimumSize(QSize(570,100))
        self.diskGroup.setMaximumSize(QSize(2280,100))
        self.vboxlayout.addWidget(self.diskGroup)

        self.gridlayout = QtGui.QGridLayout(self.diskGroup)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)

        self.splinter = QtGui.QSplitter(Qt.Horizontal,self.diskGroup)
        self.splinter.setHandleWidth(2)

        self.gridlayout.addWidget(self.splinter,0,0,1,1)

        spacerItem2 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem2)

        self.connect(self.deleteAllPartitions,QtCore.SIGNAL("clicked()"),self.deleteAll)

        self.partitions = []
        self.name = name
        self.model = model
        self.totalSize = totalSize
        self.partEdit = partEdit

    def addPartition(self,name=None,data=None):

        def getFSMeta(fs_type):

            metaTypes = {"fat32":{"bgcolor":"#18D918",
                                  "fgcolor":"#000000",
                                  "icon"   :"windows"},
                         "ntfs" :{"bgcolor":"#18D918",
                                  "fgcolor":"#000000",
                                  "icon"   :"windows"},
                         "hfs+" :{"bgcolor":"#C0A39E",
                                  "fgcolor":"#000000",
                                  "icon"   :"other"},
                          "xfs" :{"bgcolor":"#EED680",
                                  "fgcolor":"#000000",
                                  "icon"   :"linux"}, 
                         "fat16":{"bgcolor":"#00FF00",
                                  "fgcolor":"#000000",
                                  "icon"   :"windows"},
                         "ext4" :{"bgcolor":"#7590AE",
                                  "fgcolor":"#FFFFFF",
                                  "icon"   :"linux"},
                         "ext3" :{"bgcolor":"#7590AE",
                                  "fgcolor":"#FFFFFF",
                                  "icon"   :"linux"},
                         "ext2" :{"bgcolor":"#9DB8D2",
                                  "fgcolor":"#FFFFFF",
                                  "icon"   :"linux"},
                     "reiserfs" :{"bgcolor":"#ADA7C8",
                                  "fgcolor":"#FFFFFF",
                                  "icon"   :"linux"},
                        "btrfs" :{"bgcolor":"#FF9955",
                                  "fgcolor":"#FFFFFF",
                                  "icon"   :"linux"},
                   "linux-swap" :{"bgcolor":"#C1665A",
                                  "fgcolor":"#FFFFFF",
                                  "icon"   :"linux"}}

            if metaTypes.has_key(fs_type):
                return metaTypes[fs_type]

            return {"bgcolor":"#FFF79E",
                    "fgcolor":"#000000",
                    "icon"   :"other"}

        # Get Partition Info
        partitionType = getPartitionType(data)
        _name = ''
        _mpoint = ''
        if partitionType:
            if partitionType == parttype.root:
                _name += "\n" + _("Pardus will install here")
                _mpoint= "[ / ]"
            elif partitionType == parttype.home:
                _name += "\n" + _("User files will store here")
                _mpoint= "[ /home ]"
            elif partitionType == parttype.swap:
                _name += "\n" + _("Swap will be here")
                _mpoint= "[ swap ]"
            elif partitionType == parttype.archive:
                _name += "\n" + _("Backup or archive files will store here")
                _mpoint= "[ /mnt/archive ]"

        # Create partition
        partition = QtGui.QRadioButton("%s%s\n%s %s" % (name, _name, data.getSizeStr(), _mpoint), self.diskGroup)

        # Modify partition
        if data._parted_type == parteddata.freeSpaceType:
            partition.setStyleSheet("background-image:none;")
        else:
            meta = getFSMeta(data.getFSName())
            if partitionType:
                icon = "parduspart"
            else:
                icon = meta["icon"]
            partition.setIcon(QtGui.QIcon(":/gui/pics/%s.png" % icon))
            partition.setIconSize(QSize(32,32))
            partition.setStyleSheet("background-color:%s;color:%s" % (meta["bgcolor"],meta["fgcolor"]))

        partition.setToolTip(_("""<b>Path:</b> %s<br>
                                  <b>Size:</b> %s<br>
                                  <b>FileSystem:</b> %s%s""") % (data.getPath(),
                                                                 data.getSizeStr(),
                                                                 data.getFSName(),
                                                                 _name.replace("\n","<br>")))

        # Add it to the disk
        self.splinter.addWidget(partition)
        self.partitions.append({"name":name,"data":data})
        self.connect(partition,QtCore.SIGNAL("clicked()"),self.updatePartEdit)

    def updatePartEdit(self):
        i=0
        # if there is just one partition left, we need to select it ..
        if len(self.partitions) == 1:
            self.splinter.widget(0).setChecked(True)
        for part in self.partitions:
            if self.splinter.widget(i).isChecked():
                self.partEdit.ui.deviceGroup.setTitle(part["name"])
                self.partEdit.currentPart = part["data"]
                self.partEdit.currentPartNum = i
                self.partEdit.updateContent()
            i+=1

    def deleteAll(self):
        for p in self._data.getPartitions():
            ctx.partrequests.removeRequest(p, request.mountRequestType)
            ctx.partrequests.removeRequest(p, request.formatRequestType)
            ctx.partrequests.removeRequest(p, request.labelRequestType)
        self._data.deleteAllPartitions()

        _sum = {"device":self._data.getModel()}
        ctx.partSum.append(_("All partitions on device <b>%(device)s</b> has been deleted.") % _sum)

        QObject.emit(self.partEdit,SIGNAL("updateTheList"))

    def setData(self, d):
        self._data = d

    def getData(self):
        return self._data

    def updateSizes(self,toolBoxWidth):
        i=0
        for part in self.partitions:
            _h = self.splinter.handle(i)
            _h.setEnabled(False)
            self.splinter.setCollapsible(i,False)

            _size = self.sizePix(part['data'].getMB(),toolBoxWidth)
            _widget = self.splinter.widget(i)
            _widget.resize(_size,70)
            if _size <= 16:
                _widget.setMinimumSize(QSize(_size,90))
                _widget.setMaximumSize(QSize(_size,100))
            else:
                _widget.setMaximumSize(QSize(_size,100))

            i+=1
        self.splinter.widget(0).setChecked(True)

    def sizePix(self,mb,toolBoxWidth):
        _p = (toolBoxWidth * mb) / self.totalSize
        if _p <= 16:
            return 16
        return _p


def getPartitionType(part, rt=1):
    """ Get partition type from request list """
    for pt in partitionTypes:
        # We use MountRequest type for search keyword
        # which is 1, defined in partitionrequest.py
        req = ctx.partrequests.searchPartTypeAndReqType(pt, rt)
        if req:
            if req.partition().getPath() == part.getPath():
                return pt

class PartEdit(QtGui.QWidget):

    currentPart = None
    currentPartNum = 0
    isPartitionUsed = False

    def __init__(self, useTypes):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_PartEdit()
        self.ui.setupUi(self)
        self.ui.formatType.clear()

        for useType in useTypes:
            if not useType:
                self.ui.formatType.addItem("")
            else:
                self.ui.formatType.addItem(useType.desc)

    def updateContent(self):
        part = self.currentPart
        self.ui.deletePartition.setVisible(True)
        self.ui.resizePartition.setVisible(True)
        self.ui.formatType.setCurrentIndex(0)
        self.ui.formatCheck.setChecked(True)

        if part._parted_type == parteddata.freeSpaceType:
            self.ui.deletePartition.setVisible(False)
            self.ui.resizePartition.setVisible(False)
            self.ui.partitionSize.setEnabled(True)
            self.ui.partitionSlider.setEnabled(True)
        else:
            self.ui.partitionSize.setEnabled(False)
            self.ui.partitionSlider.setEnabled(False)

        self.ui.deviceGroup.setTitle("%s - %s" % (self.ui.deviceGroup.title(), part.getPath()))
        self.ui.fileSystem.setText(part.getFSName())
        self.ui.partitionSize.setMaximum(part.getMB()-1)
        self.ui.partitionSlider.setMaximum(part.getMB()-1)
        self.ui.partitionSize.setValue(part.getMB()-1)
        self.ui.information.setText("")
        self.ui.partitionSize.setMinimum(minimumSize)
        self.ui.partitionSlider.setMinimum(minimumSize)

        # We must select formatType after GUI update
        partitionType = getPartitionType(part)
        if partitionType:
            self.isPartitionUsed = True
            for i in range(len(partitionTypes)):
                if partitionTypes[i] == partitionType:
                    self.ui.formatType.setCurrentIndex(i)
            key = part.getFSName()
            if part.getFSName() == 'linux-swap':
                key = 'swap'
            self.ui.fileSystemBox.setCurrentIndex(self.ui.fileSystemBox.findText(key))
        else:
            self.isPartitionUsed = False

        self.ui.resizePartition.setVisible(part.isResizable() and not self.isPartitionUsed)

        isFormatChecked = getPartitionType(part,0)
        if isFormatChecked:
            self.ui.formatCheck.setChecked(True)
        else:
            self.ui.formatCheck.setChecked(False)

