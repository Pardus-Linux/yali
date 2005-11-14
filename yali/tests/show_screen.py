#!/usr/bin/python

import sys
sys.path.append("./yali/gui")
sys.path.append("../yali/gui")
from qt import *


app = QApplication(sys.argv)
win = QMainWindow()


module_name = sys.argv[1]
m = __import__("%s" % module_name)
w = m.Widget(win)

win.setCentralWidget(w)
win.resize(800,600)
win.show()

app.connect(app, SIGNAL("lastWindowClosed()"),
            app, SLOT("quit()"))

app.exec_loop()


