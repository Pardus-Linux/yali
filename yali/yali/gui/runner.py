# -*- coding: utf-8 -*-

import sys
from qt import *


import YaliWindow
# screens
# FIXME
# I haven't forget the localization part, just left it for later.
# import Welcome
# import Partitioning
# import InstallSystem
# import SetupUsers
# import SetupBootloader


##
# Runner creates main GUI components for installation...
class Runner:

    _window = None
    _app = None

    def __init__(self):

        stages = [
            {'num': 1, 'text': "Prepare for install"},
            {'num': 2, 'text': "Install system"},
            {'num': 3, 'text': "Basic setup"}
            ]

#         screens = [
#             {'stage': 1, 'module': Welcome},
#             {'stage': 1, 'module': Partitioning},
#             {'stage': 2, 'module': InstallSystem},
#             {'stage': 3, 'module': SetupUsers},
#             {'stage': 3, 'module': SetupBootloader}
#             ]

        self._app = QApplication(sys.argv)
        w = YaliWindow.Widget()

        for stage in stages:
            w.addStage(stage['num'], stage['text'])

#         num = 0
#         for screen in screens:
#             num += 1
#             w.addScreen(screen['stage'], num, screen['module'].Widget())

        self._window = w

        self._app.connect(self._app, SIGNAL("lastWindowClosed()"),
                          self._app, SLOT("quit()"))


    ##
    # Fire up the interface.
    def run(self):

        self._window.show()
        # We want it to be a full-screen window.
        #self._window.resize(app.desktop().size())
        # FIXME:
        # But for testing purposes a 800x600 window can be OK.
        self._window.resize(800, 600)

        self._app.exec_loop()

