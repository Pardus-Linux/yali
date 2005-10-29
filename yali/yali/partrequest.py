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

def get_fs_obj(fsname):
    return filesystem_types[fsname]


##
# requests object holds the list of requests
class RequestList(list):

    ##
    # iterator function searches for the a request by partition and
    # type
    def searchRequest(self, partition, request_type=None):
        i = self.__iter__()
        try:
            cur = i.next()
            while True:
                if cur.partition() == partition:
                    # partitions match!

                    if not request_type:
                        # FOUND (without checking a type)
                        yield cur
                
                    else:
                        if cur.requestType() == request_type:
                            # FOUND
                            yield cur

                cur = i.next()
        except StopIteration:
            # end of list
            pass

    def append(self, req):

        self.removeRequest(req.partition(), req.requestType())
        list.append(self, req)


    def removeRequest(self, partition, request_type):
        found = [x for x in self.searchRequest(partition, request_type)]
        # this should give (at most) one result
        # cause we are storing one request for a (part, reqType) pair
        assert(len(found) <= 1)

        for f in found:
            list.remove(self, f)
        

##
# Abstract Partition request class
class PartRequest:

    ##
    # empty initializeer
    def __init__(self):
        self._partition = None
        self._request_type = ""
        self._isapplied = False

    ##
    # apply the request to the partition
    def applyRequest(self):
        self._isapplied = True

    ##
    # is the request applied on partition?
    def isApplied(self):
        return self._isapplied

    ##
    # set the partition to apply request
    def setPartition(self, partition):
        self._partition = partition

    def partition(self):
        return self._partition

    ##
    # set the type of the request
    def setRequestType(self, t):
        self._request_type = t

    ##
    # get the type of the request
    def requestType(self):
        return self._request_type

##
# format partition request
class FormatRequest(PartRequest):

    _part_type_name = ""
    _fs = ""

    def __init__(self, partition, part_type):
        PartRequest.__init__(self)

        self.setPartition(partition)
        self.setRequestType("format")

        self._part_type_name = partition_types[part_type][0]
        self._fs = partition_types[part_type][1]

    def applyRequest(self):
        fsobj = get_fs_obj(self._fs)
        fsobj.format(self.partition())

        PartRequest.applyRequest(self)

    def fs(self):
        return self._fs

    def part_type_name(self):
        return self._part_type_name


##
# mount partition request
class MountRequest(PartRequest):

    _part_type_name = ""
    _fs = ""
    _mountpoint = ""
    _options = ""

    def __init__(self, partition, part_type, options=None):
        PartRequest.__init__(self)

        self.setPartition(partition)
        self.setRequestType("mount")

        self._part_type_name = partition_types[part_type][0]
        self._fs = partition_types[part_type][1]
        self._mountpoint = partition_types[part_type][2]
        self._options = options

    def applyRequest(self):
        #raise YaliException, "Not Implemented yet!"
        PartRequest.applyRequest(self)

    def fs(self):
        return self._fs

    def mountpoint(self):
        return self._mountpoint

    def part_type_name(self):
        return self._part_type_name
