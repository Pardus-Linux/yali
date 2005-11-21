#!/usr/bin/python

import sys
sys.path.append(".")
sys.path.append("..")

from yali.asod.loggeraspect import LoggerAspect
from yali.asod.debuggeraspect import DebuggerAspect
from yali.asod.weaver import *

l = LoggerAspect()
d = DebuggerAspect()

class C:
    def selam(self):
        print "selam"

    def hola(self, name):
        print "hola", name

c = C()
c2 = C()

weave_class_methods(l, C)
weave_object_methods(d, c2)

c.selam()
print '-'*10
print
c2.selam()
print
c2.hola("Baris")
