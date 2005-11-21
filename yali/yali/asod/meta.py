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


# Aspect is an unit encapsulating cross-cutting conserns.
# meta.py module defines a metaclass called MetaAspects.
# Every aspect class should set this as __metaclass__


from yali.asod.pointcut import PointCut


##
# MetaAspect is a metaclass that creates an Aspect class.
class MetaAspect(type):

    ##
    # create a new class with the necessity members
    def __new__(cls, classname, bases, classdict):
        _pointcut = PointCut()

        def updatePointCut(cls, pc):
            for wobj, met_names in pc.items():
                for met_name in met_names:
                    cls._pointcut.addMethod(wobj, met_name)

        def before(cls, wobj, data, *args, **kwargs):
            if cls.hasJoinPoint(wobj, data):
                    met = getattr(cls, 'before__original')
                    return met.im_func(cls, wobj, data, *args, **kwargs)

        def after(cls, wobj, data, *args, **kwargs):
            if cls.hasJoinPoint(wobj, data):
                    met = getattr(cls, 'after__original')
                    return met.im_func(cls, wobj, data, *args, **kwargs)        
        def hasJoinPoint(cls, wobj, data):
            met_name = data['original_method_name']

            
            if cls._pointcut.has_key(wobj):
                if met_name in cls._pointcut[wobj]:
                    return True

            ##
            # Try object's class if instance is not found
            klass = data['__class__']
            if cls._pointcut.has_key(klass):
                if met_name in cls._pointcut[klass]:
                    return True

            return False

        # we'll first rebind before and after.
        # then bind our new modules
        classdict['before__original'] = classdict['before']
        classdict['after__original'] = classdict['after']
        classdict['before'] = before
        classdict['after'] = after
        classdict['_pointcut'] = _pointcut
        classdict['updatePointCut'] = updatePointCut
        classdict['hasJoinPoint'] = hasJoinPoint
        
        selfclass = super(MetaAspect, cls).__new__\
            (cls, classname, bases, classdict)
        return selfclass

