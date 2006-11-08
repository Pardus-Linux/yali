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


import new
import inspect


from yali.asod.pointcut import PointCut


##
# weave_method, weaves the method (met_name) of an object (obj) with
# an Aspect instance.
def weave_method(aspect, obj, met_name):

    # set or update the aspects list of weaved object
    try:
        aspect_dict = getattr(obj, 'aspect_dict')
    except:
        # no aspects defined before
        aspect_dict = {}
    if not aspect_dict.has_key(aspect.name):
        aspect_dict[aspect.name] = aspect
    setattr(obj, 'aspect_dict', aspect_dict)


    # new method's data 
    data = {}
    data['original_method_name'] = met_name
    data['method_name'] = '__' + met_name + '_weaved'
    if inspect.isclass(obj):
        data['__class__'] = obj
    else:
        data['__class__'] = obj.__class__


    def wrapper(wobj, *args, **kwargs):

        # run aspect's before method
        for a in aspect_dict.values():
            a.before(wobj, data, *args, **kwargs)
        
        # run original method
        met_name = data['method_name']
        met = getattr(wobj, met_name)
        ret =  met.im_func(wobj, *args, **kwargs)

        # run aspect's after method
        for a in aspect_dict.values():
            a.after(wobj, data, *args, **kwargs)

        return ret

    original_method = getattr(obj, met_name)
    weaved_name = data['method_name']
    # don't rebind it 
    if not hasattr(obj, weaved_name):
        setattr(obj, weaved_name, original_method)

    wrapper.__doc__ = original_method.__doc__
    if inspect.isclass(obj):
        new_method = new.instancemethod(wrapper, None, obj)
    else:
        new_method = new.instancemethod(wrapper, obj, obj.__class__)
    setattr(obj, met_name, new_method)



def weave_class_method(aspect, klass, met_name):
    p = PointCut()
    p.addMethod(klass, met_name)
    aspect.updatePointCut(p)
    weave_method(aspect, klass, met_name)

def weave_object_method(aspect, obj, met_name):
    weave_class_method(aspect, obj, met_name)



##
# weave all methods in class (klass) with an aspect
def weave_all_class_methods(aspect, klass):
    
    p = PointCut()
    _dict = dict(inspect.getmembers(klass, inspect.ismethod))
    for met_name in _dict:
        if not met_name.startswith('__'):
            p.addMethod(klass, met_name)

    aspect.updatePointCut(p)
    for met_name in _dict:
        if not met_name.startswith('__'):
            weave_method(aspect, klass, met_name)


##
# weave all methods in an object (obj) with an aspect
def weave_all_object_methods(aspect, obj):
    # it's the same as weaving a class. so apply it...
    weave_all_class_methods(aspect, obj)
