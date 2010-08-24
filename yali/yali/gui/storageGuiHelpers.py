#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.context as ctx
from yali.storage.formats import device_formats, get_default_filesystem_type

defaultMountPoints = ['/', '/boot', '/home', '/tmp',
                      '/usr', '/var', '/usr/local', '/opt']

class DriveItem(QtGui.QListWidgetItem):
    def __init__(self, parent, text, drive):
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self._drive = drive

    @property
    def drive(self):
        return self._drive



def createMountpointMenu(parent, request, excludeMountPoints=[]):

    mountCombo = QtGui.QComboBox(parent)
    mountCombo.setEditable(True)

    mntptlist = []
    label = getattr(request.format, "label", None)
    if request.exists and label and label.startswith("/"):
        mntptlist.append(label)
        idx = 0

    for mnt in defaultMountPoints:
        if mnt in excludeMountPoints:
            continue

        if not (mnt in mntptlist) and (mnt[0] =="/"):
            mntptlist.append(mnt)

    map(mountCombo.addItem, mntptlist)

    if (request.format.type or request.format.migrate) and request.format.mountable:
        mountpoint = request.format.mountpoint
        if mountpoint:
            if mountpoint in mntptlist:
               mountCombo.setCurrentIndex(mountCombo.findText(mountpoint))
            else:
                mountCombo.insertItem(0, mountpoint)
    else:
        mountCombo.setItemText(0, _("<Not Applicable>"))
        mountCombo.setEnabled(False)

    return mountCombo

def createFSTypeMenu(parent, format, mountCombo, availablefstypes=None, ignorefs=None):
    fstypeCombo = QtGui.QComboBox(parent)

    if availablefstypes:
        names = availablefstypes
    else:
        names = device_formats.keys()

    if format and format.supported and format.formattable:
        default = format.type
    else:
        default = get_default_filesystem_type()

    index = 0
    for i, name in enumerate(names):
        format = device_formats[name]()
        if not format.supported:
            continue

        if ignorefs and name in ignorefs:
            continue

        if format.formattable:
            fstypeCombo.addItem(name)
            if default == name:
                defindex = i
                defismountable = format.mountable
            i = i + 1

    fstypeCombo.setCurrentIndex(defindex)

    if parent.fstypechangeCB and mountCombo:
        QObject.connect(fstypeCombo, SIGNAL("currentIndexChanged(int)"), parent.fstypechangeCB)

    if mountCombo:
        QObject.connect(mountCombo, SIGNAL("currentIndexChanged(int)"), parent.mountptchangeCB)

    return fstypeCombo

def createAllowedDrivesList(parent, disks, requestDrives, selectDrives=True, disallowDrives=[]):
    driveList = QtGui.QListWidget(parent)

    createAllowedDrives(disks, requestDrives, driveList, selectDrives=selectDrives, disallowDrives=disallowDrives)

    return driveList


def createAllowedDrives(disks, requestDrives=None, driveList=None, selectDrives=True, disallowDrives=[]):
    driveList.clear()
    for disk in disks:
        selected = 0
        if selectDrives:
            if requestDrives:
                if disk.name in requestDrives:
                    selected = 2
            else:
                if drive not in disallowDrives:
                    selected = 2

        sizestr = "%8.0f MB" % disk.size
        driveItem = DriveItem(driveList, sizestr, disk)
        driveItem.setCheckState(selected)
        if len(disks) < 2:
            driveList.setEnabled(False)
        else:
            driveList.setEnabled(True)

