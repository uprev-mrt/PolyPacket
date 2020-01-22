<!DOCTYPE html>
<html>
<head>
  <title>${proto.name} ICD</title>
</head>
<body>
<div class="content">
<h1>${proto.name} ICD</h1>
<ul>
  <li> Generated with <a href="https://github.com/up-rev/PolyPacket/wiki">PolyPacket</a> on ${proto.genTime}</li>
  <li> CRC: ${proto.hash}</li>
  <li> Transport Encoding: (COBS) <a href="https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing">Consistent Overhead ByteStuffing</a></li>
</ul>
<hr/>
<h2>Description: </h2>
<p>${proto.desc}</p>

<br/>
<hr class="section">
<h2 class="right"> Index </h2>
<hr>


%if len(proto.packets) > 0:
<a href="#packet_${proto.packets[0].name.lower()}"> Packets:</a>


<ul>
  %for packet in proto.packets:
  <li><a href="#packet_${packet.name.lower()}">${"[%0.2X]" % packet.packetId}  ${packet.name} </a></li>
  %endfor
</ul>
%endif

%if len(proto.structs) > 0:
<a href="#packet_${proto.structs[0].name.lower()}"> Structs:</a>

<ul>
  %for struct in proto.structs:
  <li><a href="#packet_${struct.name.lower()}">${"[%0.2X]" % struct.packetId}  ${struct.name} </a></li>
  %endfor
</ul>
%endif




<hr class="section">

<h2 class="right"> Packets</h2>
<hr class="thick">
<div class="packet" id="packet_ping">
<h3>Ping </h3>
<hr/>
<ul>
  <li class="note">Packet ID: <b>[00]</b></li>
  <li class="note"> Requests: <a href="#packet_ack">Ack</a></li>
</ul>

<p class="desc">Ping to request an <a href="#packet_ack">Ack</a>. Used for testing and ICD verification</p>
<br/>
<br/>
<b>Fields:</b>
<table class="fields">
  <tr>
    <th> Field</th>
    <th> Type</th>
    <th> Description</th>
  </tr>
  <tr>
    <td width="">icd</td>
    <td width="">  uint32_t    </td>
    <td>32bit Hash of protocol description. This is used to verify endpoints are using the same protocol</td>
  </tr>
</table>
<br/>
<hr class="thick">
</div>

<div class="packet" id="packet_ack">
<h3>Ack </h3>
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
<h3>${packet.name} </h3>
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
<br/>
<b>Fields:</b>
<table class="fields">
  <tr>
    <th> Field</th>
    <th> Type</th>
    <th> Description</th>
  </tr>
  %for field in packet.fields:
  <tr>
    %if field.isRequired:
    <td width=""><b>${field.name}</b></td>
    %else:
    <td width="">${field.name}</td>
    %endif
    <td width="">  ${field.cType}\
      %if field.isArray:
        [${field.arrayLen}]\
      %endif
    </td>
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

%if len(proto.structs) > 0:

<hr class="section">
<h2 class="right"> Structs</h2>
<hr class="thick">

%for packet in proto.structs:
%if not packet.standard:
<div id="packet_${packet.name.lower()}" class="packet">
<h3>${packet.name} </h3>
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
<br/>
<b>Fields:</b>
<table class="fields">
  <tr>
    <th> Field</th>
    <th> Type</th>
    <th> Description</th>
  </tr>
  %for field in packet.fields:
  <tr>
    %if field.isRequired:
    <td width=""><b>${field.name}</b></td>
    %else:
    <td width="">${field.name}</td>
    %endif
    <td width="">  ${field.cType}\
      %if field.isArray:
        [${field.arrayLen}]\
      %endif
    </td>
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

%endif
</div>
</body>
<style>
table.fixed { table-layout:auto; }
table.fixed td { overflow:visible; }

table.fields{
  table-layout:auto;
}

body {
  padding:0;
}

.content{
  padding-top: 0;
  padding-left: 1%;
  padding-right: 1%;
  background-color: #fff;
}

@media print {
  .packet {
    page-break-inside: avoid;
    padding-top: 4px;
  }
  .content{
    width: 100%;
  }
  body{
    background-color: #fff;
  }
}

@media screen {
  .content{
    width: 50%;
    margin-left: auto;
    margin-right: auto;
    margin-top: 0;
    padding-top: 4px;
    box-shadow: 5px 10px #AAA;
  }

  body{
    background-color: #ccc;
    padding: 0;
  }
}

html *{
  font-size: 1em ;
   color: #000 ;
  font-family: Arial ;
}

hr.section {
  border-style: solid;
  border-width: 2px;
  opacity: 1;
}


hr.thick {
  border-style: solid;
  border-width: 1px;
  border-color: #94b2d3;
  opacity: 1;
}

hr {
  opacity: 0.5;
}

table {
  border-collapse: collapse;
}

td {
  border: 1px solid #000000;
  text-align: left;
  padding: 8px;
  vertical-align: top;
}

.desc{
  font-size: 1.2em;
}

th {
  border: 1px solid #000000;
  text-align: left;
  padding: 8px;
  background-color: #94b2d3;
}

li.val{
  opacity: 0.6;
}

h1{
  font-size: 2.5em;
}

h2 
{
  font-size: 1.8em;
}

h2.right{
  text-align: center;
  font-size: 1.8em;
}

h3
{
  font-size: 1.8em;
  color: #003366;
}

h4 
{
  font-size: 1.1em;
  color: #003366;
}


.note{
  font-style: italic;
  opacity: 0.6;
}

a{
  text-decoration:none;
}

a:link {
  color: blue;
}

/* visited link */
a:visited {
  color: blue;
}

table.fixed tr td:last-child{
    width:1%;
    white-space:nowrap;
}
</style>
</html>
