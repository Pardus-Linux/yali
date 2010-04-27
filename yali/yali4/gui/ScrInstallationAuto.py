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

from yali4.gui.ScreenWidget import ScreenWidget
from yali4.gui.Ui.autoinstallationwidget import Ui_AutoInstallationWidget
from yali4.gui.Ui.autoinstallationlistitemwidget import Ui_AutoInstallationListItemWidget
from yali4.gui.GUIException import *
from yali4.gui.installdata import *
import yali4.pisiiface
import yali4.gui.context as ctx
import yali4.sysutils

##
# Installation Choice Widget
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Choose Installation')
    desc = _('Auto or Manual installation...')
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
        self.enable_next = False
        self.isManualInstallation = False
        self.kernelType = None
        self.defaultChoice = None
        self.currentChoice = None
        self.previousChoice = None

        self.fillCollectionList()

        self.connect(self.ui.radioManual, SIGNAL("clicked()"),self.slotClickedManual)
        self.connect(self.ui.radioManual, SIGNAL("toggled(bool)"),self.slotToggleManual)
        self.connect(self.ui.radioAutomatic, SIGNAL("toggled(bool)"),self.slotToggleAutomatic)
        self.connect(self.ui.radioAutomatic, SIGNAL("clicked()"),self.slotClickedAutomatic)
        self.connect(self.ui.radioDefaultKernel, SIGNAL("toggled(bool)"),self.slotToggleDefaultKernel)
        self.connect(self.ui.radioPAEKernel, SIGNAL("toggled(bool)"),self.slotTogglePAEKernel)
        #self.connect(self.ui.radioRTKernel, SIGNAL("toggled(bool)"),self.slotToggleRTKernel)

    def fillCollectionList(self):
        self.ui.collectionList.clear()
        self.collections = yali4.pisiiface.getCollection()
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

        self.currentChoice.setChecked(Qt.Checked)

    def setKernelType(self):
        if yali4.sysutils.isLoadedKernelPAE() or yali4.sysutils.checkKernelFlags("pae"):
            self.kernelType = paeKernel
            ctx.debugger.log("Kernel Type as PAE")
        else:
            self.kernelType = defaultKernel
            ctx.debugger.log("Kernel Type as Default")

    def shown(self):
        self.toggleAll()
        self.fillCollectionList()
        self.setKernelType()
        self.toggleAll(True)

        if len(self.collections) == 0:
            self.isManualInstallation = False
            self.ui.radioManual.setEnabled(self.isManualInstallation)
            self.ui.collectionList.setEnabled(self.isManualInstallation)
            self.ui.radioAutomatic.toggle()
        elif len(self.collections) >= 1:
            self.isManualInstallation = True

        if self.kernelType == paeKernel:
            self.ui.radioPAEKernel.setEnabled(True)
            self.ui.radioPAEKernel.setChecked(True)
        else:
            self.ui.radioPAEKernel.setEnabled(False)
            self.ui.radioDefaultKernel.setChecked(True)

        ctx.mainScreen.disableNext()

        if ctx.installData.autoInstallationMethod == methodInstallAutomatic:
            self.ui.radioAutomatic.toggle()
        if ctx.installData.autoInstallationMethod == methodInstallManual:
            self.slotClickedManual()

        self.update()

    def execute(self):
        ctx.installData.autoInstallationCollection = None

        if self.ui.radioAutomatic.isChecked():
            ctx.installData.autoInstallationMethod = methodInstallAutomatic
            ctx.installData.autoInstallationCollection = self.currentChoice.collection
            ctx.debugger.log("Automatic Installation selected..")
        else:
            ctx.installData.autoInstallationMethod = methodInstallManual
            ctx.installData.autoInstallationCollection = self.currentChoice.collection
            ctx.debugger.log("Manual Installation selected..")

        if self.ui.radioDefaultKernel.isChecked():
            ctx.installData.autoInstallationKernel = defaultKernel
        elif self.ui.radioPAEtKernel.isChecked():
            ctx.installData.autoInstallationKernel = paeKernel
        #elif self.ui.radioRTKernel.isChecked():
        #    ctx.installData.autoInstallationKernel = rtKernel

        ctx.debugger.log("Trying to Install selected Packages from %s Collection with %s Type" % \
                                (ctx.installData.autoInstallationCollection.title, kernels[ctx.installData.autoInstallationKernel]))
        return True

    def slotClickedAutomatic(self):
        self.ui.radioAutomatic.setChecked(True)
        self.ui.radioManual.setChecked(False)
        self.currentChoice.setChecked(Qt.Unchecked)

    def slotClickedManual(self):
        self.currentChoice.setChecked(Qt.Checked)
        self.ui.radioManual.setChecked(True)
        self.ui.radioAutomatic.setChecked(False)
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

    #def slotToggleRTKernel(self, checked):
    #    if checked:
    #        self.kernelType = rtKernel

    def update(self):
        if self.enable_next:
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
        self.ui.labelDesc.setText(collection.description.content)
        self.ui.labelIcon.setPixmap(QtGui.QPixmap(collection.icon))
        self.connect(self.ui.checkBox, SIGNAL("stateChanged(int)"), self.slotSelectCollection)

        ctx.debugger.log("#######icon is found %s" % collection.icon)

    def setChecked(self, state):
        self.ui.checkBox.setCheckState(state)

    def slotSelectCollection(self, state):
        if state == Qt.Checked and self.parent.currentChoice != self:
            self.parent.currentChoice.setChecked(Qt.Unchecked)
            self.parent.previousChoice = self.parent.currentChoice
            self.parent.currentChoice = self
            self.parent.isManualInstallation = True
            ctx.debugger.log("Manual Installation List Item %s selected. Packages Index from %s" % (self.collection.title, self.collection.uniqueTag))

