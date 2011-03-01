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

from PyQt4.Qt import QWidget, SIGNAL, QPixmap, Qt, QListWidgetItem, QSize, QTimeLine

import yali.pisiiface
import yali.context as ctx
from yali.gui import ScreenWidget
from yali.gui.Ui.collectionswidget import Ui_CollectionsWidget
from yali.gui.Ui.collectionitem import Ui_CollectionItem

class Widget(Ui_CollectionsWidget, QWidget, ScreenWidget):
    name = "collectionSelection"

    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.collections = None
        self.current_item = None
        self.toggled_item = None
        self.collectionList.currentItemChanged.connect(self.itemChanged)

    def fillCollections(self):
        self.collectionList.clear()
        self.collections = yali.pisiiface.getCollection()
        selected = None
        for index, collection in enumerate(self.collections):
            self.addItem(collection)
            if ctx.installData.autoCollection  == collection:
                selected = index

        if selected:
            self.current_item = self.collectionList.item(selected)
            self.collectionList.setCurrentRow(selected)

    def shown(self):
        self.fillCollections()

        if len(self.collections) == 0:
            ctx.mainScreen.enableBack()
        elif len(self.collections) == 1:
            ctx.mainScreen.slotNext()

        ctx.mainScreen.disableNext()
        self.check()

    def execute(self):
        ctx.installData.autoCollection = self.collectionList.itemWidget(self.current_item).collection
        return True

    def check(self):
        if self.current_item:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def itemChanged(self, current, previous):
        self.current_item = current
        self.check()

    def addItem(self, collection):
        item = QListWidgetItem(self.collectionList)
        item.setSizeHint(QSize(36, 50))
        self.collectionList.addItem(item)
        self.collectionList.setItemWidget(item, CollectionItem(self, collection, item))

class CollectionItem(Ui_CollectionItem, QWidget):
    def __init__(self, parent, collection, item):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.item = item
        self.collection = collection
        self.title.setText(collection.title)
        self.description.setText(collection.description)
        self.icon.setPixmap(QPixmap(collection.icon))
        self.collectionContainer.hide()
        self.detailsButton.clicked.connect(lambda: self.openDetails(item))
        self.animation = QTimeLine(1000, self)

    def openDetails(self, item):
        if not self.animation.state() == QTimeLine.NotRunning:
            return

        self.detailsButton.setEnabled(False)

        if self.parent.toggled_item:
            self.closeDetails(self.parent.toggled_item)
            if item == self.parent.toggled_item:
                self.parent.toggled_item = None
                return

        #self.animation = QTimeLine(1000, self)
        self.animation.setFrameRange(36,146)
        self.animation.frameChanged.connect(lambda x: item.setSizeHint(QSize(32, x)))
        self.animation.start()
        self.animation.finished.connect(lambda: self.detailsButton.setEnabled(True))
        self.collectionContainer.show()
        self.parent.toggled_item = item

    def closeDetails(self, item):
        animation = QTimeLine(600, self)
        animation.setFrameRange(146,50)
        animation.frameChanged.connect(lambda x: item.setSizeHint(QSize(32, x)))
        animation.start()
        animation.finished.connect(lambda: self.parent.collectionList.itemWidget(item).collectionContainer.hide())
        animation.finished.connect(lambda: self.parent.collectionList.itemWidget(item).detailsButton.setEnabled(True))
