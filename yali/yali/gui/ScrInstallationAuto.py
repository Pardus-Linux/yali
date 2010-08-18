# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import time
import platform
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *


import yali.pisiiface
import yali.context as ctx
from yali.gui.installdata import methodInstallManual, methodInstallAutomatic, defaultKernel, paeKernel, kernels
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.autoinstallationwidget import Ui_AutoInstallationWidget
from yali.gui.Ui.autoinstallationlistitemwidget import Ui_AutoInstallationListItemWidget
from yali.gui.GUIException import *

##
# Installation Choice Widget
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Choose a Package Collection")
    icon = "iconPartition"
    help = _('''
<font size="+2">Automatic Installation</font>
<font size="+1">
<p>
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_AutoInstallationWidget()
        self.ui.setupUi(self)

        self.collections = None
        self.kernelType = None
        self.defaultChoice = None
        self.currentChoice = None
        self.previousChoice = None

        self.ui.kernelTypeGroupBox.setEnabled(False)

        self.connect(self.ui.radioManual, SIGNAL("clicked()"),self.slotClickedManual)
        self.connect(self.ui.radioManual, SIGNAL("toggled(bool)"),self.slotToggleManual)
        self.connect(self.ui.radioAutomatic, SIGNAL("toggled(bool)"),self.slotToggleAutomatic)
        self.connect(self.ui.radioAutomatic, SIGNAL("clicked()"),self.slotClickedAutomatic)
        self.connect(self.ui.radioDefaultKernel, SIGNAL("toggled(bool)"),self.slotToggleDefaultKernel)
        self.connect(self.ui.radioPAEKernel, SIGNAL("toggled(bool)"),self.slotTogglePAEKernel)

    def fillCollectionList(self):
        self.ui.collectionList.clear()
        self.collections = yali.pisiiface.getCollection()
        selectedItem=None
        for collection in self.collections:
            item = QtGui.QListWidgetItem(self.ui.collectionList)
            #item.setFlags(Qt.NoItemFlags | Qt.ItemIsEnabled)
            item.setSizeHint(QSize(48,48))
            if ctx.installData.autoInstallationCollection  == collection:
                collectionItem = CollectionListItem(self, item, collection)
                selectedItem = collectionItem
            elif collection.default:
                collectionItem = CollectionListItem(self, item, collection)
                self.defaultChoice = collectionItem
            else:
                collectionItem = CollectionListItem(self, item, collection)
            self.ui.collectionList.setItemWidget(item, collectionItem)

        if selectedItem:
            self.currentChoice = selectedItem
        elif self.defaultChoice and not selectedItem:
            self.currentChoice = self.defaultChoice
        else:
            self.currentChoice = collectionItem

        self.currentChoice.setChecked(Qt.Checked)

    def shown(self):
        self.toggleAll()
        self.fillCollectionList()
        self.toggleAll(True)

        if len(self.collections) == 0:
            self.ui.radioManual.setEnabled(False)
            self.ui.collectionList.setEnabled(False)

        ctx.mainScreen.disableNext()

        if ctx.installData.autoInstallationMethod == methodInstallManual:
            self.slotClickedManual()
        else:
            self.slotClickedAutomatic()

        if platform.machine() == "x86_64":
            self.ui.kernelTypeGroupBox.hide()
        else:
            if ctx.installData.autoInstallationKernel == paeKernel:
                self.slotTogglePAEKernel(True)
            else:
                self.slotToggleDefaultKernel(True)

        self.update()

    def execute(self):
        ctx.installData.autoInstallationCollection = None

        if self.ui.radioAutomatic.isChecked():
            ctx.installData.autoInstallationMethod = methodInstallAutomatic
            ctx.installData.autoInstallationCollection = self.defaultChoice.collection
            ctx.logger.debug("Automatic Installation selected..")
        else:
            ctx.installData.autoInstallationMethod = methodInstallManual
            ctx.installData.autoInstallationCollection = self.currentChoice.collection
            ctx.logger.debug("Manual Installation selected..")

        if self.ui.kernelTypeGroupBox.isVisible():
            if self.ui.radioPAEKernel.isChecked():
                ctx.installData.autoInstallationKernel = paeKernel
            else:
                ctx.installData.autoInstallationKernel = defaultKernel
        else:
            ctx.installData.autoInstallationKernel = defaultKernel


        ctx.logger.debug("Trying to Install selected Packages from %s Collection with %s Type" % \
                                (ctx.installData.autoInstallationCollection.title, kernels[ctx.installData.autoInstallationKernel]))
        return True

    def slotClickedAutomatic(self):
        self.ui.radioAutomatic.setChecked(True)
        self.ui.radioManual.setChecked(False)
        self.defaultChoice.setChecked(Qt.Checked)
        self.defaultChoice.setKernelType()
        self.update()

    def slotClickedManual(self):
        self.ui.radioManual.setChecked(True)
        self.ui.radioAutomatic.setChecked(False)
        if self.currentChoice:
            self.currentChoice.setChecked(Qt.Checked)
            self.currentChoice.setKernelType()
        self.update()

    def slotToggleAutomatic(self, checked):
        if checked:
            self.ui.collectionList.setEnabled(False)
        else:
            self.ui.collectionList.setEnabled(True)

    def slotToggleManual(self, checked):
        if checked:
            self.ui.collectionList.setEnabled(True)
        else:
            self.ui.collectionList.setEnabled(False)


    def slotToggleDefaultKernel(self, checked):
        if checked:
            self.kernelType = defaultKernel

    def slotTogglePAEKernel(self, checked):
        if checked:
            self.kernelType = paeKernel

    def update(self):
        if self.ui.radioAutomatic.isChecked() and self.defaultChoice:
            ctx.mainScreen.enableNext()
        elif self.ui.radioManual.isChecked() and self.currentChoice and self.currentChoice.isChecked():
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def toggleAll(self, state=False):
        widgets = ["radioAutomatic", "radioManual"]
        for widget in widgets:
            getattr(self.ui, widget).setEnabled(state)
        ctx.mainScreen.processEvents()

class CollectionListItem(QtGui.QWidget):
    def __init__(self, parent, item, collection):
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui_AutoInstallationListItemWidget()
        self.ui.setupUi(self)

        self.collection = collection
        self.parent = parent
        self.item = item
        self.ui.labelName.setText(collection.title)
        self.ui.labelDesc.setText(collection.description)
        self.ui.labelIcon.setPixmap(QtGui.QPixmap(collection.icon))
        self.connect(self.ui.checkBox, SIGNAL("stateChanged(int)"), self.slotSelectCollection)

    def setChecked(self, state):
        self.ui.checkBox.setCheckState(state)

    def isChecked(self):
        return self.ui.checkBox.isChecked()

    def setKernelType(self):
        isPAEKernelAvailable = None
        if self.parent.ui.kernelTypeGroupBox.isVisible():
            isPAEKernelAvailable = yali.pisiiface.getNeededKernel(paeKernel, self.collection.index)
            if isPAEKernelAvailable:
                self.parent.ui.kernelTypeGroupBox.setEnabled(True)
            else:
                self.parent.ui.kernelTypeGroupBox.setEnabled(False)

    def slotSelectCollection(self, state):
        if state == Qt.Checked and self.parent.currentChoice != self:
            if self.parent.currentChoice:
                self.parent.currentChoice.setChecked(Qt.Unchecked)
            self.parent.previousChoice = self.parent.currentChoice
            self.parent.currentChoice = self
        elif state == Qt.Unchecked and self.parent.currentChoice == self:
            self.parent.currentChoice = None

        self.setKernelType()
        self.parent.update()
