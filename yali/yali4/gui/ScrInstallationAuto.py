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
        self.selectedKernelType = None
        self.selectedCollection = None
        self.defaultKernelType = None
        self.defaultCollection = None
        self.enable_next = False
        self.isManualInstallation = False
        self.lastChoice = None

        self.fillCollectionList()

        #if not self.ui.collectionList.count():
        #    raise YaliExceptionInfo, _("It seems that you don't have the collection of packages for Pardus installation.")

        self.connect(self.ui.radioManual, SIGNAL("clicked()"),self.slotClickedManual)
        self.connect(self.ui.radioManual, SIGNAL("toggled(bool)"),self.slotToggleManual)
        self.connect(self.ui.radioAutomatic, SIGNAL("toggled(bool)"),self.slotToggleAutomatic)
        self.connect(self.ui.radioAutomatic, SIGNAL("clicked()"),self.slotClickedAutomatic)
        self.connect(self.ui.radioDefaultKernel, SIGNAL("toggled(bool)"),self.slotToggleDefaultKernel)
        self.connect(self.ui.radioPAEKernel, SIGNAL("toggled(bool)"),self.slotTogglePAEKernel)
        #self.connect(self.ui.collectionList, SIGNAL("currentItemChanged(QListWidgetItem *, QListWidgetItem *)"),self.slotCollectionItemChanged)

    def fillCollectionList(self):
        self.ui.collectionList.clear()
        for collection in yali4.pisiiface.getCollection():
            item = QtGui.QListWidgetItem(self.ui.collectionList)
            item.setFlags(Qt.NoItemFlags | Qt.ItemIsEnabled)
            item.setSizeHint(QSize(48,48))
            collectionItem = CollectionListItem(collection, self, item)
            self.ui.collectionList.setItemWidget(item, collectionItem)

        self.collections = yali4.pisiiface.getCollection()
        for collection in self.collections:
            if collection.default:
                self.defaultCollection = collection

        self.ui.collectionList.setCurrentRow(0)

    def getLoadedKernelType(self):
        pass

    def shown(self):
        # scan partitions for resizing
        self.toggleAll()
        self.fillCollectionList()
        self.toggleAll(True)

        if len(self.collections) == 0:
            self.isManualInstallation = False
            self.ui.radioManual.setEnabled(self.isManualInstallation)
            self.ui.radioAutomatic.toggle()
        elif len(self.collections) >= 1:
            self.isManualInstallation = True
            self.selectedCollection = self.defaultCollection

        if sysutils.isLoadedKernelPAE() or sysutils.checkKernelFlags("pae"):
            self.radioPAEKernel.setEnabled(True)
        else:
            self.radioPAEKernel.setEnabled(False)

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
            ctx.installData.autoInstallationCollection = self.defaultCollection
            ctx.debugger.log("Automatic Installation selected..")
        else:
            ctx.installData.autoInstallationMethod = methodInstallManual
            ctx.installData.autoInstallationCollection = self.selectedCollection
            ctx.debugger.log("Manual Installation selected..")

        ctx.debugger.log("Trying to Install selected Packages from %s Collection" % ctx.installData.autoInstallationCollection.title)
        return True

    #def slotCollectionItemChanged(self, current, previous):
    #    if current:
    #        self.collection = self.ui.collectionList.itemWidget(current).collection
    #        ctx.debugger.log("Installation collection selected as %s" % self.collection.uniqueTag)

    def slotClickedAutomatic(self):
        self.ui.radioAutomatic.setChecked(True)
        self.ui.radioManual.setChecked(False)
        #ctx.installData.autoInstallationMethod = methodInstallAutomatic
        self.selectedCollection = self.defaultCollection
        self.collectionList.itemWidget(self.lastChoice).ui.checkToggler.setChecked(False)
        #self.setAutoExclusives(False)
        #self.lastChoice.setChecked(True)

    def slotClickedManual(self):
        self.ui.radioManual.setChecked(True)
        self.ui.radioAutomatic.setChecked(False)
        #self.setAutoExclusives(False)
        #ctx.installData.autoInstallationMethod = methodInstallManual
        self.enable_next = True
        self.update()

    def slotToggleAutomatic(self, checked):
        if checked:
            self.ui.collectionList.setEnabled(False)
        else:
            self.ui.collectionList.setEnabled(True)

        #self.ui.radioAutomatic.setChecked(True)
        #self.ui.radioManual.setChecked(False)

    def slotToggleManual(self, checked):
        if checked:
            self.ui.collectionList.setEnabled(True)
        else:
            self.ui.collectionList.setEnabled(False)
        #self.ui.radioAutomatic.setChecked(False)
        #self.ui.collectionList.setEnabled(True)

    def slotToggleDefaultKernel(self, checked):
        if checked:
            self.defaultKernelType = ctx.installdata.defaultKernel

    def slotTogglePAEKernel(self, checked):
        if checked:
            self.defaultKernelType = ctx.installdata.paeKernel


#    def setAutoExclusives(self, val=True):
#        self.ui.collectionList.setEnabled(val)
#        self.ui.radioAutomatic.setAutoExclusive(val)
#        self.ui.radioManual.setAutoExclusive(val)
#        if not val:
#            self.slotToggleManual(True)
#        else:
#            self.slotToggleAutomatic(True)

    def update(self):
        if self.ui.radioManual.isChecked():
            self.enable_next = True
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
    def __init__(self, collection, parent, item):
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui_AutoInstallationListItemWidget()
        self.ui.setupUi(self)

        self.collection = collection
        self.parent = parent
        self.item = item
        self.ui.labelName.setText(collection.title)
        self.ui.labelDesc.setText(collection.description.content)
        self.ui.labelIcon.setPixmap(QtGui.QPixmap(collection.icon))

        self.connect(self.ui.checkToggler, SIGNAL("clicked()"), self.slotToggleCollection)


    def slotToggleCollection(self):
        if self.ui.checkToggler.isChecked():
            self.parent.selectedCollection = self.collection
            self.parent.lastChoice = self.item
            self.parent.isManualInstallation = True
            ctx.debugger.log("Manual Install selected Packages from %s Collection as %s" % (self.collection.uniqueTag, self.collection.title))

