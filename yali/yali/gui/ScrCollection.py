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

import platform
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QPixmap, Qt, QListWidgetItem, QSize

import yali.pisiiface
import yali.context as ctx
from yali.gui import ScreenWidget
from yali.gui.Ui.autoinstallationwidget import Ui_AutoInstallationWidget
from yali.gui.Ui.autoinstallationlistitemwidget import Ui_AutoInstallationListItemWidget

class Widget(QWidget, ScreenWidget):
    name = "collectionSelection"

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_AutoInstallationWidget()
        self.ui.setupUi(self)

        self.collections = None
        self.kernel_type = None
        self.default_choice = None
        self.current_choice = None

        self.ui.kernelTypeGroupBox.setEnabled(False)

        self.connect(self.ui.radioManual, SIGNAL("clicked()"), self.slotClickedManual)
        self.connect(self.ui.radioManual, SIGNAL("toggled(bool)"), self.slotToggleManual)
        self.connect(self.ui.radioAutomatic, SIGNAL("toggled(bool)"), self.slotToggleAutomatic)
        self.connect(self.ui.radioAutomatic, SIGNAL("clicked()"), self.slotClickedAutomatic)
        self.connect(self.ui.radioDefaultKernel, SIGNAL("toggled(bool)"), self.slotToggleDefaultKernel)
        self.connect(self.ui.radioPAEKernel, SIGNAL("toggled(bool)"), self.slotTogglePAEKernel)

    def fillCollectionList(self):
        self.ui.collectionList.clear()
        self.collections = yali.pisiiface.getCollection()
        selected = None
        collection_item = None
        for collection in self.collections:
            item = QListWidgetItem(self.ui.collectionList)
            #item.setFlags(Qt.NoItemFlags | Qt.ItemIsEnabled)
            item.setSizeHint(QSize(48, 48))
            if ctx.installData.autoInstallationCollection  == collection:
                collection_item = CollectionListItem(self, item, collection)
                selected = collection_item
            elif collection.default:
                collection_item = CollectionListItem(self, item, collection)
                self.default_choice = collection_item
            else:
                collection_item = CollectionListItem(self, item, collection)
            self.ui.collectionList.setItemWidget(item, collection_item)

        if selected:
            self.current_choice = selected
        elif self.default_choice and not selected:
            self.current_choice = self.default_choice
        else:
            self.current_choice = collection_item

        self.current_choice.setChecked(Qt.Checked)

    def shown(self):
        self.toggleAll()
        self.fillCollectionList()
        self.toggleAll(True)

        if len(self.collections) == 0:
            self.ui.radioManual.setEnabled(False)
            self.ui.collectionList.setEnabled(False)

        ctx.mainScreen.disableNext()

        if ctx.installData.autoInstallationMethod == ctx.methodInstallManual:
            self.slotClickedManual()
        else:
            self.slotClickedAutomatic()

        if platform.machine() == "x86_64":
            self.ui.kernelTypeGroupBox.hide()
        else:
            if ctx.installData.autoInstallationKernel == ctx.paeKernel:
                self.slotTogglePAEKernel(True)
            else:
                self.slotToggleDefaultKernel(True)

        self.update()

    def execute(self):
        ctx.installData.autoInstallationCollection = None

        if self.ui.radioAutomatic.isChecked():
            ctx.installData.autoInstallationMethod = ctx.methodInstallAutomatic
            ctx.installData.autoInstallationCollection = self.default_choice.collection
            ctx.logger.debug("Automatic Installation selected..")
        else:
            ctx.installData.autoInstallationMethod = ctx.methodInstallManual
            ctx.installData.autoInstallationCollection = self.current_choice.collection
            ctx.logger.debug("Manual Installation selected..")

        if self.ui.kernelTypeGroupBox.isVisible():
            if self.ui.radioPAEKernel.isChecked():
                ctx.installData.autoInstallationKernel = ctx.paeKernel
            else:
                ctx.installData.autoInstallationKernel = ctx.defaultKernel
        else:
            ctx.installData.autoInstallationKernel = ctx.defaultKernel


        ctx.logger.debug("Trying to Install selected Packages from %s Collection with %s Type" % \
                                (ctx.installData.autoInstallationCollection.title, ctx.kernels[ctx.installData.autoInstallationKernel]))
        return True

    def slotClickedAutomatic(self):
        self.ui.radioAutomatic.setChecked(True)
        self.ui.radioManual.setChecked(False)
        self.default_choice.setChecked(Qt.Checked)
        self.default_choice.setKernelType()
        self.update()

    def slotClickedManual(self):
        self.ui.radioManual.setChecked(True)
        self.ui.radioAutomatic.setChecked(False)
        if self.current_choice:
            self.current_choice.setChecked(Qt.Checked)
            self.current_choice.setKernelType()
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
            self.kernel_type = ctx.defaultKernel

    def slotTogglePAEKernel(self, checked):
        if checked:
            self.kernel_type = ctx.paeKernel

    def update(self):
        if self.ui.radioAutomatic.isChecked() and self.default_choice:
            ctx.mainScreen.enableNext()
        elif self.ui.radioManual.isChecked() and self.current_choice and self.current_choice.isChecked():
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def toggleAll(self, state=False):
        widgets = ["radioAutomatic", "radioManual"]
        for widget in widgets:
            getattr(self.ui, widget).setEnabled(state)
        ctx.mainScreen.processEvents()

class CollectionListItem(QWidget):
    def __init__(self, parent, item, collection):
        QWidget.__init__(self, parent)

        self.ui = Ui_AutoInstallationListItemWidget()
        self.ui.setupUi(self)

        self.collection = collection
        self.parent = parent
        self.item = item
        self.ui.labelName.setText(collection.title)
        self.ui.labelDesc.setText(collection.description)
        self.ui.labelIcon.setPixmap(QPixmap(collection.icon))
        self.connect(self.ui.checkBox, SIGNAL("stateChanged(int)"), self.slotSelectCollection)

    def setChecked(self, state):
        self.ui.checkBox.setCheckState(state)

    def isChecked(self):
        return self.ui.checkBox.isChecked()

    def setKernelType(self):
        pae_available = None
        if self.parent.ui.kernelTypeGroupBox.isVisible():
            pae_available = yali.pisiiface.getNeededKernel(ctx.paeKernel, self.collection.index)
            if pae_available:
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


