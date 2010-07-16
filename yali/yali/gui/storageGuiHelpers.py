#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.gui.context as ctx
from yali.gui.GUIAdditional import DeviceTreeItem, DriveItem
from yali.storage.formats import device_formats, get_default_filesystem_type

defaultMountPoints = ['/', '/boot', '/home', '/tmp',
                      '/usr', '/var', '/usr/local', '/opt']

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

        if not mnt in mntptlist and (mnt[0] =="/"):
            mntptlist.append(mnt)

    map(mountCombo.addItem, mntptlist)

    if (request.format.type or request.format.migrate) and \
       request.format.mountable:
        mountpoint = request.format.mountpoint
        if mountpoint:
            mountCombo.setItemText(0, mountpoint)
        else:
            mountCombo.setItemText(0, "")

    else:
        mountCombo.setItemText(0, _("<Not Applicable>"))
        mountCombo.setEnabled(False)

    return mountCombo

def createFSTypeMenu(parent, format, availablefstypes=None, ignorefs=None):
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
        formatCheckBox = QtGui.QCheckBox(_("Format As :"), parent)
        parent.layout.addWidget(formatCheckBox, row, 0, 1, 1)
        formatCheckBox.setChecked(origfs.formattable and not origfs.exists)
        rc["formatCheckBox"] = formatCheckBox
        fstypeComboBox = createFSTypeMenu(parent, origrequest.format, ignorefs=ignorefs)
        fstypeComboBox.setEnabled(formatCheckBox.isChecked())
        parent.layout.addWidget(fstypeComboBox, row, 1, 1, 1)
        rc["fstypeComboBox"] = fstypeComboBox
        QObject.connect(formatCheckBox, SIGNAL("stateChanged(int)"), parent.formatOptionCB)
        row += 1
    else:
        formatCheckBox = None
        fstypeComboBox = None


    if origfs.migratable and origfs.exists:
        migrateCheckBox = QtGui.QCheckBox(_("Migrate filesystem To :"), parent)
        parent.layout.addWidget(migrateCheckBox, row, 0, 1, 1)
        migrateCheckBox.setChecked(isEnabled(origfs.migrate))

        migtypes = origrequest.origfstype.getMigratableFSTargets()

        migratefstypeComboBox = createFSTypeMenu(parent, origfs, availablefstypes=migtypes)
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
        parent.layout.addWidget(resizeCheckBox, row, 0, 1, 1)
        resizeCheckBox.setChecked(origfs.resizable and \
                            (origfs.currentSize != origfs.targetSize) and \
                            (origfs.currentSize != 0))
        rc["resizeCheckBox"] = resizeCheckBox

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
        resizeSpinBox.setRange(reqlower, requpper)
        resizeSpinBox.setValue(value)
        parent.layout.addWidget(resizeSpinBox, row, 1, 1, 1)
        rc["resizeSpinBox"] = resizeSpinBox
        QObject.connect(resizeCheckBox, SIGNAL("stateChanged(int)"), parent.resizeOption)

        row += 1
        QObject.connect(formatCheckBox, SIGNAL("stateChanged(int)"), parent.formatOptionResize)

    row += 1

    return (row, rc)


def createAdvancedSizeOptions(parent, request):
    groupBox = QtGui.QGroupBox(_("Advanced Size Options"), parent)
    gridLayout = QtGui.QGridLayout(groupBox)
    fixedRadioButton = QtGui.QRadioButton(_("Fixed Size :"), groupBox)
    gridLayout.addWidget(fixedRadioButton, 0, 0, 1, 2)
    fillMaxsizeRadioButton = QtGui.QRadioButton(_("Fill all space up to (MB):"))
    gridLayout.addWidget(fillMaxsizeRadioButton,1, 0, 1, 2)
    fillUnlimitedRadiobutton = QtGui.QRadioButton(_("Fill to maximum allowable size"), groupBox)
    gridLayout.addWidget(fillUnlimitedRadiobutton, 2, 0, 1, 1)
    fillMaxsizeSpinBox = QtGui.QSpinBox(groupBox)
    fillMaxsizeSpinBox.setRange(1, ctx.consts.MAX_PART_SIZE)
    gridLayout.addWidget(fillMaxsizeSpinBox, 2, 1, 1, 1)
    QObject.connect(fillMaxsizeRadioButton, SIGNAL("toggled()"), parent.fillMaxSizeCB)

    fillMaxsizeSpinBox.setEnabled(True)

    if request.req_grow:
        if request.max_size:
            fillMaxsizeRadioButton.setEnabled(True)
            fillMaxsizeSpinBox.setEnabled(True)
            fillMaxsizeSpinBox.setValue(request.max_size)
        else:
            fillUnlimitedRadiobutton.setEnabled(True)
    else:
        fixedRadioButton.setEnabled(True)

    return (groupBox, fixedRadioButton, fillMaxsizeRadioButton, fillMaxsizeSpinBox)


def doUIRAIDLVMChecks(request, devicetree):
    fstype = request.fstype
    numdrives = len(devicetree.disks.keys())

    if fstype and fstype.getName() in ["physical volume (LVM)", "software RAID"]:
        if numdrives > 1 and (request.drive is None or len(request.drive) > 1):
                    return (_("Partitions of type '%s' must be constrained to "
                        "a single drive.  To do this, select the "
                        "drive in the 'Allowable Drives' checklist.")) % fstype.getName()
    return None

