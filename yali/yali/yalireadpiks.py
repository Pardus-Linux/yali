#!/usr/bin/python
#

import piksemel
import sys

class kahyaData:
    def __init__(self):
        self.language=None
        self.keyData=Keymap()
        self.rootPassword=None
        self.hostname=None
        self.users=[]
        self.partitioning=[]
        self.partitioningType=None
        self.autoLoginUser=None
        self.repoName = "remoteRepo"
        self.repoAddr = None
        
class yaliUser:	
    def __init__(self):
        self.autologin=None
        self.username=None
        self.realname=None
        self.password=None
        self.groups=[]
 
class Keymap:
    def __init__(self):
        self.console = None
        self.X = None
        self.translation = None
   
class yaliPartition:
    def __init__(self):
        self.partitionType=None
        self.format=None
        self.ratio=None
        self.disk=None
        self.fsType=None
        self.mountPoint=None

def read(args):
    doc=piksemel.parse(args)
    data=kahyaData()
    data.language=doc.getTagData("language")
    data.keyData.X=doc.getTagData("keymap")
    data.rootPassword=doc.getTagData("root_password")
    data.hostname=doc.getTagData("hostname")
    data.repoName=doc.getTagData("reponame") or data.repoName
    data.repoAddr=doc.getTagData("repoaddr")
    usrsTag=doc.getTag("users")

    for p in usrsTag.tags():
        info=yaliUser()
        info.autologin=p.getAttribute("autologin")
        info.username=p.getTagData("username")
        info.realname=p.getTagData("realname")
        info.password=p.getTagData("password")
        if(p.getTagData("groups")!=None):
            info.groups=p.getTagData("groups").split(",")
        data.users.append(info)

    partitioning=doc.getTag("partitioning")
    data.partitioningType=partitioning.getAttribute("partitioning_type")
    if(data.partitioningType=="auto"):
        autoPart=yaliPartition()
        autoPart.disk=partitioning.firstChild().data()
        data.partitioning.append(autoPart)
    else:
        for q in partitioning.tags():
            partinfo=yaliPartition()
            partinfo.partitionType=q.getAttribute("partition_type")
            partinfo.format=q.getAttribute("format")
            partinfo.ratio=q.getAttribute("ratio")
            partinfo.fsType=q.getAttribute("fs_type")
            partinfo.mountPoint=q.getAttribute("mountpoint")
            partinfo.disk=q.firstChild().data()
            data.partitioning.append(partinfo)
    return data

