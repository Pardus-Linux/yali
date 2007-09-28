#!/usr/bin/python
#

import re
import sys
import yali.yalireadpiks as yaliReadPiks
from yali.localedata import *
from yali.users import *

class userErrors:
    def __init__(self):
        self.Empty=False
        self.Uname=False
        self.Rname=False
        self.Password=False
        self.Groups=False

class partitionErrors:
    def __init__(self):
        self.PartitionType=False
        self.Format=False
        self.Disk=False
        self.FsType=False
        self.MountPoint=False

class errors:
    def __init__(self):
        self.Keymap=False
        self.Lang=False
        self.Root=False
        self.Users=False
        self.Empty=False
        self.Disk=False
        self.Root=False
        self.TotalRatio=False

class userFunctions:
    def __init__(self,username,groups,correctdata):
        self.username=username
        self.groups=groups
        self.correctData = correctdata

    def checkAutologin(self):
        if(self.correctData.autoLoginUser):
            return False
        return True

    def checkValidity(self):
        if self.username and re.search("[0-9a-zA-Z.?!_-]",self.username):
            return True
        return False

    def checkName(self):
        for usr in self.correctData.users:
            if(usr.username==self.username):
                return True
        return False

    def checkGroups(self):
        for element in self.groups:
            for group in yaliKickStart().defaultGroups:
                if (group==element or element=="wheel"):
                    break
            else:
                return element
        else:
            return False

class otherFunctions:
    def __init__(self,keyX):
        self.keyX=keyX

    def checkKeymapX(self):
        for element in getKeymaps():
            if element.X==self.keyX:
                return True
        return False 

    def findKeymap(self):
        for element in getKeymaps():
            if element.X==self.keyX:
                return element.console
        return False

class partitionFunctions:
    def __init__(self,fs,disk):
        self.fs=fs
        self.disk=disk
    def checkFileSystem(self):
        for element in yaliKickStart().fileSystems:
            if element==self.fs:
                return True
        return False
    def checkFileSystem2(self):
        for element in yaliKickStart().fileSystems2:
            if element == self.fs:
                return True
        return False
    def checkDiskSyntax(self):
        return re.match("[h,s]d(\D{1})[1-9]$",self.disk) 
    def convertDisk(self):
        list={'a':'p0','b':'p1','c':'s0','d':'s1'}
        self.letter=self.disk[2]
        device=str(list[self.letter]+'p'+str(int(self.disk[3])-1))
        print device
        return device

