/**
  *@file ${proto.fileName}.h
  *@brief generated code for ${proto.name} packet service
  *@author make_protocol.py
  *@date ${proto.genTime}
  *@hash ${proto.hash}
  */

#pragma once
/***********************************************************
        THIS FILE IS AUTOGENERATED. DO NOT MODIFY
***********************************************************/
#include "Utilities/PolyPacket/poly_service.h"

#define ${proto.prefix.upper()}_SERVICE_HASH 0x${proto.hash}

/*******************************************************************************
  Enums
*******************************************************************************/
% for field in proto.fields:
% if field.isEnum:
/* Enums for ${field.name} field */
typedef enum{
  % for val in field.vals:
  ${proto.prefix.upper()+"_"+field.name.upper() + "_" + val.name.upper()},              /* ${val.desc} */
  % endfor
  ${proto.prefix.upper()+"_"+field.name.upper()}_MAX_LIMIT
} ${proto.prefix}_${field.name.lower()}_e;
%if proto.snippets:
//Switch Snippet
/*
switch(${field.name.lower()})
{
% for val in field.vals:
  case ${proto.prefix.upper()+"_"+field.name.upper() + "_" + val.name.upper()}:    // ${val.desc}
    break;
% endfor
  default:
    break;
}
*/
% endif

% endif
% endfor

/*******************************************************************************
  Bits/Flags
*******************************************************************************/
% for field in proto.fields:
% if field.isMask:
/* Flags for ${field.name} field */
typedef enum{
  % for idx,val in enumerate(field.vals):
  ${proto.prefix.upper()+"_"+field.name.upper() + "_" + val.name.upper()} = ${ field.valsFormat % (1 << idx)},    /* ${val.desc} */
  % endfor
  ${proto.prefix.upper()+"_"+field.name.upper()}_MAX_LIMIT
} ${proto.prefix}_${field.name.lower()}_e;

% endif
% endfor

/*******************************************************************************
  Global Descriptors
*******************************************************************************/
//Declare extern packet descriptors
% for packet in proto.packets:
extern poly_packet_desc_t* ${packet.globalName};
% endfor

% for struct in proto.structs:
extern poly_packet_desc_t* ${struct.globalName};
% endfor


//Declare extern field descriptors
% for field in proto.fields:
extern poly_field_desc_t* ${field.globalName};
% endfor

/*
 *@brief The main type dealt with by the user
 */

typedef meta_packet_t ${proto.prefix}_packet_t;
typedef ${proto.prefix}_packet_t ${proto.prefix}_struct_t;


/*******************************************************************************
  Service Functions
*******************************************************************************/
/**
  *@brief initializes protocol service
  *@param ifaces number of interfaces to use
  */
void ${proto.prefix}_service_init(int interfaceCount);

/**
  *@brief tears down service
  *@note probably not needed based on lifecycle of service
  *@ but useful for detecting memory leaks
  */
void ${proto.prefix}_service_teardown();


/**
  *@brief handles packets and dispatches to handler
  *@param req incoming message
  *@param resp response to message
  *@param number of bytes
  */
HandlerStatus_e ${proto.prefix}_service_dispatch(${proto.prefix}_packet_t* req, ${proto.prefix}_packet_t* resp);

/**
  *@brief processes data in buffers
  */
void ${proto.prefix}_service_process();

/**
  *@brief registers a callback to let the service know how to send bytes for a given interface
  *@param iface index of interface to register with
  *@param txBytesCallBack a function pointer for the callback
  */
void ${proto.prefix}_service_register_bytes_tx( int iface, poly_tx_bytes_callback txBytesCallBack);

/**
  *@brief registers a callback to let the service know how to send entire packets
  *@param iface index of interface to register with
  *@param txPacketCallBack a function pointer for the callback
  */
void ${proto.prefix}_service_register_packet_tx( int iface, poly_tx_packet_callback txPacketCallBack);

/**
  *@brief 'Feeds' bytes to service at given interface for processing
  *@param iface index of interface to send on
  *@param data data to be processed
  *@param number of bytes
  */
void ${proto.prefix}_service_feed(int iface, uint8_t* data, int len);

/**
  *@brief handles json message, and shortcuts the servicing proccess. used for http requests
  *@param req incoming json message string
  *@param resp response data
  *@param number of bytes
  */
HandlerStatus_e ${proto.prefix}_handle_json(const char* req,int len, char* resp);

/**
  *@brief 'Feeds' json message to service
  *@param iface index of interface to send on
  *@param msg data to be processed
  *@param number of bytes
  */
void ${proto.prefix}_service_feed_json(int iface, const char* msg, int len);

/**
  *@brief sends packet over given interface
  *@param packet packet to be sent
  *@param iface index of interface to send on
  */
HandlerStatus_e ${proto.prefix}_send( int iface, ${proto.prefix}_packet_t* packet);

