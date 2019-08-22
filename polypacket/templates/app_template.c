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
%endif

static uint8_t iface0_rx_buf[512];
%if proto.genUtility:
int fd;
static char printBuf[512];

#define ${proto.prefix.upper()}_PRINT(packet) fp_print_json((packet),printBuf); printf("%s",printBuf)
%else:
mrt_uart_handle_t ifac0;
%endif

static inline HandlerStatus_e iface0_write(uint8_t* data, int len)
{
  /* Place code for writing bytes on interface 0 here */
%if proto.genUtility:
  uart_write(fd,data,len);
%else:
  MRT_UART_TX(ifac0, data, len, 10);
%endif

  return PACKET_SENT;
}


static inline void iface0_read()
{

  /* Place code for reading bytes from interface 0 here */
%if proto.genUtility:
  int len = uart_read(fd,iface0_rx_buf, 32);
%else:
  //TODO read bytes from interface to iface0_rx_buf
  int len = MRT_UART_RX(ifac0, iface0_rx_buf, 32);  //read 32 bytes at a time
%endif

  ${proto.prefix}_service_feed(0,iface0_rx_buf, len);
}

/*******************************************************************************
  App Init/end
*******************************************************************************/
%if proto.genUtility:
void app_${proto.name.lower()}_init(const char* port, int baud)
{
  /* initialize peripheral for iface_0 */
  if(uart_open(&fd,port, baud))
    printf("successfully opened port: %s\n",port);
  else
    printf("Could not open port: %s",port);
%else:
void app_${proto.name.lower()}_init(mrt_uart_handle_t uart_handle)
{
  /* Set ifac0 to uart handle, this can use any peripheral, but uart is the most common case */
  ifac0 = uart_handle; //set interface to uart handle
%endif

  //initialize service
  ${proto.prefix}_service_init(1);

  ${proto.prefix}_service_register_tx(0, iface0_write);

}

void app_${proto.name.lower()}_end()
{
%if proto.genUtility:
  uart_close(fd);
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
  *@return handling ${proto.prefix}_status
  */
HandlerStatus_e ${proto.prefix}_default_handler( ${proto.prefix}_packet_t * ${proto.prefix}_packet)
{


  return PACKET_NOT_HANDLED;
}