class yaliKickStart:
    def __init__(self):
        self.fileSystems=["swap","ext3","ntfs","reiserf","xfs"]
        self.fileSystems2=["ext3","xfs"]
        self.defaultGroups=["audio","dialout","disk","pnp","pnpadmin","power","removable","users","video"]
        self.errorList=[]
        self.RatioList=[]
        self.correctData=yaliReadPiks.yaliKickstartData()
        self.total=0

    def readData(self,kickstartFile):
        self.filePath = kickstartFile
        self.data = yaliReadPiks.read(kickstartFile)

    def checkRatio(self):
        """ It checks partition ratios """
        for eachRatio in self.data.partitioning:
            self.RatioList.append(eachRatio.ratio)
        for i in self.RatioList:
            self.total+=int(i)
        if self.total==100:
            return True
        return False

    def checkAllOptions(self):
        error=errors()
        otherFunct=otherFunctions(self.data.keyData.X)

        ###language selection###
        if(locales.has_key(self.data.language)):
            self.correctData.language=self.data.language
        else:
            error.Lang=True
            self.errorList.append("Language Error: %s does not exist"%self.data.language)

        ###keymap selection###
        if(self.data.keyData.X):
            if (otherFunct.checkKeymapX()):
                self.correctData.keyData.X=self.data.keyData.X
                self.correctData.keyData.console=otherFunct.findKeymap()
            else:
                error.Keymap=True
                self.errorList.append("Keymap Error: %s not valid "%self.data.keyData.X)
        else:
            if error.Lang!=True:
                for lang in getLangsWithKeymaps():
                    if(lang[0]==self.correctData.language):
                        if(self.correctData.language=="tr"):
                            self.correctData.keyData.X=lang[1][0].X
                            self.correctData.keyData.console=lang[1][0].console
                        else:
                            self.correctData.keyData.X=lang[1].X
                            self.correctData.keyData.console=lang[1].console
                        break
                else:
                    error.Keymap=True
                    self.errorList.append("Keymap Error: Cannot associate Keymap for %s"%self.data.language)

        ###root password selection###
        if(len(self.data.rootPassword)<4):
            error.Root=True
            self.errorList.append("Root Password Error : Password is too short")
        else:
            self.correctData.rootPassword=self.data.rootPassword

        ###hostname selection###
        if(self.data.hostname):
            self.correctData.hostname=self.data.hostname
        else:
            self.correctData.hostname="pardus"

        ###users selections###
        if(len(self.data.users)==0):
            error.Users=True
            self.errorList.append("User Error: No user entry")
        else:
            self.correctData.users=[]
            for user in self.data.users:
                userError=userErrors()
                correctUser=User()
                checkFunctions=userFunctions(user.username,user.groups,self.correctData)
                if(user.autologin=="yes" and checkFunctions.checkAutologin()):
                    self.correctData.autoLoginUser=user.username
                if (user.username=="root" or checkFunctions.checkValidity()!=True or checkFunctions.checkName()==True):
                    userError.Uname=True
                    if (user.username and userError.Uname==True):
                        self.errorList.append("Username Error for %s : username already exist or not valid"%user.username)
                    else:
                        self.errorList.append("Username Error : no Entry")
                if not user.realname:
                    userError.Rname=True
                    if userError.Uname!=True:
                        self.errorList.append("Real name Error for %s: No entry"%user.username)
                if (len(user.password)<4 or user.username==user.password or user.realname==user.password):
                    userError.Password=True
                    if userError.Uname!=True:
                        self.errorList.append("Password Error for %s "%user.username)
                if len(user.groups)==0:
                    user.groups=self.defaultGroups
                elif (checkFunctions.checkGroups()):
                    self.errorList.append("Groups Error for %s : %s group not valid"%(user.username,checkFunctions.checkGroups()))
                    userError.Groups=True
                if(userError.Uname!=True and userError.Rname!=True and userError.Password!=True and userError.Groups!=True):
                    correctUser.username=user.username
                    correctUser.realname=user.realname
                    correctUser.passwd=user.password
                    correctUser.groups=user.groups
                    self.correctData.users.append(correctUser)

        if (len(self.correctData.users)==0):
            error.Users=True
            self.errorList.append("User Error: No user added")

        ###partitioning selection###
        correctPart=yaliReadPiks.yaliPartition()
        if(self.data.partitioningType=="auto" or self.data.partitioningType!="manuel"):
            self.correctData.partitioningType="auto"
            if(len(self.data.partitioning)!=1):
                error.Empty=True
                self.errorList.append("Auto Partitioning Error : No partition entry  or too many partition")
            else:
                PartiFunction=partitionFunctions(self.data.partitioning[0].fsType,self.data.partitioning[0].disk)
                print self.data.partitioning[0].disk
                if not PartiFunction.checkDiskSyntax():
                    error.Disk=True
                    self.errorList.append("Auto Partitioning Error : Wrong Disk Syntax")
                else:
                    correctPart.partitionType="pardus_root"
                    correctPart.format="true"
                    correctPart.ratio="100"
                    correctPart.disk=self.data.partitioning[0].disk
                    self.correctData.partitioning.append(correctPart)

        elif(self.data.partitioningType=="manuel"):
            self.correctData.partitioningType="manuel"

            if(len(self.data.partitioning)==0):
                error.Empty=True
                self.errorList.append("Manuel Partitioning Error : No partition entry ")
            else:
                for partitionRoot in self.data.partitioning:
                    if partitionRoot.partitionType=="pardus_root": #pardus_root is required
                        break
                else:
                    error.Root=True
                    self.errorList.append("Manuel Partitioning Error : \"pardus_root\" missing ")
                if(self.checkRatio()!=True):
                    error.TotalRatio=True
                    self.errorList.append(" Ratio Error : Total not equal to 100")
                else:    
                    if(error.Empty!=True and error.Root!=True):
                        for partition in self.data.partitioning:
                            errorPartition=partitionErrors()
                            functPart=partitionFunctions(partition.fsType,partition.disk)
                            if  not (partition.partitionType=="pardus_root" or partition.partitionType=="pardus_swap" or partition.partitionType=="pardus_home" or partition.partitionType=="other"):
                                errorPartition.PartitionType=True
                                self.errorList.append("Partition type Error :%s not valid"%partition.partitionType)
                            if(partition.format!="false"):
                                partition.format="true"
                            if not (functPart.checkDiskSyntax()):
                                errorPartition.Disk=True
                                self.errorList.append(" Disk Error for %s: %s not valid"%(partition.partitionType,partition.disk))
                            if (partition.partitionType!="other"):
                                if not (functPart.checkFileSystem2()):
                                    errorPartition.FsType=True
                                    self.errorList.append("File system Error for %s : %s not valid"%(partition.partitionType,partition.fsType))
                            else:
                                if not (functPart.checkFileSystem()):
                                    errorPartition.FsType=True
                                    self.errorList.append("File system Error for %s : %s not valid"%(partition.partitionType,partition.fsType))
                            if  partition.mountPoint!=None  and not(re.search("[a-zA-Z0-9]",partition.mountPoint)) :
                                errorPartition.MountPoint=True
                                self.errorList.append("Mountpoint Error for %s : %s not valid"%(partition.partitionType,partition.mountPoint))
                            if(errorPartition.PartitionType!=True and errorPartition.Disk!=True and errorPartition.FsType!=True and errorPartition.MountPoint!=True):
                                partition.disk=functPart.convertDisk()
                                self.correctData.partitioning.append(partition)

        return self.errorList

    def checkFileValidity(self):
        self.correctData=None
        self.errorList=self.checkAllOptions()
        if(len(self.errorList)==0):
            return True
        return self.errorList
    def getValues(self):
        if self.checkFileValidity() == True:
            return self.correctData
        return self.errorList

