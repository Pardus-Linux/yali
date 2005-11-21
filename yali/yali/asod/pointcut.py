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

# A pointcut is a logical description of a set of join points, where
# join points are points in the structure or execution of a program.


##
# PointCut class, a dict for join points
class PointCut(dict):

    ##
    # add a brakepoint
    # @param obj: python class or object
    # @param method_name: name of the method in object/class
    def addMethod(self, obj, method_name):
        if not self.has_key(obj):
            self[obj] = set()

        self[obj].add(method_name)

    ##
    # remove a breakpoint
    # @param obj: python class or object
    # @param method_name: name of the method in object/class
    def delMethod(self, obj, method_name):
        if self.has_key(obj):
            self[obj].remove(method_name)