def createPreExistFSOption(parent, origrequest, row, mountcombo, storage, ignorefs=[]):
    """ createPreExistFSOptionSection: given inputs for a preexisting partition,
        create a section that will provide format and migrate options

        Returns the value of row after packing into the maintable,
        and a dictionary consistenting of:
           formatcb      - checkbutton for 'format as new fs'
           fstype        - part of format fstype menu
           fstypeMenu    - part of format fstype menu
           resizecb      - checkbutton for 'resize fs'
           resizesb      - spinbutton with resize target
    """
    rc = {}
    origfs = origrequest.format
    if origfs.formattable or not origfs.type:
        formatCheckBox = QtGui.QCheckBox(_("Format as :"), parent)
        parent.layout.addWidget(formatCheckBox, row, 0, 1, 1)
        formatCheckBox.setChecked(origfs.formattable and not origfs.exists)

        fstypeComboBox = createFSTypeMenu(parent, origrequest.format, mountcombo, ignorefs=ignorefs)
        fstypeComboBox.setEnabled(formatCheckBox.isChecked())
        parent.layout.addWidget(fstypeComboBox, row, 1, 1, 1)

        rc["formatCheckBox"] = formatCheckBox
        rc["fstypeComboBox"] = fstypeComboBox

        QObject.connect(formatCheckBox, SIGNAL("stateChanged(int)"), parent.formatOptionCB)

        row += 1
    else:
        formatCheckBox = None
        fstypeComboBox = None


    if origfs.migratable and origfs.exists:
        migrateCheckBox = QtGui.QCheckBox(_("Migrate filesystem To :"), parent)
        if formatCheckBox  is not None:
            migrateCheckBox.setChecked(origfs.migrate and (not formatCheckBox.isChecked()))
        else:
            migrateCheckBox.setChecked(origfs.migrate)

        migtypes = [origfs.migrationTarget]

        parent.layout.addWidget(migrateCheckBox, row, 0, 1, 1)
        migratefstypeComboBox = createFSTypeMenu(parent, origfs, None, availablefstypes=migtypes)
        migratefstypeComboBox.setEnabled(migrateCheckBox.isChecked())
        parent.layout.addWidget(migratefstypeComboBox, row, 1, 1, 1)
        rc["migrateCheckBox"] = migrateCheckBox
        rc["migfstypeComboBox"] = migratefstypeComboBox

        QObject.connect(migrateCheckBox, SIGNAL("stateChanged(int)"), parent.formatOptionCB)

        row += 1
    else:
        migrateCheckBox = None
        migfstypeCombo = None


    if origrequest.resizable and origfs.exists:
        resizeCheckBox = QtGui.QCheckBox(_("Resize :"), parent)
        resizeCheckBox.setChecked(origfs.resizable and \
                            (origfs.currentSize != origfs.targetSize) and \
                            (origfs.currentSize != 0))


        if origrequest.targetSize is not None:
            value = origrequest.targetSize
        else:
            value = origrequest.size

        reqlower = 1
        requpper = origrequest.maxSize
        if origfs.exists:
            reqlower = origrequest.minSize

            if origrequest.type == "partition":
                geomsize = origrequest.partedPartition.geometry.getSize(unit="MB")
                if (geomsize != 0) and (requpper > geomsize):
                    requpper = geomsize

        resizeSpinBox = QtGui.QSpinBox(parent)
        resizeSpinBox.setMinimum(reqlower)
        resizeSpinBox.setMaximum(requpper)
        resizeSpinBox.setValue(value)

        parent.layout.addWidget(resizeCheckBox, row, 0, 1, 1)
        parent.layout.addWidget(resizeSpinBox, row, 1, 1, 1)

        QObject.connect(resizeCheckBox, SIGNAL("stateChanged(int)"), parent.resizeOption)
        QObject.connect(formatCheckBox, SIGNAL("stateChanged(int)"), parent.formatOptionResize)

        rc["resizeCheckBox"] = resizeCheckBox
        rc["resizeSpinBox"] = resizeSpinBox
        row += 1

    row += 1

    return (row, rc)


def createAdvancedSizeOptions(parent, request):
    groupBox = QtGui.QGroupBox(_("Advanced Size Options"), parent)
    gridLayout = QtGui.QGridLayout(groupBox)
    fixedRadioButton = QtGui.QRadioButton(_("Fixed Size :"), groupBox)
    fillUnlimitedRadiobutton = QtGui.QRadioButton(_("Fill to maximum allowable size"), groupBox)
    fillMaxsizeRadioButton = QtGui.QRadioButton(_("Fill all space up to (MB):"))
    fillMaxsizeSpinBox = QtGui.QSpinBox(groupBox)
    fillMaxsizeSpinBox.setMaximum(ctx.consts.MAX_PART_SIZE)
    QObject.connect(fillMaxsizeRadioButton, SIGNAL("toggled(bool)"), lambda x: fillMaxsizeSpinBox.setEnabled(x))

    fillMaxsizeSpinBox.setEnabled(False)

    if request.req_grow:
        if request.req_max_size:
            fillMaxsizeRadioButton.setChecked(True)
            fillMaxsizeSpinBox.setEnabled(True)
            fillMaxsizeSpinBox.setValue(request.req_max_size)
        else:
            fillUnlimitedRadiobutton.setChecked(True)
    else:
        fixedRadioButton.setChecked(True)

    gridLayout.addWidget(fixedRadioButton, 0, 0, 1, 2)
    gridLayout.addWidget(fillMaxsizeRadioButton, 1, 0, 1, 1)
    gridLayout.addWidget(fillMaxsizeSpinBox, 1, 1, 1, 1)
    gridLayout.addWidget(fillUnlimitedRadiobutton, 2, 0, 1, 2)

    return (groupBox, fixedRadioButton, fillMaxsizeRadioButton, fillMaxsizeSpinBox)
