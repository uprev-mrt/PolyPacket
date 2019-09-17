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
import struct
import random


def packVarSize(value):
    bytes = bytearray([])
    tmp =0
    size =0

    while( value > 0):
        tmp = value & 0x7F
        value = value >> 7
        if value > 0:
            tmp |= 0x80
        bytes.append(tmp)

    return bytes

def readVarSize(bytes):
    tmp =0
    val =0
    size =0

    for i in range(4):
        tmp = bytes[i]
        size+= 1
        val = val << 7
        val |= tmp & 0x7F
        if (tmp & 0x80) == 0:
            break

    return val, size


class PolyField:
    def __init__(self, desc):
        self.desc = desc
        self.id = desc.id
        self.isPresent = False
        self.values = [-1]
        self.len = 0

    def set(self,val):
        self.isPresent = True
        if self.desc.isArray:
            self.len = len(val)
            self.values = val
        else:
            if self.desc.isString:
                self.len = len(val)
                self.values[0] = val
            else:
                self.len = 1
                self.values[0] = int(val)


    def get(self):
        if self.isPresent :
            if self.desc.isArray :
                return self.values
            else:
                return self.values[0]
        else:
            return -1

    def parse(self, bytes):
        self.isPresent = True
        strFormat = "%s"+ self.desc.pyFormat
        idx =0
        if self.desc.isArray:
            self.len, idx = readVarSize(bytes)
            self.len = self.len / self.desc.objSize
        else:
            if self.desc.isString:
                self.len, idx = readVarSize(bytes)
            else:
                self.len = 1

        if self.desc.isString:
            self.values[0] = struct.unpack(">" + str(self.len) + self.desc.pyFormat, bytes[idx:idx+self.len+1])[0].decode("utf-8")
        else:
            self.values = struct.unpack(">" + str(self.len) + self.desc.pyFormat, bytes[idx:idx+self.len+1])
        return idx + self.len +1

    def pack(self, id):
        byteArr = bytes([])
        strFormat = ">" + str(self.len)+ self.desc.pyFormat

        byteArr += packVarSize(id)

        if self.desc.isArray | self.desc.isString:
            byteArr += packVarSize(self.len * self.desc.objSize)


        if self.desc.isString:
            byteArr+= struct.pack(">" +str(self.len) + "s", self.values[0].encode('utf-8'))
        else:
            byteArr+= struct.pack(strFormat, *self.values)

        return byteArr

    def printJSON(self):
        json =""
        json += "\"" + self.desc.name +"\" : "
        if self.desc.isArray:
            json+= "[" + ''.join(' {:02x}'.format(x) for x in self.values) + "]"
        else:
            if self.desc.isString :
                json+= "\"" + str(self.values[0]) +"\""
            else:
                json+= str(self.values[0])

        return json

class PolyPacket:
    def __init__(self, protocol ):
        self.protocol = protocol
        self.fields = []
        self.seq =0
        self.dataLen = 0
        self.token = randint(1, 32767)
        self.checksum = 0
        self.typeId = 0
        self.packet_handler = ''

    def setField(self, fieldName, value):
        for field in self.fields:
            if fieldName.lower() == field.desc.name.lower():
                field.set(value)
                break


    def build(self, typeId):
        self.typeId = typeId
        self.desc = self.protocol.packets[typeId]
        for fieldDesc in self.desc.fields:
            self.fields.append( PolyField(fieldDesc))

    def handler(self, iface):
        if not self.packet_handler == '':
            newPacket = self.packet_handler(self)
        else
            newPacket = iface.service.newPacket('Ack')

        newPacket.token = self.token + 32768

    def parse(self, rawBytes):
        self.raw = rawBytes
        idx =0;
        #pull in header
        self.typeId = rawBytes[0]
        self.seq = rawBytes[1]
        self.dataLen = (rawBytes[2] << 8) | rawBytes[3]
        self.token =   (rawBytes[4] << 8) | rawBytes[5]
        self.checksum =   (rawBytes[6] << 8) | rawBytes[7]

        idx = 8

        #look up desc
        self.build(self.typeId)

        #parse fields
        while idx < (len(rawBytes)-1):
            fieldId, varLenSize = readVarSize(rawBytes[idx:])
            idx+= varLenSize
            idx+= self.fields[fieldId].parse(rawBytes[idx:])


        return True

    def pack(self):
        byteArr =  bytes([])
        dataArr = bytes([])

        #TODO add header
        for i,field in enumerate(self.fields):
            if field.isPresent:
                dataArr += field.pack(i)

        self.dataLen = len(dataArr)

        byteArr = struct.pack('BBHHH', self.typeId, self.seq, self.dataLen, self.token, self.checksum)
        self.raw = byteArr + dataArr
        return self.raw

    def printJSON(self, meta= False):
        json ="{ \"typeId\" : \""+ self.desc.name + "\""



        for field in self.fields:
            if field.isPresent:
                json+= ", " + field.printJSON()

        json += "}"
        return json

class PolyIface:
    def __init__(self, connStr, service):
        self.connStr = connStr
        self.service = service
        self.bytesIn = deque([])
        self.frameCount =0
        self.packetsIn = deque([])
        self.name = "iface0"

    def print(self, text):
        if not self.service.print == '':
            self.service.print( text)

    def feedEncodedBytes(self, encodedBytes):

        for i in encodedBytes:
            self.bytesIn.append(i)
            if i == 0:
                self.frameCount +=1

        while self.frameCount > 0:
            encodedPacket = bytes([])
            newPacket = PolyPacket(self.service.protocol)
            while(1):
                x = self.bytesIn.popleft()
                if x == 0:
                    self.frameCount -=1
                    break
                else:
                    encodedPacket+= bytes([x])

            newPacket.parse(cobs.decode(encodedPacket))

            self.print( " <<< " + newPacket.printJSON())
            self.packetsIn.append(newPacket)

    def sendPacket(self, packet):
        raw = packet.pack()

        encoded = cobs.encode(bytearray(raw))
        encoded += bytes([0])

        self.print( " >>> " + packet.printJSON())

        return encoded


    def getPacket(self):
        if len(packetsIn) > 0:
            return packetsIn.popleft()



class PolyService:
    def __init__(self, protocol):
        self.protocol = protocol
        self.interfaces = []
        self.print = ''

    def addIface(self, connStr):
        self.interfaces.append(PolyIface(connStr, self))

    def newPacket(self, type):
        packet = PolyPacket(self.protocol)

        if type in self.protocol.packetIdx:
            packet.build(self.protocol.packetIdx[type])
        else:
            seld.print(" Packet Type \"" + type + "\", not found!")

        return packet

    def newStruct(self, type):
        return self.newPacket(type)
    #
    # def process(self):
    #     for iface in self.interfaces:
    #         if iface.frameCount > 0:
