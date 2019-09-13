# PolyPacket

Poly Packet is backend and code generation tool for creating messaging protocols/Services. Protocols are described in an YAML document which can be easily shared with all components of a system.

A python script is used to parse the YAML file and generate code as well as documentation. The code generation tool can create the back end service, app layer, and even an entire linux utility app

## Protocol Generation

Protocols are generated using YAML. The messaging structure is made up 4 entity types:

* Field
* Packet
* Val
* Struct

## Fields
 A field is a data object within a packet. These can be expressed either as nested yaml, or an inline dictionary

**Example fields:**

```yaml
fields:
  - sensorA: { type: int16 ,desc: Value of Sensor A}
  - sensorB:
      type: int
      format: hex
      desc: Value of Sensor B

  - sensorsC_Z:
      type: int*24
      desc: Values for remaining 24 sensors
```
> **type**: The data type for the field. \*n indicates it is an array with a max size of n <br/>
> **format**: (optional)  This sets the display format used for the toString and toJsonString methods [ hex , dec , assci ]  <br/>
> **desc**: (optional)  The description of the field. This is used to create the documentation  <br/>

<br/>

**Fields can be nested into 'Field Groups' for convenience**
```yaml
fields:
  - header:
      - src: {type: uint16, desc: Address of node sending message }
      - dst: {type: uint16, desc: Address of node to receive message }
```
> **Note** these will be added to the packet as regular fields. The grouping is just for convenience

## Packets
A Packet describes an entire message and is made up of fields

example Packet:

```yaml
packets:
  - Data:
      desc: contains data from a sensor
      fields:
        - sensorA
        - sensorB
        - sensorName
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

```yaml
fields:
  - cmd:
      type: enum
      format: hex
      desc: command byte for controlling node
      vals:
        - led_ON: { desc: turns on led}
        - led_OFF: { desc: turns off led}
        - reset: { desc: resets device }
```

In this example an enum is used to set up some predefined options for the **cmd** field. enums are created with sequential values starting at 0. a **flags** field is defined in the same way, but instead of sequential numbers, it shifts bits to the left, to create a group of individually set-able flags.

## Struct
Structs are essentially the same thing as packets in that they are a collection of fields. The only real difference is the name, and that the code generation tool will create classes for structs.

```yaml
structs:

  - Node:
      desc: struct for modeling node
      field:
        - sensorA
        - sensorB
        - sensorName
```


The idea being that a Struct will hold data locally, and can be easily updated from a message. Any packet can be copied to another packet using the packet copy funtion. this function can be used with any 2 packets/structs but will only copy the fields that have in common:

```c

sp_struct_t thisNode; //must be initialized with sp_struct_build(&thisNode, SP_STRUCT_NODE);

HandlerStatus_e sp_Data_handler(sp_packet_t* sp_data)
{

  sp_packet_copy(&thisNode, sf_data); //update thisNode from incoming data packet

  return PACKET_HANDLED;
}

HandlerStatus_e sp_GetData_handler(sp_packet_t* sp_getData, sp_packet_t* sp_data)
{

  sp_packet_copy( sp_data, &thisNode);  //update data packet with fields from thisNode

  return PACKET_HANDLED;
}

```
>sp is just the prefix for the sample protocol

## Example:

The following example show the YAML for a simple message protocol.


```yaml
---
name: sample
prefix: sp
desc: This is a sample protocol made up to demonstrate features of the PolyPacket
  code generation tool. The idea is to have a tool that can automatically create parseable/serializable
  messaging for embedded systems

###########################################################################################################
#                                   FIELDS                                                                #
###########################################################################################################

fields:

  - sensorA: { type: int16 ,desc: Value of Sensor A}

  - sensorB:
      type: int
      desc: Value of Sensor B

  - sensorName:
      type: string
      desc: Name of sensor

  - cmd:
      type: enum
      format: hex
      desc: command byte for controlling node
      vals:
        - led_ON: { desc: turns on led}
        - led_OFF: { desc: turns off led}
        - reset: { desc: resets device }

