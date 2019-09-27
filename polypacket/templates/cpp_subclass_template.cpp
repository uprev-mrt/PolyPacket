/**
  *@file ${role.className}.cpp
  *@brief generated code for ${proto.name} packet service
  *@author make_protocol.py
  *@date ${proto.genTime}
  */

#include "${role.className}.h"


${role.className}::${role.className}()
:${proto.cppFileName}(1)  //Initialize with 1 interface
{

}

/**
  *@brief Handler for receiving ping packets
  *@param ${proto.prefix}_ping ptr to incoming ping packet
  *@param ${proto.prefix}_ack ptr to repsonding ack
  *@return PACKET_HANDLED
  */
HandlerStatus_e ${proto.cppFileName}::PingHandler(${proto.camelPrefix()}Packet& ${proto.prefix}_ping, ${proto.camelPrefix()}Packet& ${proto.prefix}_ack)
{
  /* Ack token has already been set as ping token with POLY_ACK_FLAG*/
  uint32_t icd_hash = ${proto.prefix}_ping.getIcd();
  /* assert(icd_hash == ${proto.prefix.upper()}_SERVICE_HASH ); */

  return PACKET_HANDLED;
}

/**
  *@brief Handler for receiving ack packets
  *@param ${proto.prefix}_ack ptr to ack
  *@return PACKET_HANDLED
  */
HandlerStatus_e ${proto.cppFileName}::AckHandler(${proto.camelPrefix()}Packet& ${proto.prefix}_ack)
{
  return PACKET_HANDLED;
}

% for packet in proto.packets:
%if not packet.standard:
%if not packet.hasResponse:
/**
  *@brief Handler for receiving ${packet.name} packets
  *@param ${packet.name} incoming ${packet.name} packet
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.cppFileName}::${packet.name}Handler(${proto.camelPrefix()}Packet& ${proto.prefix}_${packet.name})
%else:
/**
  *@brief Handler for receiving ${packet.name} packets
  *@param ${packet.name} incoming ${packet.name} packet
  *@param ${packet.response.name} ${packet.response.name} packet to respond with
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.cppFileName}::${packet.name}Handler(${proto.camelPrefix()}Packet& ${proto.prefix}_${packet.name}, ${proto.camelPrefix()}Packet& ${proto.prefix}_${packet.response.name})
%endif
{
  /*  Get Required Fields in packet */
% for field in packet.fields:
%if field.isRequired:
  //${field.getDeclaration()};  //${field.desc}
%endif
%endfor

% for field in packet.fields:
%if field.isRequired:
  %if field.isArray:
  //${proto.prefix}_get${field.camel()}(${proto.prefix}_${packet.name}, ${field.name});
  %else:
  //${field.name} = ${proto.prefix}_get${field.camel()}(${proto.prefix}_${packet.name});
  %endif
%endif
% endfor
%if packet.hasResponse:
  /*    Set required Fields in response  */
% for field in packet.response.fields:
  //${proto.prefix}_set${field.camel()}(${proto.prefix}_${packet.response.name}, value );  //${field.desc}
%endfor
%endif


  /* NOTE : This function should not be modified! If needed,  It should be overridden in the application code */

  return PACKET_NOT_HANDLED;
}

%endif
% endfor


/**
  *@brief catch-all handler for any packet not yet handled
  *@param ${proto.prefix}_packet ptr to incoming message
  *@param ${proto.prefix}_response ptr to response
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.cppFileName}::defaultHandler( ${proto.camelPrefix()}Packet& ${proto.prefix}Packet, ${proto.camelPrefix()}Packet& ${proto.prefix}Response)
{

  /* NOTE : This function should not be modified, when the callback is needed,
          ${proto.prefix}_default_handler  should be implemented in the user file
  */

  return PACKET_NOT_HANDLED;
}
