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

# partrequest.py defines requests (format, mount) on the partitions.

from yali.exception import *
from yali.parteddata import *
from yali.filesystem import filesystem_types

def get_fs_obj(fs):
    for i in filesystem_types:
        if i.name == fs:
            return i

##
# requests object holds the list of requests
class RequestList(list):

    def append(self, req):
        i = self.__iter__()
        try:
            cur = i.next()
            while True:
                # don't hold more than one same type of requests for a
                # partition
                if cur._part.get_path() == req._part.get_path() and \
                        cur._type == req._type:
                    list.remove(self, cur)
                cur = i.next()
        except StopIteration:
            # end of list
            list.append(self, req)


    def remove_request(self, part, req_type):
        i = self.__iter__()
        try:
            cur = i.next()
            while True:
                if cur._part.get_path() == part.get_path() and \
                        cur._type == req_type:
                    list.remove(self, cur)
                cur = i.next()
        except StopIteration:
            # end of list
            pass
        


class PartRequest:
    _part = None

    def __init__(self, partition):
        self._part = partition

    def get_partition(self):
        return self._part



class FormatRequest(PartRequest):

    _type = "format"

    def __init__(self, partition, part_type):
        PartRequest.__init__(self, partition)
        self._part_type_name = partition_types[part_type][0]
        self._fs = partition_types[part_type][1]

    def apply_request(self):
        fsobj = get_fs_obj(self._fs)
        fs.format(self._part)

    def get_fs(self):
        return self._fs

    def get_part_type_name(self):
        return self._part_type_name


class MountRequest(PartRequest):

    _type = "mount"

    def __init__(self, partition, part_type, options=None):
        PartRequest.__init__(self, partition)
        self._part_type_name = partition_types[part_type][0]
        self._fs = partition_types[part_type][1]
        self._mountpoint = partition_types[part_type][2]
        self._options = options

    def apply_request(self):
        raise YaliException, "Not Implemented yet!"

    def get_fs(self):
        return self._fs

    def get_mountpoint(self):
        return self._mountpoint

    def get_part_type_name(self):
        return self._part_type_name