###########################################################################################################
#                                   Packets                                                               #
###########################################################################################################
packets:
  - SendCmd:
      desc: Message to send command to node
      fields:
        - cmd

  - GetData:
      desc: Message tp get data from node
      response: Data

  - Data:
      desc: contains data from a sensor
      fields:
        - sensorA
        - sensorB
        - sensorName
###########################################################################################################
#                                   Structs                                                                #
###########################################################################################################

structs:

  - Node:
      desc: struct for modeling node
      field:
        - sensorA
        - sensorB
        - sensorName


```
The YAML sets up 3 Fields:

**cmd** - Command for device </br>
**sensorA** - Value of Sensor A <br/>
**sensorB** - Value of Sensor B <br/>
**sensorName** - Name of sensor <br/>

It then lists the packets, and which fields are in each packet. fields are considered optional in a packet unless specified with **req="true"**. So in this example you could send a Data packet that only contained sensorB and sensorName.

## Using Poly Packet

To use poly packet, write your YAML to define the fields and packets in your protocol. Then use poly-packet to generate the source code.


>the mako module is required (pip install mako)
```bash
poly-packet -i sample_protocol.yml -o . -a
```
* -i is for input file, this will be the YAML file used
* -o is the output directory, this is where the code and documentation will be generated
* -a tells the tool to create an application layer for you
* -u specifies a path to create a standalone serial utility for the service

>by default all functions will start with the prefix 'pp'. but the 'prefix' attribute can be used in the YAML to set a different prefix. this allows the use of multiple services/protocols in a single project without conflict


This example shows how to use the code to create a service. The service is initialized with 1 interface:

### Initializing service

```c
sp_service_init(1); //initialize the service with 1 interface
```
For devices where multiple hardware ports are being used by the same protocol, you can use more interfaces

---

### Register Tx functions

For each interface we need to register a send function. This allows us the service to handle the actual sending so we can automate things like acknowledgements and retries. There are two types of send callbacks that can be registered:

```c
typedef HandlerStatus_e (*poly_tx_byte_callback)(uint8_t* data , int len);
typedef HandlerStatus_e (*poly_tx_packet_callback)(poly_packet_t* packet );
```

The tx_byte callback will pass the packet as an array of COBS encoded bytes which can be sent directly over a serial connection. The tx_packet will pass a reference to the packet itself which can be converted to JSON, or manipulated before sending.

```c
sp_service_register_tx_bytes(0, &uart_send ); // register sending function for raw bytes
sp_service_register_tx_packet(0, &json_send ); // register sending function for entire packet
```
once we have registered a callback for an interface, we can send messages to it using the quick send functions generated for the service.
```c
sp_sendGetData();
```
---
### Feed the service

The underlying service is responsible for packing and parsing the data. So wherever you read bytes off of the hardware interface, just feed them to the service.

#### Encoded Bytes
```c
void uart_rx_handler(uint8_t* data, int len)
{
  sp_service_feed(0,datam len);
}
```

If you are working with JSON you have two options. you can feed the json message to the service for normal handling or call the json handler to bypass the normal service queue. This option make it easy to use the service in synchronous tasks such as responding to an http request

#### Async JSON
```c
void app_json_async_handler(char* strJson, int len)
{
  sp_service_feed_json(0,strJson, len);
}
```

#### Sync JSON
```c

void app_json_sync_handler(const char* strRequest, int len, char* strResp)
{
  HandlerStatus_e status;
  status = sp_handle_json(strRequest, len, strResp);
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
The generated service creates a handler for each packet type, they are created with weak attributes, so they can be overridden by just declaring them again in our code. If you specify a response for a packet in the YAML, the generated handler will have a pointer to responding packet. As long as the handler returns 'PACKET_HANDLED', the service will send the reply. If no reponse is specified the service will send an 'Ack' packet

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
