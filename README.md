# PolyPacket

Poly Packet is backend and code generation tool for creating messaging protocols/Services. Protocols are described in an XML document which can be easily shared with all components of a system.

A python script is used to parse the XML file and generate code as well as documentation. The code generation tool can create the back end service, app layer, and even an entire linux utility app

## Protocol Generation

Protocols are generated using XML. The messaging structure is made up 3 entity types:

* Field
* Packet
* Val

## Fields
 A field is a data object within a message


example field:

```xml
<Field name="src" type="uint16_t" format="hex" desc="Source address of message" />
```
> **name**: The name of the field <br/>
> **type**: The data type for the field  <br/>
> **format**: (optional)  This sets the display format used for the toString and toJsonString methods [ hex , dec , assci ]  <br/>
> **desc**: (optional)  The description of the field. This is used to create the documentation  <br/>

## Packets
A Packet describes an entire message and is made up of fields

example Packet:

```xml
<Packet name="GetData" desc="Message to get data from node" response="RespData">
  <Field name="src" req="true"/>
  <Field name="dst" req="true" desc="address of node to retrieve data from"/>
</Packet>
```

> **name**: The name of the packet <br/>
> **desc**: (optional)  description of the packet for documentation <br/>
> **response**: (optional) name of the packet type expected in response to this message (if any)

within the packet we reference Fields which have already been declared in the Fields section. these references contain 3 attributes:

> **name**: The name of the field<br/>
> **req**: (optional)  makes the field a requirement for this packet type <br/>
> **desc**: (optional) description of this field for this packet type, will override fields description in the documentation for this packet type only

## Val
Val entities are used for defining options in **enum** and **flags** fields.

```xml
<Field name="cmd" type="enum" format="hex" desc="Command for device">
  <Val name="led_ON" desc="turns on led" />
  <Val name="led_OFF" desc="turns off led" />
  <Val name="reset" desc="resets the device" />
</Field>
```

In this example an enum is used to set up some predefined options for the **cmd** field. enums are created with sequential values starting at 0. a **flags** field is defined in the same way, but instead of sequential numbers, it shifts bits to the left, to create a group of individually set-able flags.

## Example:

The following example show the XML for a simple message protocol.


```xml
<?xml version="1.0" encoding="UTF-8"?>
<Protocol name="Sample" prefix="sp"
  desc="This is a sample protocol made up to demonstrate features of the PolyPacket code generation tool. The idea
  is to have a tool that can automatically create parseable/serializable messaging for embedded systems.">
  <!--First we declare all Field descriptors-->
  <Fields>

    <!--Common -->
    <Field name="cmd" type="enum" format="hex" desc="Command for device">
      <Val name="led_ON" desc="turns on led" />
      <Val name="led_OFF" desc="turns off led" />
      <Val name="reset" desc="resets the device" />
    </Field>

    <!-- SensorData -->
    <Field name="sensorA" type="int16" format="dec" desc="Value of Sensor A"/>
    <Field name="sensorB" type="int" format="dec" desc="Value of Sensor B" />
    <Field name="sensorName" type="string[32]" format="ascii" desc="Name of sensor"/>

  </Fields>
  <!--Declare all Packet Types-->
  <Packets>
    <Packet name="SendCmd" desc="Message to set command in node" >
      <Field name="cmd" req="true"/>
    </Packet>

    <Packet name="GetData" desc="Message to get data from node" response="Data">
    </Packet>

    <Packet name="Data" desc="Message containing data from sensor" >
      <Field name="sensorA"/>
      <Field name="sensorB"/>
      <!-- Adding a description here will overwrite the description in documentation for this packet type -->
      <Field name="sensorName" desc="Name of sensor responding to message "/>
    </Packet>

  </Packets>
</Protocol>

```
The XML sets up 3 Fields:

**cmd** - Command for device </br>
**sensorA** - Value of Sensor A <br/>
**sensorB** - Value of Sensor B <br/>
**sensorName** - Name of sensor <br/>

It then lists the packets, and which fields are in each packet. fields are considered optional in a packet unless specified with **req="true"**. So in this example you could send a Data packet that only contained sensorB and sensorName.

## Using Poly Packet

To use poly packet, write your xml to define the fields and packets in your protocol. Then use poly-packet to generate the source code.


>the mako module is required (pip install mako)
```bash
poly-packet -i sample_protocol.xml -o . -a
```
* -i is for input file, this will be the xml file used
* -o is the output directory, this is where the code and documentation will be generated
* -a tells the tool to create an application layer for you
* -u specifies a path to create a standalone serial utility for the service

>by default all functions will start with the prefix 'pp'. but the 'prefix' attribute can be used in the xml to set a different prefix. this allows the use of multiple services/protocols in a single project without conflict


This example shows how to use the code to create a service. The service is initialized with 1 interface:

### Initializing service

```c
sp_service_init(1); //initialize the service with 1 interface
```
For devices where multiple hardware ports are being used by the same protocol, you can use more interfaces

---

### Register Tx functions

For each interface we can register a send function this allows us to automate things like acknowledgements

```c
sp_service_register_tx(0, &platform_uart_send ); // register sending function
```
once we have registered a callback for an interface, we can send messages to it
```c
sp_sendGetData();
```
---
### Feed the service

The underlying service is responsible for packing and parsing the data. So wherever you read bytes off of the hardware interface, just feed them to the service.

```c
void uart_rx_handler(uint8_t* data, int len)
{
  sp_service_feed(0,datam len);
}
```

From here the service will take care of parsing the data and dispatching messages to the proper message handler.

---
### Sending messages

The service creates one-liner functions for easily sending simple messages


Using the example protocol we can send a message to get data from a remote device on interface 0 with:
```c
sp_sendGetData(0);
```

for packet types with data fields, the datafields get turned into the arguments for the function

```c
sp_sendData(0, 97, 98, "My Sensor name");
```

---
### Creating a message (Be sure to clean after)

If for some reason you need to build your own message, you can do that as well, ***but be sure to clean it when you are done***.

```c
sp_packet_t msg;
sp_packet_init(&msg,SP_SETDATA_PACKET);
```

next we set fields in the message

```c
sp_setSrc(msg,0xABCD );
sp_setDst(msg,0xCDEF);
```

```c
sp_send(0,&msg);
```

When creating your own packets, make sure they are cleaned up after
```c
sp_clean(&msg);
```

---

### Receive Handlers
The generated service creates a handler for each packet type, they are created with weak attributes, so they can be overridden by just declaring them again in our code. If you specify a response for a packet in the xml, the generated handler will have a pointer to responding packet. As long as the handler returns 'PACKET_HANDLED', the service will send the reply. If no reponse is specified the service will send an 'Ack' packet

The following is our handler for 'SetData' type packets

```c
/**
  *@brief Handler for receiving GetData packets
  *@param GetData incoming GetData packet
  *@param Data Data packet to respond with
  *@return handling status
  */
HandlerStatus_e sp_GetData_handler(sp_packet_t* sp_GetData, sp_packet_t* sp_Data)
{
  sp_setSensorA(sp_Data, 97);
  sp_setSensorB(sp_Data, 98);
  sp_setSensorName(sp_Data, "My sensor");

  return PACKET_HANDLED;
}
```

### Process

The service is meant to be run on many platforms, so it does not have built in threading/tasking. For it to continue handling messages, we have to call its process function either in a thread/task or in our super-loop

```c
while(1)
{
  sp_service_process();
}
```
