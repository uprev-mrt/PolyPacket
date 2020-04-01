![polypacket_logo](https://raw.githubusercontent.com/wiki/up-rev/PolyPacket/polypacket_logo.png)

Poly Packet is a set of tools aimed at generating protocols from embedded projects. Protocols are described in an YAML document which can be easily shared with all components of a system.

A python script is used to parse the YAML file and generate C/C++ code as well as documentation. The code generation tool can create the back end service, application layer, and even an entire linux utility app

## Installation

The tools can be installed using pip:

```bash
pip3 install polypacket
```
<br>

To view an example protocol file:
```bash
poly-make -e
```
<br>

## Live Protocol Interpreter


Once you have a descriptor file, you can run a live interface of the protocol using poly-packet

Open two terminals and connect them over udp to test it out:
<br>
<br>
terminal 1:
```bash
poly-packet -i sample_protocol.yml -c connect udp:8020
```

<br>

terminal 2:
```bash
poly-packet -i sample_protocol.yml -c connect udp:8010:8020
```
<br>
The terminal interface uses autocompletion, so hit tab to show available packet/ field types. to send a packet just type the packet name followed by comma seperated field names and values.

example:
```bash
Data sensorA: 45, sensorB: 78, sensorName: mySensor
```

[Visit Wiki for more information](https://github.com/up-rev/PolyPacket/wiki)
