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


# logger aspect

from yali.asod.meta import MetaAspect

class LoggerAspect:

    __metaclass__ = MetaAspect
    name = "logger"

    def before(self, wobj, data, *args, **kwargs):
        print "begin method", data['original_method_name']


    def after(self, wobj, data, *args, **kwargs):
        print "end method", data['original_method_name']
