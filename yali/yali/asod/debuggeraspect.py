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


from sys import stderr

from yali.asod.meta import MetaAspect

class DebuggerAspect:
    __metaclass__ = MetaAspect
    name = "testaspect"

    def __init__(self, out = stderr):
        self.out = out

    def before(self, wobj, data, *args, **kwargs):
        met_name = data['original_method_name']
        fun_str = "%s (args: %s -- kwargs: %s)" % (met_name, args, kwargs)
        
        self.out.write("Entering function: %s\n" % fun_str)


    def after(self, wobj, data, *args, **kwargs):
        met_name = data['original_method_name']
        fun_str = "%s (args: %s -- kwargs: %s)" % (met_name, args, kwargs)
        
        self.out.write("Left function: %s\n" % fun_str)

