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
import threading
import errno
import socket





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

    if len(bytes) == 0:
        bytes.append(0)

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

class PolyUdp (threading.Thread):
    def __init__(self, iface, localPort ):
        threading.Thread.__init__(self)
        self.iface = iface
        self.localPort = localPort
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(0)
        self.socket.bind(("127.0.0.1", self.localPort))
        self.iface.print(self.iface.name + " Listening on port: " + str(localPort))
        self.host = 0

    def __del__(self):
        self.socket.close()
        threading.Thread.__del__(self)

    def close(self):
        self.socket.close()

    def connect(self, hostIp, hostPort):
        self.iface.print(self.iface.name + " Connecting to " + hostIp + ":"+str(hostPort))
        self.host = (hostIp, hostPort)

    def send(self, data):
        if not self.host == 0:
            #self.iface.print(" >>> " + ''.join(' {:02x}'.format(x) for x in data))
            self.socket.sendto(data, self.host)

    def run(self):
        while True:
            try:
                data, address = self.socket.recvfrom(1024)
                if data:
                    if self.host == 0:
                        self.host = address
                        self.iface.service.print("Connection Accepted: " + str(self.host))
                    #self.iface.print(" <<< " + ''.join(' {:02x}'.format(x) for x in data))
                    self.iface.feedEncodedBytes(data)
            except IOError as e:  # and here it is handeled
                if e.errno == errno.EWOULDBLOCK:
                    pass


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

        dataLen = self.len * self.desc.objSize

        try:
            if self.desc.isString:
                self.values[0] = struct.unpack("<" + str(self.len) + self.desc.pyFormat, bytes[idx:idx+dataLen ])[0].decode("utf-8")
            else:
                self.values = struct.unpack("<" + str(self.len) + self.desc.pyFormat, bytes[idx:idx+dataLen])
        except:
            print(" Error Parsing: " + self.desc.name+ '-->' + ''.join(' {:02x}'.format(x) for x in bytes[idx:idx+dataLen]))
        return idx + dataLen

    def pack(self, id):
        byteArr = bytes([])
        strFormat = "<" + str(self.len)+ self.desc.pyFormat

        byteArr += packVarSize(id)

        if self.desc.isArray | self.desc.isString:
            byteArr += packVarSize(self.len * self.desc.objSize)


        if self.desc.isString:
            byteArr+= struct.pack("<" +str(self.len) + "s", self.values[0].encode('utf-8'))
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
        self.token = random.randint(1, 32767)
        self.checksum = 0
        self.typeId = 0
        self.packet_handler = ''
        self.ackFlag = False

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

    def copyTo(self, packet):
        return 0

    def handler(self, iface):

        #dont respond to acks
        if self.ackFlag:
            return 0

        resp = 0

        if self.desc.name in iface.service.handlers:
            resp = iface.service.handlers[self.desc.name](self)
        elif 'default' in iface.service.handlers:
            resp = iface.service.handlers['default'](self)
        elif self.desc.hasResponse:
            resp =  iface.service.newPacket(self.desc.response.name)
        elif iface.service.autoAck:
            resp = iface.service.newPacket('Ack')
        else:
            return 0


        resp.ackFlag = True
        resp.token = self.token | 0x8000

        return resp

    def parse(self, rawBytes):
        self.raw = rawBytes
        idx =0;
        #pull in header
        self.typeId = rawBytes[0]
        self.seq = rawBytes[1]
        self.dataLen = (rawBytes[3] << 8) | rawBytes[2]
        self.token =   (rawBytes[5] << 8) | rawBytes[4]
        if rawBytes[5] & 0x80:
            self.ackFlag = True
        self.checksum =   (rawBytes[7] << 8) | rawBytes[6]

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
        self.checksum = 1738

        #TODO add header
        for i,field in enumerate(self.fields):
            if field.isPresent:
                dataArr += field.pack(i)

        for dat in dataArr:
            self.checksum += dat

        self.dataLen = len(dataArr)

        byteArr = struct.pack('<BBHHH', self.typeId, self.seq, self.dataLen, self.token, self.checksum)
        self.raw = byteArr + dataArr

        return self.raw

    def printJSON(self, meta= False):
        json = ""
        #json += ''.join(' {:02x}'.format(x) for x in self.raw) + "\n"
        json +="{ \"packetType\" : \""+ self.desc.name + "\""

        if meta:
            json+= ", \"typeId\": "  + str(self.typeId)
            json+= ", \"token\": \"" + '{:04x}'.format(self.token) + "\""
            json+= ", \"token\": \"" + '{:04x}'.format(self.checksum) + "\""
            json+= ", \"len\": "  + str(self.dataLen) + " "


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
        self.name = ""

        words = connStr.split(':')

        if words[0] == 'udp':
            self.coms = PolyUdp(self, int(words[1]))
            self.name = "UDP"
            if len(words) == 3:
                self.coms.connect('127.0.0.1', int(words[2]))
            if len(words) == 4:
                self.coms.connect(words[2], int(words[3]))

            self.coms.start()

    def close(self):
        self.coms.close()

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

            decoded = cobs.decode(encodedPacket)

            #self.print(" PARSE: " + ''.join(' {:02x}'.format(x) for x in decoded))

            newPacket.parse(decoded)


            self.print( " <-- " + newPacket.printJSON(self.service.showMeta))
            resp = newPacket.handler(self)
            if resp:
                self.sendPacket(resp)
            #self.packetsIn.append(newPacket)

    def sendPacket(self, packet):

        if packet.desc.name == "Ping":
            packet.setField('icd', self.service.protocol.crc)

        raw = packet.pack()

        #self.print(" PACK: " + ''.join(' {:02x}'.format(x) for x in raw))

        encoded = cobs.encode(bytearray(raw))
        encoded += bytes([0])

        self.print( " --> " + packet.printJSON(self.service.showMeta))

        self.coms.send(encoded)

        return encoded


    def getPacket(self):
        if len(packetsIn) > 0:
            return packetsIn.popleft()



class PolyService:
    def __init__(self, protocol):
        self.protocol = protocol
        self.interfaces = []
        self.print = ''
        self.showMeta = False
        self.autoAck = True
        self.handlers = {}

    def close(self):
        for iface in self.interfaces:
            iface.close()

    def addIface(self, connStr):
        self.interfaces.append(PolyIface(connStr, self))

    def newPacket(self, type):
        packet = PolyPacket(self.protocol)

        if type in self.protocol.packetIdx:
            packet.build(self.protocol.packetIdx[type])
        else:
            self.print(" Packet Type \"" + type + "\", not found!")

        return packet

    def newStruct(self, type):
        return self.newPacket(type)
    #
    # def process(self):
    #     for iface in self.interfaces:
    #         if iface.frameCount > 0:
