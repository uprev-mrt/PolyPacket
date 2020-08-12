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
import yaml


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

pyFormatDict = {
        "uint8" : "B",
        "int8" : "b",
        "char" : "c",
        "string" : "s",
        "uint16" : "H",
        "int16" : "h",
        "uint32" : "L",
        "int32" : "l",
        "int64" : "q",
        "uint64" : "Q",
        "int" : "l",
        "float": "f",
        "double": "d",
}


def crc(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)


    return prev,"%X"%(prev & 0xFFFFFFFF)

class simulator:
    def __init__(self,name, simItem):
        self.init =""
        self.handlers = {}
        self.name = name
        
        if 'init' in simItem:
            self.init = simItem['init']

        for handler in simItem['handlers']:
            name = list(handler.keys())[0]
            code  = list(handler.values())[0]
            self.handlers[name] = code

class fieldVal:
    def __init__(self, name):
        self.name = name.upper()
        self.desc = ""
        self.val = None
        

class fieldDesc:
    def __init__(self, name, strType):
        self.vals = []
        self.valDict = {}
        self.arrayLen = 1
        self.isEnum = False
        self.isMask = False
        self.valsFormat = "0x%0.2X"
        self.valIndex = 0

        self.format = 'FORMAT_DEFAULT'

        if strType in ['flag','flags','mask','bits']:
            self.format = 'FORMAT_HEX'
            self.isMask = True
            strType = 'uint8_t'

        if strType in ['enum','enums']:
            self.format = 'FORMAT_HEX'
            self.isEnum = True
            strType = 'uint8_t'

        m = re.search('\*([0-9]*)', strType)
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
        self.objSize = sizeDict[self.type]
        self.pyFormat = pyFormatDict[self.type]
        self.cType = cNameDict[self.type]
        self.cppType = self.cType

        self.isString = False
        self.isArray = False

        if(self.arrayLen > 1):
            self.isArray = True

        if(self.type == 'string'):
            self.cppType = "string"
            self.isString = True
            self.isArray = True
            if(self.arrayLen == 1):
                self.arrayLen = 32 #if no arraylen is specified default 32
        else:
            if(self.isArray):
                self.cppType = self.cppType +"*"

    def addVal(self, val):
 
        self.valDict[val.name] = len(self.vals) -1

        if self.isMask:
            val.val = 1 << self.valIndex
            self.valIndex+=1
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
        
        elif self.isEnum:
            val.val =  self.valIndex
            self.valIndex+=1

        self.valDict[val.name] = val.val
        self.vals.append(val)
    

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
    def __init__(self,name, protocol):
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
        self.protocol = protocol
        self.requiredFields = []
        self.requiredFieldCount = 0

    def camel(self):
        return self.name[:1].capitalize() + self.name[1:]

    def setPrefix(self, prefix):
        self.globalName = prefix.upper()+"_PACKET_"+self.name.upper()

    def addField(self, field):
        field.id = self.fieldCount
        self.fields.append(field)
        self.fieldCount+=1

    def addYAMLField(self, pfieldItem):

        if type(pfieldItem) is dict:
            pfname = list(pfieldItem.keys())[0]
            pfield = list(pfieldItem.values())[0]
        else:
            pfname = pfieldItem
            pfield = {}

        strReq =""
        if not (pfname in self.protocol.fieldIdx):
            print( 'ERROR Field not declared: ' + pfname)

        #get id of field and make a copy
        idx = self.protocol.fieldIdx[pfname]
        fieldCopy = copy.copy(self.protocol.fields[idx])

        if('req' in pfield):
            fieldCopy.isRequired = pfield['req']

        if('desc' in pfield):
            fieldCopy.desc = pfield['desc']

        fieldCopy.id = self.fieldCount
        self.fields.append(fieldCopy)
        self.fieldCount+=1

    def postProcess(self):
        if len(self.requests) > 0:
            self.hasResponse = True;
            self.response = self.protocol.getPacket(next(iter(self.requests.keys())))

        for field in self.fields:
            if field.isRequired:
                self.requiredFields.append(field)
                self.requiredFieldCount += 1

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
        self.cppFileName = name+"Service"
        self.desc = ""
        self.hash = ""
        self.fields = []
        self.fieldIdx = {}
        self.fieldId =0
        self.fieldGroups = {}
        self.packets = []
        self.packetIdx ={}
        self.packetId =0
        self.structs =[]
        self.structsAndPackets=[]
        self.structIdx ={}
        self.structId =0
        self.prefix = "pp"
        self.snippets = False
        self.genUtility = False
        self.xmlName =""
        self.utilName =""
        self.sims = {}
        self.defaultResponse = ""

    def service(self):
        return self.prefix.upper() +'_SERVICE'

    def descFromId(self, typeId):
        return self.packets[typeId-len(self.structs)]

    def fieldDescFromId(self, typeId):
        return self.fields[typeId]

    def camelPrefix(self):
        return self.prefix[:1].capitalize() + self.prefix[1:]

    def addField(self,field):
        field.id = self.fieldId
        field.protocol = self
        self.fields.append(field)
        self.fieldIdx[field.name] = self.fieldId
        self.fieldId+=1

    def addGroup(self, name, fields):
        self.fieldGroups[name] = fields

    def addPacket(self,packet):
        packet.packetId = self.packetId
        packet.protocol = self
        packet.setPrefix(self.prefix)
        self.packets.append(packet)
        self.structsAndPackets.append(packet)
        self.packetIdx[packet.name] = self.packetId
        self.packetId+=1

    def addStruct(self,struct):
        struct.packetId = self.packetId
        struct.protocol = self
        struct.struct = True
        struct.globalName = self.prefix.upper()+"_STRUCT_"+struct.name.upper()
        self.structs.append(struct)
        self.structsAndPackets.append(struct)
        self.structIdx[struct.name] = self.packetId
        self.packetId+=1

    def getPacket(self, name):
        if name in self.packetIdx:
            return self.structsAndPackets[self.packetIdx[name]]




def addStandardPackets(protocol):
    ping = packetDesc("Ping", protocol)
    ack = packetDesc("Ack", protocol)
    icd = fieldDesc("icd", "uint32")
    icd.isRequired = True
    icd.setPrefix(protocol.prefix)
    icd.desc = "CRC Hash of protocol description. This is used to verify endpoints are using the same protocol"
    ping.desc = "This message requests an Ack from a remote device to test connectivity"
    ping.response = ack
    ping.hasResponse = True
    ping.requests['Ack'] =0
    ack.desc ="Acknowledges any packet that does not have an explicit response"
    ping.standard = True
    ack.standard = True
    protocol.addField(icd)
    ping.addField(icd)
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
        newPacket = packetDesc(name, protocol)
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
        newStruct = packetDesc(name, protocol)


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


def parseYAMLField(protocol, fieldItem):
    name = list(fieldItem.keys())[0]
    field = list(fieldItem.values())[0]

    strType = field['type'].replace("(","[").replace(")","]");

    newField = fieldDesc(name, strType)
    newField.setPrefix(protocol.prefix)

    if('format' in field):
        format = field['format'].lower()
        if not format in formatDict:
            print( "INVALID FORMAT :" + format)

        newField.format = formatDict[format]

    if 'req' in field:
        newField.isRequired = field['req']

    if 'required' in field:
        newField.isRequired = field['required']

    if('desc' in field):
        newField.desc = field['desc']

    if(name in protocol.fields):
        print( 'ERROR Duplicate Field Name!: ' + name)

    #get vals if any
    if "vals" in field:
        for valItem in field['vals']:
            if type(valItem) is dict:
                name = list(valItem.keys())[0]
                val = list(valItem.values())[0]
            else:
                name = valItem
                val = {}

            newVal = fieldVal(name)

            if('val' in val):
                newVal.val = val['val']

            if('desc' in val):
                newVal.desc = val['desc']

            newField.addVal(newVal)

    protocol.addField(newField)
    return newField

def parseYAML(yamlFile):
    data = open(yamlFile)
    objProtocol = yaml.load(data , Loader=yaml.FullLoader)

    protocol = protocolDesc(objProtocol['name'])

    if "prefix" in objProtocol:
        protocol.prefix = objProtocol['prefix']

    if "desc" in objProtocol:
        protocol.desc = objProtocol['desc']

    if "defaultResponse" in objProtocol:
        protocol.defaultResponse = objProtocol['defaultResponse']

    addStandardPackets(protocol)

    protocol.xmlName = os.path.basename(yamlFile)

    for fieldItem in objProtocol['fields']:

        nodeType = list(fieldItem.values())[0]

        #all fields must have a 'type', so if it doesnt, then it is a field group
        if not 'type' in list(fieldItem.values())[0]:
            groupName = list(fieldItem.keys())[0]
            fieldGroupItems = list(fieldItem.values())[0]
            groupFields = []
            for fieldGroupItem in fieldGroupItems:
                newField = parseYAMLField(protocol, fieldGroupItem)
                groupFields.append(newField.name)
            protocol.addGroup(groupName, groupFields)
        else:
            parseYAMLField(protocol, fieldItem)

    if 'structs' in  objProtocol:
        for structItem in objProtocol['structs']:
            name = list(structItem.keys())[0]
            struct = list(structItem.values())[0]
            desc =""
            newStruct = packetDesc(name,protocol)


            if(name in protocol.structIdx):
                print( 'ERROR Duplicate Struct Name!: ' + name)

            if('desc' in struct):
                desc = struct['desc']

            #get all fields declared for packet
            if "fields" in struct:
                for pfieldItem in struct['fields']:

                    if type(pfieldItem) is dict:
                        pfname = list(pfieldItem.keys())[0]
                        pfield = list(pfieldItem.values())[0]
                    else:
                        pfname = pfieldItem
                        pfield = {}


                    if pfname in protocol.fieldGroups:
                        for pfFieldGroupItem in protocol.fieldGroups[pfname]:
                            newStruct.addYAMLField(pfFieldGroupItem)
                    else:
                        newStruct.addYAMLField(pfieldItem)

            newStruct.desc = desc

            protocol.addStruct(newStruct)

    if 'packets' in  objProtocol:
        for packetItem in objProtocol['packets']:
            name = list(packetItem.keys())[0]
            packet = list(packetItem.values())[0]
            desc =""
            newPacket = packetDesc(name, protocol)
            newPacket.setPrefix(protocol.prefix)

            if(name in protocol.packetIdx):
                print( 'ERROR Duplicate Packet Name!: ' + name)

            if('desc' in packet):
                desc = packet['desc']

            if('response' in packet):
                if (packet['response'] != "none"):
                    newPacket.requests[packet['response']] = 0
            else:
                if not protocol.defaultResponse == "" and not  protocol.defaultResponse == newPacket.name :
                    newPacket.requests[protocol.defaultResponse] = 0

            #get all fields declared for packet
            if "fields" in packet:
                for pfieldItem in packet['fields']:

                    if type(pfieldItem) is dict:
                        pfname = list(pfieldItem.keys())[0]
                        pfield = list(pfieldItem.values())[0]
                    else:
                        pfname = pfieldItem
                        pfield = {}


                    if pfname in protocol.fieldGroups:
                        for pfFieldGroupItem in protocol.fieldGroups[pfname]:
                            newPacket.addYAMLField(pfFieldGroupItem)
                    else:
                        newPacket.addYAMLField(pfieldItem)

            newPacket.desc = desc

            protocol.addPacket(newPacket)


    if 'sims' in  objProtocol: #experimental
        for simItem in objProtocol['sims']:
            name = list(simItem.keys())[0]
            sim = list(simItem.values())[0]
            protocol.sims[name] = simulator(name,sim)
    
    for packet in protocol.packets:
        for request in packet.requests.keys():
            protocol.getPacket(request).respondsTo[packet.name] = 0

    for packet in protocol.packets:
        packet.postProcess()


    # return news items list
    return protocol

def buildProtocol(file):
    extension = os.path.splitext(file)[1]

    if(extension == ".xml"):
        print(" XML files are depreciated. Please convert to YAML for future use")
        return parseXML(file)

    elif(extension == ".yml"):
        return parseYAML(file)

    else:
        print(" Files Type: " + extension+" Not supported. Please use YAML")

    return 0
