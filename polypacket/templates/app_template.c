/**
  *@file app_${proto.name.lower()}.c
  *@brief generated protocol source code
  *@author make_protocol.py
  *@date ${proto.genTime}
  */

/***********************************************************
        Application Layer
***********************************************************/

#include "app_${proto.name.lower()}.h"
%if proto.genUtility:
#include "Platforms/Linux/linux_uart.h"
#include "Platforms/Linux/linux_udp.h"

int ifaceMode;
udp_stream udp;
int fd;

#define ${proto.prefix.upper()}_PRINT(packet) fp_print_json((packet),printBuf); printf("%s",printBuf)
%else:
mrt_uart_handle_t ifac0;
%endif
static uint8_t iface0_rx_buf[512];
static char printBuf[512];

static inline HandlerStatus_e iface0_write(uint8_t* data, int len)
{
  /* Place code for writing bytes on interface 0 here */
%if proto.genUtility:
  switch (ifaceMode)
  {
    case UART_MODE:
      uart_write(fd,data,len);
      break;
    case UDP_MODE:
      udp_send(&udp,data,len);
      break;
  }
%else:
  MRT_UART_TX(ifac0, data, len, 10);
%endif

  return PACKET_SENT;
}


static inline void iface0_read()
{
  int len =0;
  /* Place code for reading bytes from interface 0 here */
%if proto.genUtility:
  switch (ifaceMode)
  {
    case UART_MODE:
      len = uart_read(fd,iface0_rx_buf, 32);
      break;
    case UDP_MODE:
      len = udp_recv(&udp,iface0_rx_buf,512);
      break;
  }

%else:
  //TODO read bytes from interface to iface0_rx_buf
  len = MRT_UART_RX(ifac0, iface0_rx_buf, 32, 5);  //read 32 bytes at a time
%endif

  ${proto.prefix}_service_feed(0,iface0_rx_buf, len);
}

/*******************************************************************************
  App Init/end
*******************************************************************************/
%if proto.genUtility:
void app_${proto.name.lower()}_init(const char* connectionStr, int mode)
{
  /* initialize peripheral for iface_0 */
  ifaceMode = mode;

  switch(ifaceMode)
  {
    case UART_MODE:
    if(uart_init(&fd, connectionStr))
      printf("successfully opened port: %s\n",connectionStr);
    else
      printf("Could not open port: %s",connectionStr);
    break;
    case UDP_MODE:
      udp_init(&udp,connectionStr);
      break;
  }

%else:
void app_${proto.name.lower()}_init(mrt_uart_handle_t uart_handle)
{
  /* Set ifac0 to uart handle, this can use any peripheral, but uart is the most common case */
  ifac0 = uart_handle; //set interface to uart handle
%endif

  //initialize service
  ${proto.prefix}_service_init(1,16);

  ${proto.prefix}_service_register_bytes_tx(0, iface0_write);

}

void app_${proto.name.lower()}_end()
{
%if proto.genUtility:
  switch(ifaceMode)
  {
    case UART_MODE:
      uart_close(fd);
      break;
    case UDP_MODE:
      udp_close(&udp);
      break;
  }
%endif
}

/*******************************************************************************
  App Process
*******************************************************************************/

void app_${proto.name.lower()}_process()
{
  /* read in new data from iface 0*/
  iface0_read();

  /* process the actual service */
  ${proto.prefix}_service_process();

}


/*******************************************************************************
  Packet handlers
*******************************************************************************/
% for packet in proto.packets:
%if not packet.standard:
%if not packet.hasResponse:
/**
  *@brief Handler for receiving ${packet.name} packets
  *@param ${packet.name} incoming ${packet.name} packet
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.prefix}_${packet.camel()}_handler(${proto.prefix}_packet_t* ${proto.prefix}_${packet.name})
%else:
/**
  *@brief Handler for receiving ${packet.name} packets
  *@param ${packet.name} incoming ${packet.name} packet
  *@param ${packet.response.name} ${packet.response.name} packet to respond with
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.prefix}_${packet.camel()}_handler(${proto.prefix}_packet_t* ${proto.prefix}_${packet.name}, ${proto.prefix}_packet_t* ${proto.prefix}_${packet.response.name})
%endif
{
  /*  Get Required Fields in packet */
% for field in packet.fields:
  ${field.getDeclaration()};  //${field.desc}
%endfor

% for field in packet.fields:
  %if field.isArray:
  ${proto.prefix}_get${field.camel()}(${proto.prefix}_${packet.name}, ${field.name});
  %else:
  ${field.name} = ${proto.prefix}_get${field.camel()}(${proto.prefix}_${packet.name});
  %endif
% endfor

% for field in packet.fields:
% if field.isEnum:
  switch(${field.name})
  {
  % for val in field.vals:
    case ${proto.prefix.upper()+"_"+field.name.upper() + "_" + val.name.upper()}:    // ${val.desc}
      break;
  % endfor
    default:
      break;
  }

%endif
% endfor
% for field in packet.fields:
% if field.isMask:
  % for val in field.vals:
  if(${field.name} & ${proto.prefix.upper()+"_"+field.name.upper() + "_" + val.name.upper()})    // ${val.desc}
  {
  }
  %endfor

%endif
% endfor
%if packet.hasResponse:
  /*    Set required Fields in response  */
% for field in packet.response.fields:
  //${proto.prefix}_set${field.camel()}(${proto.prefix}_${packet.response.name}, value );  //${field.desc}
%endfor
%endif



  return PACKET_NOT_HANDLED;
}

%endif
% endfor

/**
  *@brief catch-all handler for any packet not handled by its default handler
  *@param metaPacket ptr to ${proto.prefix}_packet_t containing packet
  *@param ${proto.prefix}_response ptr to response
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.prefix}_default_handler( ${proto.prefix}_packet_t * ${proto.prefix}_packet, ${proto.prefix}_packet_t * ${proto.prefix}_response)
{


  return PACKET_NOT_HANDLED;
}
