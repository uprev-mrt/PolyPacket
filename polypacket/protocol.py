import sys
import xml.etree.ElementTree as ET
import re
import io
import os
import copy
import datetime
import zlib
import argparse
#import pdfkit
from shutil import copyfile
from mako.template import Template
import pkgutil
import polypacket
import subprocess
import hjson


sizeDict = {
    "uint8" : 1,
    "int8" : 1,
    "char" : 1,
    "string" : 1,
    "uint16" : 2,
    "int16" : 2,
    "uint32" : 4,
    "int32" : 4,
    "int64" : 8,
    "uint64" : 8,
    "int" : 4,
    "float": 4,
    "double": 8,
}

cNameDict = {
    "uint8" : "uint8_t",
     "int8" : "int8_t",
     "char" : "char",
     "string" : "char",
     "uint16" : "uint16_t",
     "int16" : "int16_t",
     "uint32" : "uint32_t",
     "int32" : "int32_t",
     "int64" : "int64_t",
     "uint64" : "uint64_t",
     "int" : "int",
     "float" : "float",
     "double" : "double",
     "enum" : "uint8_t",
     "flag" : "uint8_t"
 }

formatDict = {
    "hex" : "FORMAT_HEX",
    "dec" : "FORMAT_DEC",
    "default" : "FORMAT_DEFAULT",
    "ascii" : "FORMAT_ASCII",
    "none" : "FORMAT_NONE"
}


