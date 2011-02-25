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
from yali.gui.Ui.collectionselectionwidget import Ui_CollectionSelectionWidget
from yali.gui.Ui.collectionitem import Ui_CollectionItem

class Widget(QWidget, ScreenWidget):
    name = "collectionSelection"

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_CollectionSelectionWidget()
        self.ui.setupUi(self)
        self.collections = None
        self.current_choice = None

    def fillCollectionList(self):
        self.ui.collectionList.clear()
        self.collections = yali.pisiiface.getCollection()
        selected = None
        collection_item = None
        for collection in self.collections:
            item = QListWidgetItem(self.ui.collectionList)
            item.setSizeHint(QSize(48, 48))
            collection_item = CollectionListItem(self, item, collection)
            if ctx.installData.autoCollection  == collection:
                self.current_choice = collection_item
            self.ui.collectionList.setItemWidget(item, collection_item)

        if not self.current_choice:
            self.current_choice = self.ui.collectionList.itemWidget(self.ui.collectionList.item(0))

        self.current_choice.setChecked(Qt.Checked)

    def shown(self):
        self.fillCollectionList()

        if len(self.collections) == 0:
            ctx.mainScreen.enableBack()
        elif len(self.collections) == 1:
            ctx.mainScreen.slotNext()

        ctx.mainScreen.disableNext()

        self.update()

    def execute(self):
        ctx.installData.autoCollection = self.current_choice.collection

        return True

    def update(self):
        if self.current_choice and self.current_choice.isChecked():
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

class CollectionListItem(QWidget):
    def __init__(self, parent, item, collection):
        QWidget.__init__(self, parent)

        self.ui = Ui_CollectionItem()
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

    def slotSelectCollection(self, state):
        if state == Qt.Checked and self.parent.current_choice != self:
            if self.parent.current_choice:
                self.parent.current_choice.setChecked(Qt.Unchecked)
            self.parent.current_choice = self
        elif state == Qt.Unchecked and self.parent.current_choice == self:
            self.parent.current_choice = None

        self.parent.update()
