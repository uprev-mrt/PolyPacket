#!/usr/bin/python3
#
#@file polyservice.py
#@brief python module to run a command line utility for a protocol
#@author Jason Berger
#@date 02/19/2019
#

import sys
import pkgutil
import subprocess
from polypacket.protocol import *
from collections import deque
from cobs import cobs


class PolyField:
    def __init__(self, desc):
        self.desc = desc
        self.id = desc.id
        self.isPresent = False

    def set(self,val):
        self.isPresent = True
        self.value = val

    def get(self):
        if self.isPresent :
            return self.value
        else
            return 0

    def pack(self):
        byteArr = []
        return byteArr

    def printJSON(self):
        str =""
        return str

class PolyPacket:
    def __init__(self, desc):
        self.name = ""
        self.desc = desc
        self.fields = []
        for fieldDesc in desc.fields:
            self.fields.append(PolyField(fieldDesc))

    def pack(self):
        byteArr = []
        #TODO add header
        for field in self.fields:
            byteArr.append(field.pack())

        return byteArr

    def printJSON(self):
        str =""
        return str

class PolyIface:
    def __init__(self, connStr):
        self.connStr = connStr
        self.bytesIn = deque([])
        self.frameCount =0

    def feedEncodedBytes(self, bytes):
        self.bytesIn.append(bytes)

        for i in bytes:
            if i == 0:
                self.frameCount +=1

    def getPacketBytes(self):
        encodedPacket =[]
        if self.frameCount > 0:
            while(1):
                x = self.bytesIn.popleft()
                if x == 0:
                    self.frameCount -=1
                    break
                else
                    encodedPacket.append(i)


        return cobs.decode(encodedPacket)








class PolyService:
    def __init__(self, protocol):
        self.protocol = protocol
        self.interfaces = []

    def addIface(self, connStr):
        self.interfaces.append(PolyIface(connStr))

    def process(self):
        for iface in self.interfaces:
            if iface.frameCount > 0:
