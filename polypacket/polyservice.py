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
import serial





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

    return int(val), int(size)


class PolySerial (threading.Thread):
    def __init__(self, iface, port, baud ):
        threading.Thread.__init__(self)
        self.iface = iface
        self.port = port
        self.baud = baud
        self.opened = False
        try:
            self.serialPort = serial.Serial(
                port = port,
                baudrate=baud,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize= serial.EIGHTBITS
            )
            self.opened = True
            self.iface.print(self.iface.name + " Port Opened : " + port)
        except serial.SerialException as e:
            print(e)
            self.iface.print(self.iface.name + " Could not open port : " + port)


    def __del__(self):
        self.close()
        self.join()     #stop thread


    def close(self):
        if self.opened:
            self.serialPort.close()


    def send(self, data):
        if self.opened:
            self.serialPort.write(data)

    def run(self):
        if self.opened:
            while True:
                if self.serialPort.inWaiting() > 0:
                    data = self.serialPort.read()
                    self.iface.feedEncodedBytes(data)


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
                        self.iface.service.print(" Connection Accepted: " + str(self.host))
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
        if type(val) != 'str':
            val = str(val)

        if val in self.desc.valDict:
            self.len = 1
            self.values[0] = self.desc.valDict[val]
        else:
            if self.desc.isArray and not self.desc.isString:
                val = val.replace('[','').replace(']','')
                arrVal = val.split(',')
                self.len = len(arrVal)
                self.values = []
                for v in arrVal:
                    self.values.append( int(v, 0))
            else:
                if self.desc.isString:
                    self.len = len(val)
                    self.values[0] = val
                else:
                    self.len = 1
                    self.values[0] = int(val, 0)


    def get(self):
        if self.isPresent :
            if self.desc.isArray and not self.desc.isString :
                return self.values
            else:
                return self.values[0]
        else:
            return -1

    def parse(self, bytes):
        self.isPresent = True
        strFormat = "%s"+ self.desc.pyFormat
        idx =0
        if self.desc.isArray and not self.desc.isString:
            self.len, idx = readVarSize(bytes)
            self.len = int(self.len / self.desc.objSize)
        else:
            if self.desc.isString:
                self.len, idx = readVarSize(bytes)
            else:
                self.len = 1

        if self.len == 0:
            if self.desc.isString:
                self.values[0] =""
            else:
                self.values[0] = 0

        dataLen = int(self.len * self.desc.objSize)

        strFormat = "<" + str(self.len) + self.desc.pyFormat;

        try:
            if self.desc.isString:
                self.values[0] = struct.unpack(strFormat, bytes[idx:idx+dataLen ])[0].decode("utf-8")
            else:
                self.values = struct.unpack(strFormat, bytes[idx:idx+dataLen])
        except:
            print(strFormat)
            print(idx)
            print (dataLen)
            print(len(bytes))
            print(" Error Parsing: " + self.desc.name+ '-->' + ''.join(' {:02x}'.format(x) for x in bytes[idx:idx+dataLen]))
        return idx + dataLen

    def pack(self, id):
        byteArr = bytes([])

        strFormat = "<" + str(self.len)+ self.desc.pyFormat

        byteArr += packVarSize(id)

        if self.desc.isArray :
            byteArr += packVarSize(self.len * self.desc.objSize)


        if self.desc.isString:
            byteArr+= struct.pack("<" +str(self.len) + "s", self.values[0].encode('utf-8'))
        else:
            byteArr+= struct.pack(strFormat, *self.values)

        return byteArr

    def printJSON(self):
        json =""
        json += "\"" + self.desc.name +"\" : "
        if self.desc.isArray and not self.desc.isString:
            json+= "[" + ''.join(' 0x{:02x},'.format(x) for x in self.values) + "]"
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
        self.autoAck = True
        self.ackFlag = False

    def setField(self, fieldName, value):
        for field in self.fields:
            if fieldName.lower() == field.desc.name.lower():
                field.set(value)
                break

    def getField(self, fieldName):
        for field in self.fields:
            if fieldName.lower() == field.desc.name.lower():
                return field.get()
        return -1



    def build(self, typeId):
        self.typeId = typeId
        self.desc = self.protocol.structsAndPackets[typeId]
        for fieldDesc in self.desc.fields:
            self.fields.append( PolyField(fieldDesc))

    def copyTo(self, packet):
        return 0

    def handler(self, iface):

        #dont respond to acks
        if self.ackFlag:
            if self.desc.name in iface.service.handlers:
                iface.service.handlers[self.desc.name](iface.service,self,None )
            elif 'default' in iface.service.handlers:
                iface.service.handlers['default'](iface.service, self,None)
            return 0

        if not iface.service.autoAck:
            return 0

        resp = 0

        if self.desc.hasResponse:
            resp =  iface.service.newPacket(self.desc.response.name)
        elif iface.service.autoAck:
            resp = iface.service.newPacket('Ack')

        if self.desc.name in iface.service.handlers:
            iface.service.handlers[self.desc.name](iface.service,self,resp)
        elif 'default' in iface.service.handlers:
            iface.service.handlers['default'](iface.service, self,resp)


        if not resp == 0:
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
            json+= ", \"checksum\": \"" + '{:04x}'.format(self.checksum) + "\""
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
        self.lastToken = 0

        if not connStr == "":
            words = connStr.split(':')

            if words[0] == 'udp':
                try:
                    self.coms = PolyUdp(self, int(words[1]))
                    self.name = "UDP"
                    if len(words) == 3:
                        self.coms.connect('127.0.0.1', int(words[2]))
                    if len(words) == 4:
                        self.coms.connect(words[2], int(words[3]))
                    
                    self.coms.daemon = True
                    self.coms.start()
                except:
                    self.print( "Invalid connection string\n udp:local-port to open a port\n udp:local-port:ip:remote-port to target remote port ")

            elif words[0] == 'serial':
                try:
                    if len(words) == 2:
                        self.coms = PolySerial(self,words[1], 9600)
                    if len(words) == 3:
                        self.coms = PolySerial(self,words[1], words[2])

                    self.coms.daemon = True
                    self.coms.start()
                except:
                    self.print( "Invalid connection string\n serial:/dev/ttyS[COM Number]:baud")
                    
    def close(self):
        if hasattr(self, 'coms'):
            self.coms.close()

    def print(self, text):
        if not self.service.print == '':
            self.service.print( text)

    def feedEncodedBytes(self, encodedBytes):

        silent = False

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

            newPacket.parse(decoded)

            if self.service.silenceDict[newPacket.desc.name]:
                silent = True

            if not silent:
                if self.service.showBytes:
                    self.print(" PARSE HDR: " + ''.join(' {:02x}'.format(x) for x in decoded[:8]))
                    self.print(" PARSE DATA: " + ''.join(' {:02x}'.format(x) for x in decoded[8:]))
                if (newPacket.token & 0x7FFF) != (self.lastToken & 0x7FFF):
                    self.print("")

                self.print( " <-- " + newPacket.printJSON(self.service.showMeta))

            resp = newPacket.handler(self)
            self.lastToken = newPacket.token
            if resp:
                self.sendPacket(resp, silent)
            #self.packetsIn.append(newPacket)

    def sendPacket(self, packet, silent = False):

        if packet.desc.name == "Ping":
            packet.setField('icd', str(self.service.protocol.crc))

        if (packet.token & 0x7FFF) != (self.lastToken & 0x7FFF):
            self.print("")

        if not silent:
            self.print( " --> " + packet.printJSON(self.service.showMeta))

        raw = packet.pack()

        if self.service.showBytes and not silent:
            self.print(" PACK HDR: " + ''.join(' {:02x}'.format(x) for x in raw[:8]))
            self.print(" PACK DATA: " + ''.join(' {:02x}'.format(x) for x in raw[8:]))

        encoded = cobs.encode(bytearray(raw))
        encoded += bytes([0])


        if hasattr(self, 'coms'):
            self.coms.send(encoded)

        self.lastToken = packet.token

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
        self.silenceDict = {}
        self.showBytes = False
        self.dataStore = {}

        for packet in protocol.packets:
            self.silenceDict[packet.name] = False

        self.addIface("") #add dummy interface that just prints

    def close(self):
        for iface in self.interfaces:
            iface.close()

    def addIface(self, connStr):
        self.interfaces.append(PolyIface(connStr, self))

    def setIface(self,connStr):
        self.interfaces[0].close()
        self.interfaces[0] = PolyIface(connStr, self)

    def toggleAck(self):
        if self.autoAck:
            self.autoAck = False
            self.print( "AutoAck turned OFF")
        else:
            self.autoAck = True
            self.print( "AutoAck turned ON")

    def toggleSilence(self, packetType):

        if not packetType in self.silenceDict:
            self.print( "Can not find: " + packetType)

        if self.silenceDict[packetType]:
            self.silenceDict[packetType] = False
            self.print( "Un-Silencing: " + packetType)
        else:
            self.silenceDict[packetType] = True
            self.print( "Silencing: " + packetType)

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