def crc(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X"%(prev & 0xFFFFFFFF)


class fieldVal:
    def __init__(self, name):
        self.name = name.upper()
        self.desc = ""

class fieldDesc:
    def __init__(self, name, strType):
        self.vals = []
        self.arrayLen = 1
        self.isEnum = False
        self.isMask = False
        self.valsFormat = "0x%0.2X"

        self.format = 'FORMAT_DEFAULT'

        if strType in ['flag','flags','mask','bits']:
            self.format = 'FORMAT_HEX'
            self.isMask = True
            strType = 'uint8_t'

        if strType in ['enum','enums']:
            self.format = 'FORMAT_HEX'
            self.isEnum = True
            strType = 'uint8_t'

        m = re.search('\[([0-9]*)\]', strType)
        if(m):
            if(m.group(1) != ''):
                self.arrayLen = int(m.group(1))
            strType = strType[0:m.start()]


        strType = strType.lower().replace('_t','')

        self.setType(strType, self.arrayLen)

        self.id = 0
        self.name = name
        self.globalName = "PP_FIELD_"+self.name.upper()
        self.isVarLen = False
        self.isRequired = False
        self.desc = ""
        self.memberName = "m"+ self.name.capitalize()

    def camel(self):
        return self.name[:1].capitalize() + self.name[1:]

    def setType(self, type, len):

        if not (type in cNameDict):
            print( "INVALID DATA TYPE!:  " + type)

        self.arrayLen = len
        self.type = type
        self.size = sizeDict[self.type] * self.arrayLen
        self.cType = cNameDict[self.type]
        self.cppType = self.cType

        self.isString = False
        self.isArray = False

        if(self.arrayLen > 1):
            self.isArray = True

        if(self.type == 'string'):
            self.cppType = "string"
            self.isString = True
        else:
            if(self.isArray):
                self.cppType = self.cppType +"*"

    def addVal(self, val):
        self.vals.append(val)

        if self.isMask:
            strType = 'uint8'
            if len(self.vals) > 8:
                self.valsFormat = "0x%0.4X"
                strType = 'uint16'
            if len(self.vals) > 16:
                self.valsFormat = "0x%0.8X"
                strType = 'uint32'
            if len(self.vals) > 32:
                print( "Error maximum flags per field is 32")
            self.setType(strType,1)

    def setPrefix(self, prefix):
        self.globalName = prefix.upper()+"_FIELD_"+self.name.upper()

    def getFieldDeclaration(self):
        output = io.StringIO()
        output.write("{0} field_{1}".format(self.cType, self.name))
        if(self.arrayLen > 1):
            output.write("["+str(self.arrayLen)+"]")

        return output.getvalue()

    def getParamType(self):
        if self.isArray:
            return self.cType +"*"
        else:
            return self.cType;

    def getDeclaration(self):
        if self.isArray:
            return self.cType +" "+self.name+"["+ str(self.arrayLen)+"]"
        else:
            return self.cType + " " + self.name;

    def getFormat(self):
        if self.isString:
            return "%s"
        else:
            return "%i"



class packetDesc:
    def __init__(self, name):
        self.name = name
        self.globalName =  "PP_PACKET_"+self.name.upper()
        self.className = name.capitalize() +"Packet"
        self.desc =""
        self.fields = []
        self.sruct = False
        self.fieldCount=0
        self.respondsTo = {}
        self.requests = {}
        self.standard = False
        self.structName = name.lower() + '_packet_t'
        self.hasResponse = False

    def camel(self):
        return self.name[:1].capitalize() + self.name[1:]

    def setPrefix(self, prefix):
        self.globalName = prefix.upper()+"_PACKET_"+self.name.upper()

    def addField(self, field):
        field.id = self.fieldCount
        self.fields.append(field)
        self.fieldCount+=1

    def postProcess(self):
        if len(self.requests) > 0:
            self.hasResponse = True;
            self.response = self.protocol.getPacket(next(iter(self.requests.keys())))

    def tableSize(self):
        sum =0;
        for field in self.fields:
            if field.size > 4:
                sum+=4
            else:
                sum += field.size

        return sum


    def getDocMd(self):
        output = io.StringIO()
        idHex = "%0.2X" % self.packetId
        output.write('### '  + self.name + '\n')
        output.write(self.desc + '\n\n')
        output.write('* Packet ID: *['+idHex+']*\n')
        requestCount = len(self.requests)
        respondsToCount = len(self.respondsTo)

        #write response packets
        if(requestCount > 0):
            output.write('* *Requests: ')
            first = True
            for req in self.requests:
                if(first):
                    first = False
                else:
                    output.write(', ')
                output.write(req)
            output.write('*\n\n')

        #write request packets
        if(self.name == 'Ack'):
            output.write('* *Responds To: Any Packet without a defined response*\n\n')
        else:
            if(respondsToCount > 0):
                output.write('* *Responds To: ')
                first = True
                for resp in self.respondsTo:
                    if(first):
                        first = False
                    else:
                        output.write(', ')
                    output.write(resp)
                output.write('*\n')

        output.write('\n')

        rowBytes = io.StringIO()
        rowBorder = io.StringIO()
        rowFields = io.StringIO()
        rowTypes = io.StringIO()


        if(len(self.fields) > 0):
            rowBytes.write('|***Byte***|')
            rowBorder.write('|---|')
            rowFields.write('|***Field***')
            rowTypes.write('|***Type***')

            count =0

            for pfield in self.fields:

                #write bytes
                if(pfield.size > 4):
                    rowBytes.write(str(count)+'| . . . . . . . |'+str(count+pfield.size -1))
                    count+=pfield.size
                else:
                    for x in range(pfield.size):
                        rowBytes.write(str(count) + '|')
                        count+=1

                #write border
                span = pfield.size
                if(span > 4):
                    span = 4
                for x in range(span):
                    rowBorder.write('---|')

                #write fields
                span = pfield.size
                if(span > 4):
                    span = 4
                rowFields.write('<td colspan=\''+str(span)+'\'>')
                if(pfield.isRequired):
                    rowFields.write('***'+pfield.name+'***')
                else:
                    rowFields.write(pfield.name)

                #write types
                span = pfield.size
                if(span > 4):
                    span = 4
                rowTypes.write('<td colspan=\''+str(span)+'\'>')
                rowTypes.write(pfield.cType)
                if(pfield.isArray):
                    if(pfield.isVarLen):
                        rowTypes.write('[0-'+ str(pfield.size)+' ]')
                    else:
                        rowTypes.write('['+str(pfield.size)+']')

            #combine rows for table
            output.write(rowBytes.getvalue() + "\n");
            output.write(rowBorder.getvalue() + "\n");
            output.write(rowFields.getvalue() + "\n");
            output.write(rowTypes.getvalue() + "\n");

            output.write('\n\n')
            output.write('Fields:\n')
            #write field description table
            for pfield in self.fields:
                output.write('>***'+ pfield.name+'*** : ' + pfield.desc +'<br/>\n')
                if pfield.isMask:
                    for idx,val in enumerate(pfield.vals):
                        strVal = pfield.valsFormat % (1 << idx)
                        output.write('>> **{0}** : {1} - {2}<br/>\n'.format(strVal, val.name, val.desc))
                    output.write('>\n')

                if pfield.isEnum:
                    for idx,val in enumerate(pfield.vals):
                        strVal = pfield.valsFormat % (idx)
                        output.write('>> **{0}** : {1} - {2}<br/>\n'.format(strVal, val.name, val.desc))
                    output.write('>\n')
        else:
            output.write('>This Packet type does not contain any data fields\n\n')

        output.write('\n------\n')

        return output.getvalue();



class protocolDesc:
    def __init__(self, name):
        self.name = name
        self.fileName = name+"Service"
        self.desc = ""
        self.hash = ""
        self.fields = []
        self.fieldIdx = {}
        self.fieldId =0
        self.packets = []
        self.packetIdx ={}
        self.packetId =0
        self.structs =[]
        self.structIdx ={}
        self.structId =0
        self.prefix = "pp"
        self.snippets = False
        self.genUtility = False
        self.xmlName =""
        self.utilName =""

    def service(self):
        return self.prefix.upper() +'_SERVICE'

    def addField(self,field):
        field.id = self.fieldId
        field.protocol = self
        self.fields.append(field)
        self.fieldIdx[field.name] = self.fieldId
        self.fieldId+=1


    def addPacket(self,packet):
        packet.packetId = self.packetId
        packet.protocol = self
        packet.setPrefix(self.prefix)
        self.packets.append(packet)
        self.packetIdx[packet.name] = self.packetId
        self.packetId+=1

    def addStruct(self,struct):
        struct.packetId = self.packetId
        struct.protocol = self
        struct.struct = True
        struct.globalName = self.prefix.upper()+"_STRUCT_"+struct.name.upper()
        self.structs.append(struct)
        self.structIdx[struct.name] = self.packetId
        self.packetId+=1

    def getPacket(self, name):
        if name in self.packetIdx:
            return self.packets[self.packetIdx[name]]




def addStandardPackets(protocol):
    ping = packetDesc("Ping")
    ack = packetDesc("Ack")
    ping.desc = "This message requests an Ack from a remote device to test connectivity"
    ping.response = ack
    ping.hasResponse = True
    ping.requests['Ack'] =0
    ack.desc ="Acknowledges any packet that does not have an explicit response"
    ping.standard = True
    ack.standard = True
    protocol.addPacket(ping)
    protocol.addPacket(ack)

def parseXML(xmlfile):

    # create element tree object
    tree = ET.parse(xmlfile)

    # get root element
    root = tree.getroot()

    # create empty list for Fields
    protocol = protocolDesc(root.attrib['name'])
    protocol.xmlName = os.path.basename(xmlfile)


    if('desc' in root.attrib):
        protocol.desc = root.attrib['desc']

    if('prefix' in root.attrib):
        protocol.prefix = root.attrib['prefix']

    addStandardPackets(protocol)

    #parse out fields
    for field in root.findall('./Fields/Field'):

        name = field.attrib['name']
        strType = field.attrib['type'];

        newField = fieldDesc(name, strType)
        newField.setPrefix(protocol.prefix)

        if('format' in field.attrib):
            format = field.attrib['format'].lower()
            if not format in formatDict:
                print( "INVALID FORMAT :" + format)

            newField.format = formatDict[format]

        if('desc' in field.attrib):
            newField.desc = field.attrib['desc']

        if(name in protocol.fields):
            print( 'ERROR Duplicate Field Name!: ' + name)

        #get vals if any
        for val in field.findall('./Val'):
            name = val.attrib['name']
            newVal = fieldVal(name)

            if('desc' in val.attrib):
                newVal.desc = val.attrib['desc']

            newField.addVal(newVal)



        protocol.addField(newField)


    #get all packet types
    for packet in root.findall('./Packets/Packet'):
        name = packet.attrib['name']
        desc =""
        newPacket = packetDesc(name)
        newPacket.setPrefix(protocol.prefix)

        if(name in protocol.packetIdx):
            print( 'ERROR Duplicate Packet Name!: ' + name)

        if('desc' in packet.attrib):
            desc = packet.attrib['desc']

        if('response' in packet.attrib):
            newPacket.requests[packet.attrib['response']] = 0

        #get all fields declared for packet
        for pfield in packet:

            pfname = pfield.attrib['name']
            strReq =""
            if not (pfname in protocol.fieldIdx):
                print( 'ERROR Field not declared: ' + pfname)

            #get id of field and make a copy
            idx = protocol.fieldIdx[pfname]
            fieldCopy = copy.copy(protocol.fields[idx])

            if('req' in pfield.attrib):
                strReq = pfield.attrib['req']
                if(strReq.lower() == "true" ):
                    fieldCopy.isRequired = True

            if('desc' in pfield.attrib):
                fieldCopy.desc = pfield.attrib['desc']

            newPacket.addField(fieldCopy)

        newPacket.desc = desc

        protocol.addPacket(newPacket)

    #get all packet types
    for struct in root.findall('./Structs/Struct'):
        name = struct.attrib['name']
        desc =""
        newStruct = packetDesc(name)


        if(name in protocol.structIdx):
            print( 'ERROR Duplicate Struct Name!: ' + name)

        if('desc' in packet.attrib):
            desc = packet.attrib['desc']

        #get all fields declared for packet
        for pfield in struct:

            pfname = pfield.attrib['name']
            strReq =""
            if not (pfname in protocol.fieldIdx):
                print( 'ERROR Field not declared: ' + pfname)

            #get id of field and make a copy
            idx = protocol.fieldIdx[pfname]
            fieldCopy = copy.copy(protocol.fields[idx])


            if('desc' in pfield.attrib):
                fieldCopy.desc = pfield.attrib['desc']

            newStruct.addField(fieldCopy)

        newStruct.desc = desc

        protocol.addStruct(newStruct)


    for packet in protocol.packets:
        for request in packet.requests:
            idx = protocol.packetIdx[request]
            protocol.packets[idx].respondsTo[packet.name] = 0

    for packet in protocol.packets:
        packet.postProcess()


    # return news items list
    return protocol

def parseJSON(jsonFile):
    json = open(jsonFile)
    obj = hjson.load(json)

    objProtocol = obj['protocol']
    protocol = protocolDesc(objProtocol['name'])

    if "prefix" in objProtocol:
        protocol.prefix = objProtocol['prefix']
        
    if "desc" in objProtocol:
        protocol.desc = objProtocol['desc']

    addStandardPackets(protocol)

    protocol.xmlName = os.path.basename(jsonFile)

    for field in objProtocol['fields']:
        name = field['name']
        strType = field['type'];

        newField = fieldDesc(name, strType)
        newField.setPrefix(protocol.prefix)

        if('format' in field):
            format = field['format'].lower()
            if not format in formatDict:
                print( "INVALID FORMAT :" + format)

            newField.format = formatDict[format]

        if('desc' in field):
            newField.desc = field['desc']

        if(name in protocol.fields):
            print( 'ERROR Duplicate Field Name!: ' + name)

        #get vals if any
        if "vals" in field:
            for val in field['vals']:
                name = val['name']
                newVal = fieldVal(name)

                if('desc' in val):
                    newVal.desc = val['desc']

                newField.addVal(newVal)

        protocol.addField(newField)


    for packet in objProtocol['packets']:
        name = packet['name']
        desc =""
        newPacket = packetDesc(name)
        newPacket.setPrefix(protocol.prefix)

        if(name in protocol.packetIdx):
            print( 'ERROR Duplicate Packet Name!: ' + name)

        if('desc' in packet):
            desc = packet['desc']

        if('response' in packet):
            newPacket.requests[packet['response']] = 0

        #get all fields declared for packet
        if "fields" in packet:
            for pfield in packet['fields']:

                pfname = pfield['name']
                strReq =""
                if not (pfname in protocol.fieldIdx):
                    print( 'ERROR Field not declared: ' + pfname)

                #get id of field and make a copy
                idx = protocol.fieldIdx[pfname]
                fieldCopy = copy.copy(protocol.fields[idx])

                if('req' in pfield):
                    strReq = pfield['req']
                    if(strReq.lower() == "true" ):
                        fieldCopy.isRequired = True

                if('desc' in pfield):
                    fieldCopy.desc = pfield['desc']

                newPacket.addField(fieldCopy)

        newPacket.desc = desc

        protocol.addPacket(newPacket)

    for struct in objProtocol['structs']:
        name = struct['name']
        desc =""
        newStruct = packetDesc(name)


        if(name in protocol.structIdx):
            print( 'ERROR Duplicate Struct Name!: ' + name)

        if('desc' in packet):
            desc = packet['desc']

        #get all fields declared for packet
        if "fields" in struct:
            for pfield in struct['fields']:

                pfname = pfield['name']
                strReq =""
                if not (pfname in protocol.fieldIdx):
                    print( 'ERROR Field not declared: ' + pfname)

                #get id of field and make a copy
                idx = protocol.fieldIdx[pfname]
                fieldCopy = copy.copy(protocol.fields[idx])


                if('desc' in pfield):
                    fieldCopy.desc = pfield['desc']

                newStruct.addField(fieldCopy)

        newStruct.desc = desc

        protocol.addStruct(newStruct)


    for packet in protocol.packets:
        for request in packet.requests:
            idx = protocol.packetIdx[request]
            protocol.packets[idx].respondsTo[packet.name] = 0

    for packet in protocol.packets:
        packet.postProcess()


    # return news items list
    return protocol