/**
  *@brief enables/disables the auto acknowledgement function of the service
  *@param enable true enable auto acks, false disables them
  */
void ${proto.prefix}_auto_ack(bool enable);

/**
  *@brief enables/disables the txReady of an interface
  *@param enable true enable auto acks, false disables them
  */
void ${proto.prefix}_enable_tx(int iface);
void ${proto.prefix}_disable_tx(int iface);


/*******************************************************************************
  Meta-Packet Functions
*******************************************************************************/

/**
  *@brief initializes a new {proto.prefix}_packet_t
  *@param desc ptr to packet descriptor to model packet from
  */
void ${proto.prefix}_packet_build(${proto.prefix}_packet_t* packet, poly_packet_desc_t* desc);
#define ${proto.prefix}_struct_build(packet,desc) ${proto.prefix}_packet_build(packet,desc)



/**
  *@brief recrusively cleans packet and its contents if it still has ownership
  *@param packet packet to clean
  */
void ${proto.prefix}_clean(${proto.prefix}_packet_t* packet);

/**
  *@brief converts packet to json
  *@param packet ptr to packet to convert
  *@param buf buffer to store string
  *@return length of string
  */
#define ${proto.prefix}_print_json(packet,buf) poly_packet_print_json(&(packet)->mPacket, buf, false)

/**
  *@brief parses packet from a buffer of data
  *@param packet ptr to packet to be built
  *@param buf buffer to parse
  *@return status of parse attempt
  */
#define ${proto.prefix}_parse(packet,buf,len) poly_packet_parse_buffer(&(packet)->mPacket, buf, len)

/**
  *@brief Copies all fields present in both packets from src to dst
  *@param dst ptr to packet to copy to
  *@param src ptr to packet to copy from
  */
#define ${proto.prefix}_packet_copy(dst,src) poly_packet_copy(&(dst)->mPacket,&(src)->mPacket )

/**
  *@brief packs packet into a byte array
  *@param packet ptr to packet to be packed
  *@param buf buffer to store data
  *@return length of packed data
  */
#define ${proto.prefix}_pack(packet, buf) poly_packet_pack(&(packet)->mPacket, buf)

/*******************************************************************************
  Meta-Packet setters
*******************************************************************************/
% for field in proto.fields:
  %if field.isArray:
void ${proto.prefix}_set${field.camel()}(${proto.prefix}_packet_t* packet, const ${field.getParamType()} val);
  % else:
void ${proto.prefix}_set${field.camel()}(${proto.prefix}_packet_t* packet, ${field.getParamType()} val);
  % endif
% endfor

/*******************************************************************************
  Meta-Packet getters
*******************************************************************************/

/**
  *@brief checks to see if field is present in packet
  *@param packet ptr to packet to be packed
  *@param field ptr to field desc
  *@return true if field is present
  */
#define ${proto.prefix}_hasField(packet, field) poly_packet_has(&(packet)->mPacket, field)

% for field in proto.fields:
  %if field.isArray:
void ${proto.prefix}_get${field.camel()}(${proto.prefix}_packet_t* packet, ${field.getParamType()} val);
  % else:
${field.getParamType()} ${proto.prefix}_get${field.camel()}(${proto.prefix}_packet_t* packet);
  % endif
% endfor

/*******************************************************************************
  Quick send functions

  These are convenience one-liner functions for sending messages.
  They also handle their own clean up and are less bug prone than building your own packets
*******************************************************************************/

/**
  *@brief Sends a ping
  *@param iface interface to ping
  *@note a ping is just an ACK without the ack flag set in the token
  */
HandlerStatus_e ${proto.prefix}_sendPing(int iface);

% for packet in proto.packets:
%if not packet.standard:
HandlerStatus_e ${proto.prefix}_send${packet.camel()}(int iface\
  %for idx,field in enumerate(packet.fields):
,\
  %if field.isArray:
 const ${field.getParamType()} ${field.name}\
  %else:
 ${field.getParamType()} ${field.name}\
  %endif
  %endfor
);
%endif
% endfor

/*******************************************************************************
  Packet Handlers
*******************************************************************************/
% for packet in proto.packets:
%if packet.hasResponse:
/*@brief Handler for ${packet.name} packets */
HandlerStatus_e ${proto.prefix}_${packet.camel()}_handler(${proto.prefix}_packet_t* ${proto.prefix}_${packet.name}, ${proto.prefix}_packet_t* ${proto.prefix}_${packet.response.name});
%else:
/*@brief Handler for ${packet.name} packets */
HandlerStatus_e ${proto.prefix}_${packet.camel()}_handler(${proto.prefix}_packet_t* ${proto.prefix}_${packet.name});
%endif

% endfor
/*@brief Catch-All Handler for unhandled packets */
HandlerStatus_e ${proto.prefix}_default_handler(${proto.prefix}_packet_t * ${proto.prefix}_packet, ${proto.prefix}_packet_t * ${proto.prefix}_response);
