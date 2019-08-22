# ${proto.name} ICD
* Generated: ${proto.genTime}<br/>
* CRC: ${proto.hash}
* Transport Encoding: (COBS) [Consistent Overhead ByteStuffing](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing)

** ${proto.desc} **

---
<div id="header" class="packet">
<h2>Header </h2>
<hr/>

<p class="desc">All packets contain a standard header</p>
<br/>
<b>Structure:</b>
<table class="fixed" style="width:40%">
  <tr>
  <th  >Byte</th>
        <th >0</th>
        <th >1</th>
        <th >2</th>
        <th >3</th>
        <th >4</th>
        <th >5</th>
        <th >6</th>
  </tr>
  <tr>
    <td>Field</td>
      <td colspan="1">Id</td>
      <td colspan="2">Length</td>
      <td colspan="2">Token</td>
      <td colspan="2">Checksum</td>
  </tr>
  <tr>
    <td>Type</td>
    <td colspan="1">uint8_t</td>
    <td colspan="2">uint16_t</td>
    <td colspan="2">uint16_t</td>
    <td colspan="2">uint16_t</td>
  </tr>
</table>
<br/>
<b>Fields:</b>
<table class="fields">
  <tr>
    <th> Field</th>
    <th> Description</th>
  </tr>
  <tr>
    <td width="">Id</td>
    <td>Packet Type identifier</td>
  </tr>
  <tr>
    <td width="">Length</td>
    <td>Number of bytes in packet (not including header)</td>
  </tr>
  <tr>
    <td width="">Token</td>
    <td>Psuedo random token generated for message</td>
  </tr>
  <tr>
    <td width="">Checksum</td>
    <td>16bit checksum used for data validation</td>
  </tr>
</table>

<br/>
<hr class="thick">

</div>

<h2> Packet Types </h2>
<hr/>

<ul>
  %for packet in proto.packets:
  <li><a href="#packet_${packet.name.lower()}">${"[%0.2X]" % packet.packetId}  ${packet.name} </a></li>
  %endfor
</ul>

<hr class="thick">

<div class="packet" id="packet_ping">
<h2>Ping </h2>
<hr/>
<ul>
  <li class="note">Packet ID: <b>[00]</b></li>
  <li class="note"> Requests: <a href="#packet_ack">Ack</a></li>
</ul>

<span class="note"> This Packet type does not contain any data fields </span><br/>
<br/>
<hr class="thick">
</div>

<div class="packet" id="packet_ack">
<h2>Ack </h2>
<hr>
<ul>
  <li class="note">  Packet ID: <b>[01]</b></li>
  <li class="note">Responds To: <a href="#packet_ping">Ping</a></li>
</ul>

<span class="note"> This Packet type does not contain any data fields </span><br/>
<br/>
<hr class="thick">
</div>


%for packet in proto.packets:
%if not packet.standard:
<div id="packet_${packet.name.lower()}" class="packet">
<h2>${packet.name} </h2>
<hr/>
<ul>
  <li class="note">  Packet ID: <b>[${"%0.2X" % packet.packetId}]</b></li>
  %if packet.hasResponse:
  <li class="note">   Requests: <a href="#packet_${packet.response.name.lower()}">${packet.response.name}</a></li>
  %endif
  %if len(packet.respondsTo) > 0:
  <li class="note">Responds To: \
  %for idx,request in enumerate(packet.respondsTo):
  %if idx == 0:
  <a href="#packet_${request.lower()}">${request}</a>\
  %else:
  , <a href="#packet_${request.lower()}">${request}</a>\
  %endif
  %endfor
  </li>
  %endif
</ul>

<p class="desc">${packet.desc}</p>
<br/>
%if len(packet.fields) > 0:
<b>Structure:</b>
<table class="fixed" >
  <tr>
  <th  >Byte</th>
  <% count = 0 %>\
%for field in packet.fields:
    %if field.size > 4:
    <th >${count}</th>
    <th colspan="2">........</th>
    <th >${(count+field.size) }</th>
  %else:
    %for x in range(field.size):
    <th >${count}</th>
    <% count += 1 %>\
    %endfor
  %endif
%endfor
  </tr>
  <tr>
    <td>Field</td>
  %for field in packet.fields:
      %if field.size > 4:
      <td colspan="4">${field.name}</td>
    %else:
      <td colspan="${field.size}">${field.name}</td>
    %endif
  %endfor
  </tr>
  <tr>
    <td>Type</td>
  %for field in packet.fields:
      %if field.size > 4:
      <td colspan="4">\
    %else:
      <td colspan="${field.size}">\
    %endif
    ${field.cType}\
    %if field.isArray:
    [${field.arrayLen}]\
    %endif
  </td>
  %endfor
  </tr>
</table>
<br/>
<b>Fields:</b>
<table class="fields">
  <tr>
    <th> Field</th>
    <th> Description</th>
  </tr>
  %for field in packet.fields:
  <tr>
    <td width="">${field.name}</td>
    <td>${field.desc}\
      %if field.isEnum:
      <br/>
      <ul>
      %for idx,val in enumerate(field.vals):
      <li class="val">${field.valsFormat % idx} : <b>${val.name}</b> - ${val.desc}</li>
      %endfor
      </ul>
      %endif
      %if field.isMask:
      <br/>
      <ul>
      %for idx,val in enumerate(field.vals):
      <li class="val">${field.valsFormat % (1 << idx)} : <b>${val.name}</b> - ${val.desc}</li>
      %endfor
      </ul>
      %endif
    </td>
  </tr>
  %endfor
</table>

%else:
## zero data fields
<span class="note"> This Packet type does not contain any data fields </span><br/>
%endif
<br/>
<hr class="thick">
</div>
%endif
%endfor
</div>
