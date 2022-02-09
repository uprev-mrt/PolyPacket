

${proto.name} ICD
%for c in proto.name:
=\
%endfor
====


* Generated with `PolyPacket <https://mrt.readthedocs.io/en/latest/pages/polypacket/polypacket.html>`_ 
* CRC: CRC: ${proto.hash}
%if not args.basic:
* Transport Encoding: (COBS) `Consistent Overhead ByteStuffing <https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing>`_ 
%endif

Description
-----------

${proto.desc}

.. <!--*user-block-description-start*-->

.. <!--*user-block-description-end*-->

%if not args.basic:

Packet Header 
-------------

Every packet has the standard `PolyPacket` header.

+------------+------------+-----------+------------+-----------+-----------+------------+------------+-----------+
| **Byte**   | **0**      | **1**     | **2**      | **3**     | **4**     | **5**      | **6**      | **7**     |
+============+============+===========+============+===========+===========+============+============+===========+
| **Field**  | typeID     | sequence  | Data Len               | Token                  | Checksum               |
+------------+------------+-----------+------------+-----------+-----------+------------+------------+-----------+
| **Type**   | uint8      | uint8     | uint16                 | uint16                 | uint16                 |
+------------+------------+-----------+------------+-----------+-----------+------------+------------+-----------+


Fields: 

+--------------+------------+--------------------------------------------------------------------------------+
| **Field**    | **Type**   | **Description**                                                                |
+==============+============+================================================================================+
| **typeId**   | uint8      | ID for packet type                                                             |
+--------------+------------+--------------------------------------------------------------------------------+
|**sequence**  | uint8      | Sequence number, can be used to ensure packets are not being dropped           |
+--------------+------------+--------------------------------------------------------------------------------+
| **Data Len** | uint16     |Total length of packet payload                                                  |
+--------------+------------+--------------------------------------------------------------------------------+
| **Token**    | uint16     | Token used for tracking acknowledgments                                        |
|              |            |                                                                                |
|              |            | * bit 15: Ack Flag                                                             |
|              |            | * bit 14:0: Random 15 bit token                                                |
+--------------+------------+--------------------------------------------------------------------------------+
| **Checksum** | uint16     | ID for packet type                                                             |
+--------------+------------+--------------------------------------------------------------------------------+

For more detailed information on how field data is serialized and encoded see the documentation for the `PolyPacket backend library <https://bitbucket.org/uprev/utility-polypacket/src/master/>`_ 


%endif


Index 
-------


%if len(proto.packets) > 0:

* `Packets`_: 

  %for packet in proto.packets:
  * `${packet.name}`_
  %endfor
%endif

%if len(proto.structs) > 0:

* `Structs`_:

  %for struct in proto.structs:
  * `${struct.name}`_
  %endfor
%endif

----

Packets 
-------


Ping 
~~~~

* Packet ID: **[00]**
* Requests:  `Ack`_ 

Ping to request an `Ack`_. Used for testing and ICD verification.

**Fields:**

+------------------------------+-----------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+
|**Field**                     | **Type**                          |**Description**                                                                                                                                    |
+==============================+===================================+===================================================================================================================================================+
|icd                           | uint32                            |32bit Hash of protocol description. This is used to verify endpoints are using the same protocol                                                   |
+------------------------------+-----------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+

----

Ack 
~~~

* Packet ID: **[01]**
* Responds To:  `Ping`_

**Fields:**

+------------------------------+-----------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+
|**Field**                     | **Type**                          |**Description**                                                                                                                                    |
+==============================+===================================+===================================================================================================================================================+
|icd                           | uint32                            |32bit Hash of protocol description. only present when responding to ping                                                                           |
+------------------------------+-----------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+



%for packet in proto.packets:
%if not packet.standard:

----

${packet.name}
%for c in packet.name:
~\
%endfor


* Packet ID: **[${"%0.2X" % packet.packetId}]**
  %if packet.hasResponse:
* Requests: `${packet.response.name}`_
  %endif
  %if len(packet.respondsTo) > 0:
* Responds To: \
  %for idx,request in enumerate(packet.respondsTo):
  %if idx == 0:
  `${request}`_
  %else:
  , `${request}`_
  %endif
  %endfor
  %endif


${packet.desc}

.. <!--*user-block-${packet.name}-start*-->

.. <!--*user-block-${packet.name}-end*-->


%if len(packet.fields) > 0:

**Fields:**

+-----------------------------------+-----------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
|**Field**                          | **Type**                          |**Description**                                                                                                                                       |
+===================================+===================================+======================================================================================================================================================+
  %for field in packet.fields:
|${t.padAfter(field.name,35)}|\
%if field.isArray:
${t.padAfter(  "{0}[{1}]".format(field.cType, field.arrayLen),35)}|\
%else :
${t.padAfter(field.cType,35)}|\
%endif
${t.padAfter(field.desc,150)}|
%if field.isEnum:
  %for idx,val in enumerate(field.vals):
|${(" "*35) + "|" + (" "*35) + "|" + t.padAfter( " * {0} : **{1}** - {2}".format(field.valsFormat % idx, val.name, val.desc) ,150) }|
  %endfor
%endif
%if field.isMask:
  %for idx,val in enumerate(field.vals):
|${(" "*35) + "|" + (" "*35) + "|" + t.padAfter( " * {0} : **{1}** - {2}".format(field.valsFormat % (1 <<idx), val.name, val.desc) ,150) }|
  %endfor
%endif
+-----------------------------------+-----------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
%endfor


%else:
## zero data fields
This Packet type does not contain any data fields
%endif
%endif
%endfor

%if len(proto.structs) > 0:

Structs
-------

%for packet in proto.structs:

${packet.name}
%for c in packet.name:
~\
%endfor


* Packet ID: **[${"%0.2X" % packet.packetId}]**
  %if packet.hasResponse:
* Requests: `${packet.response.name}`_
  %endif
  %if len(packet.respondsTo) > 0:
* Responds To: \
  %for idx,request in enumerate(packet.respondsTo):
  %if idx == 0:
  `${request}`_
  %else:
  , `${request}`_
  %endif
  %endfor
  %endif


${packet.desc}

.. <!--*user-block-${packet.name}-start*-->

.. <!--*user-block-${packet.name}-end*-->


%if len(packet.fields) > 0:

**Fields:**

+-----------------------------------+-----------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
|**Field**                          | **Type**                          |**Description**                                                                                                                                       |
+===================================+===================================+======================================================================================================================================================+
  %for field in packet.fields:
|${t.padAfter(field.name,35)}|\
%if field.isArray:
${t.padAfter(  "{0}[{1}]".format(field.cType, field.arrayLen),35)}|\
%else :
${t.padAfter(field.cType,35)}|\
%endif
${t.padAfter(field.desc,150)}|
%if field.isEnum:
  %for idx,val in enumerate(field.vals):
|${(" "*35) + "|" + (" "*35) + "|" + t.padAfter( " * {0} : **{1}** - {2}".format(field.valsFormat % idx, val.name, val.desc) ,150) }|
  %endfor
%endif
%if field.isMask:
  %for idx,val in enumerate(field.vals):
|${(" "*35) + "|" + (" "*35) + "|" + t.padAfter( " * {0} : **{1}** - {2}".format(field.valsFormat % (1 <<idx), val.name, val.desc) ,150) }|
  %endfor
%endif
+-----------------------------------+-----------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
%endfor


%else:
## zero data fields
This Packet type does not contain any data fields
%endif


%endfor
%endif

.. <!--*user-block-bottom-start*-->

.. <!--*user-block-bottom-end*-->

