# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

__version__ = "0.1"

import sys
import exceptions
import traceback
import cStringIO

from yali.exception import *


def default_runner():
    import yali.gui.runner

    sys.excepthook = exception_handler

    return yali.gui.runner.Runner()


def exception_handler(exception, value, tb):

#    sys.excepthook = sys.__excepthook__

    sio = cStringIO.StringIO()
    traceback.print_tb(tb, None, sio)

    v = '\n\n'
    for e in value.args:
        v += str(e) + '\n'
    sio.write(v)


    if isinstance(value, YaliError):
        # show Error dialog
        print "error"
    elif isinstance(value, YaliException):
        # show Exception dialog
        print "exception"
    else:
        # show known exception dialog
        print "unknown"

    sio.seek(0)

    import yali.gui.runner
    yali.gui.runner.showException(sio.read())
