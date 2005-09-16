# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'partitionlist.ui'
#
# Created: Cum Eyl 16 15:51:30 2005
#      by: The PyQt User Interface Compiler (pyuic) 3.13
#
# WARNING! All changes made in this file will be lost!


from qt import *


class PartitionList(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("PartitionList")

        self.setSizePolicy(QSizePolicy(1,5,0,0,self.sizePolicy().hasHeightForWidth()))

        PartitionListLayout = QGridLayout(self,1,1,11,6,"PartitionListLayout")

        layout3 = QVBoxLayout(None,0,5,"layout3")

        layout2 = QVBoxLayout(None,0,6,"layout2")

        self.textLabel1 = QLabel(self,"textLabel1")
        layout2.addWidget(self.textLabel1)

        self.listView1 = QListView(self,"listView1")
        self.listView1.addColumn(self.__tr("Column 1"))
        layout2.addWidget(self.listView1)
        layout3.addLayout(layout2)

        layout1 = QHBoxLayout(None,0,6,"layout1")

        self.createButton = QPushButton(self,"createButton")
        layout1.addWidget(self.createButton)
        spacer1 = QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        layout1.addItem(spacer1)

        self.deleteButton = QPushButton(self,"deleteButton")
        layout1.addWidget(self.deleteButton)
        spacer2 = QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        layout1.addItem(spacer2)

        self.editButton = QPushButton(self,"editButton")
        layout1.addWidget(self.editButton)
        layout3.addLayout(layout1)

        PartitionListLayout.addLayout(layout3,0,0)

        self.languageChange()

        self.resize(QSize(673,326).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("Form1"))
        self.textLabel1.setText(self.__tr("Partitions:"))
        self.listView1.header().setLabel(0,self.__tr("Column 1"))
        self.listView1.clear()
        item = QListViewItem(self.listView1,None)
        item.setText(0,self.__tr("New Item"))

        self.createButton.setText(self.__tr("Create"))
        self.deleteButton.setText(self.__tr("Delete"))
        self.editButton.setText(self.__tr("Edit"))


    def __tr(self,s,c = None):
        return qApp.translate("PartitionList",s,c)
