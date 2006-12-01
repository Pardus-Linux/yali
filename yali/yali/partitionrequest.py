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

# partitionrequest.py defines requests (format, mount) on the partitions.

import os
import yalisys

from yali.exception import *
from yali.constants import consts
import yali.partitiontype as parttype
import yali.sysutils

class RequestException(YaliException):
    pass


# poor man's enum ;)
formatRequestType, mountRequestType, swapFileRequestType = range(3)


##
# requests object holds the list of requests
class RequestList(list):

    ##
    # apply all requests
    def applyAll(self):
        
        # first apply format requests
        for r in self.searchReqTypeIterate(formatRequestType):
            r.applyRequest()

        # then mount request
        # but mount root (/) first
        pt = parttype.root
        rootreq = self.searchPartTypeAndReqType(pt, mountRequestType)
	if not rootreq:
	    raise RequestException, "Desired partition request not found: root partition request."
        rootreq.applyRequest()

        # mount others
        for r in self.searchReqTypeIterate(mountRequestType):
            if r.partitionType() != rootreq.partitionType():
                r.applyRequest()

        # apply swap requests if any...
        for r in self.searchReqTypeIterate(swapFileRequestType):
            r.applyRequest()


    ##
    # iterator function searches for a request by partition and
    # request type
    #
    # @return: generator returns a request type in each turn.
    #
    # @param p: Partition (defined in partition.py)
    # @param t: request Type (eg. formatRequestType)
    def searchPartAndReqTypeIterate(self, p, rt):
        i = self.__iter__()
        try:
            cur = i.next()
            while True:
                if cur.partition() == p and cur.requestType() == rt:
                    # FOUND
                    yield cur

                cur = i.next()
        except StopIteration:
            # end of list
            pass

    
    ##
    # Iterator function searches for a request 
    # by request type
    #
    # @return: generator returns a request type in each turn.
    #
    # @param t: request Type (eg. formatRequestType)
    def searchReqTypeIterate(self, rt):
        i = self.__iter__()
        try:
            cur = i.next()
            while True:
                if cur.requestType() == rt:
                    # FOUND
                    yield cur

                cur = i.next()
        except StopIteration:
            # end of list
            pass


    ##
    # Iterator function searches by partition type and request type
    #
    # @return: generator returns a request type in each turn.
    #
    # @param pt: Partition Type (defined in partitiontype.py)
    # @param rt: Request Type
    def searchPartTypeAndReqTypeIterate(self, pt, rt):
        i = self.__iter__()
        try:
            cur = i.next()
            while True:
                if cur.partitionType() == pt and cur.requestType() == rt:
                    # FOUND
                    yield cur

                cur = i.next()
        except StopIteration:
            # end of list
            pass


    ##
    # Search for a given partition type and request type.
    #
    # @return: if found returns the PartRequest else None.
    #
    # @param pt: Partition Type (defined in partitiontype.py)
    # @param rt: Request Type
    def searchPartTypeAndReqType(self, pt, rt):
	req = [x for x in self.searchPartTypeAndReqTypeIterate(pt, rt)]
        # this should give (at most) one result
        # cause we are storing one request for a partitionType()
        assert(len(req) <= 1)

	if not req:
	    return None
	else:
	    # return the only request found.
	    return req.pop()


    ##
    # add/append a request
    def append(self, req):
        self.removeRequest(req.partition(), req.requestType())

        rt = req.requestType()
        pt = req.partitionType()
        found = self.searchPartTypeAndReqType(pt, rt)

	# RequestList stores only one request for a requestType() -
	# partitionType() pair.
        if found:
            e = "There is a request with the same partitionType() and requestType()."
            raise RequestException, e

        list.append(self, req)


    ##
    # remove request matching (partition, request type) pair
    # @param p: Partition
    # @param t: request Type (eg. formatRequestType)
    def removeRequest(self, p, rt):
        found = [x for x in self.searchPartAndReqTypeIterate(p, rt)]
        # this should give (at most) one result
        # cause we are storing one request for a (part, reqType) pair
        assert(len(found) <= 1)

        for f in found:
            self.remove(f)


    ##
    # remove a request
    def remove(self, i):
        list.remove(self, i)
        

    ##
    # remove all requests
    def remove_all(self):
        def _iter_remove():
            i = self.__iter__()
            try:
                while True:
                    cur = i.next()
                    self.remove(cur)
            except StopIteration:
                # end of list
                pass

        # the code above doesn't removes all. so bruteforce it...
        while True:
            if len(self):
                _iter_remove()
            else:
                return


##
# Abstract Partition request class
class PartRequest:

    ##
    # empty initializeer
    def __init__(self):
        self._partition = None
        self._partition_type = None
        self._request_type = None
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
    
    ##
    # get partition
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
    # set partition type
    def setPartitionType(self, t):
        self._partition_type = t

    ##
    # get partition type
    def partitionType(self):
        return self._partition_type


##
# format partition request
class FormatRequest(PartRequest):

    ##
    # initialize format request
    # @param partition: Partition
    # @param part_type: partition type (defined in partitiontype.py)
    def __init__(self, partition, part_type):
        PartRequest.__init__(self)

        self.setPartition(partition)
        self.setPartitionType(part_type)
        self.setRequestType(formatRequestType)

    def applyRequest(self):
        t = self.partitionType()
        fs = t.filesystem
        fs.format(self.partition())

        PartRequest.applyRequest(self)


##
# mount partition request
class MountRequest(PartRequest):

    _options = ""

    def __init__(self, partition, part_type, options=None):
        PartRequest.__init__(self)

        self.setPartition(partition)
        self.setPartitionType(part_type)
        self.setRequestType(mountRequestType)

        self._options = options

    def applyRequest(self):

        pt = self.partitionType()

        if not pt.mountpoint: # do nothing
            return

        source = self.partition().getPath()
        target = consts.target_dir + pt.mountpoint
        filesystem = pt.filesystem.name()

        if not os.path.isdir(target):
            os.mkdir(target)

        yalisys.mount(source, target, filesystem)
        
        mtab_entry = "%s %s %s rw 0 0\n" % (source,
                                            target,
                                            filesystem)
        open("/etc/mtab", "a").write(mtab_entry)
        #FIXME: use logging system
#        print mtab_entry

        
        PartRequest.applyRequest(self)


##
# swap file request
class SwapFileRequest(PartRequest):

    def __init__(self, partition, part_type):
        PartRequest.__init__(self)

        self.setPartition(partition)
        self.setPartitionType(part_type)
        self.setRequestType(swapFileRequestType)


    def applyRequest(self):

        # see #832
        if yali.sysutils.mem_total() > 512:
            yali.sysutils.swap_as_file(consts.swap_file_path, 300)
        else:
            yali.sysutils.swap_as_file(consts.swap_file_path, 600)
        
        PartRequest.applyRequest(self)



# partition requests singleton.
partrequests = RequestList()
