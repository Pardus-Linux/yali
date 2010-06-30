# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

__version__ = "2.2.0"

import sys
import exceptions
import traceback
import cStringIO

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import pisi
from yali.exception import *

def default_runner():
    """ Main runner of YALI """
    import yali.gui.runner

    sys.excepthook = exception_handler

    return yali.gui.runner.Runner()

exception_normal, exception_fatal, \
    exception_pisi, exception_informational, \
    exception_unknown = range(5)

def exception_handler(exception, value, tb):
    """ YALI exception handler for showing exceptions in GUI """

    knownExceptions = {YaliError:           exception_fatal,
                       YaliException:       exception_normal,
                       YaliExceptionInfo:   exception_informational,
                       pisi.Error:          exception_pisi}

    try:
        exception_type = knownExceptions[filter(lambda x: isinstance(value, x), knownExceptions.keys())[0]]
    except IndexError:
        exception_type = exception_unknown

    sio = cStringIO.StringIO()

    v = ''
    for e in value.args:
        v += str(e) + '\n'
    sio.write(v)

    sio.write(str(exception))
    sio.write('\n\n')
    sio.write(_("Backtrace:"))
    sio.write('\n')
    traceback.print_tb(tb, None, sio)

    sio.seek(0)

    if exception_type == exception_informational:
        from yali.gui.YaliDialog import InfoDialog
        InfoDialog(unicode(v), title=_("Error"), icon="error")
    else:
        import yali.gui.runner
        yali.gui.runner.showException(exception_type, unicode(sio.read()))
