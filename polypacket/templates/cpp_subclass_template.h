/**
  *@file ${role.className}.h
  *@brief generated code for ${proto.name} packet service
  *@author make_protocol.py
  *@date ${proto.genTime}
  */

#pragma once

#include "${proto.cppFileName}.h"
#include <thread>

extern "C"{
#include "Platforms/Linux/linux_uart.h"
#include "Platforms/Linux/linux_udp.h"
}



class ${role.className} {
  static int IFACE_UDP = 0;
  public:


    ${role.className}();

  protected:


    /**
      *@brief handles packets and dispatches to handler
      *@param req incoming message
      *@param resp response to message
      *@param number of bytes
      */
    virtual HandlerStatus_e dispatch(${proto.camelPrefix()}Packet& ${proto.prefix}Request, ${proto.camelPrefix()}Packet& ${proto.prefix}Response);

    /*******************************************************************************
      Packet Handlers
    *******************************************************************************/
    % for packet in proto.packets:
    %if packet.hasResponse:
    /*@brief Handler for ${packet.name} packets */
    virtual HandlerStatus_e ${packet.name}Handler(${proto.camelPrefix()}Packet& ${proto.prefix}Request, ${proto.camelPrefix()}Packet& ${proto.prefix}Response );
    %else:
    /*@brief Handler for ${packet.name} packets */
    virtual HandlerStatus_e ${packet.name}Handler(${proto.camelPrefix()}Packet& ${proto.camelPrefix()}Request);
    %endif

    % endfor
    /*@brief Catch-All Handler for unhandled packets */
    virtual HandlerStatus_e defaultHandler(${proto.camelPrefix()}Packet& ${proto.prefix}Request, ${proto.camelPrefix()}Packet& ${proto.prefix}Response );

  private:

    std::thread mThread;
    udp_stream mUdp;

};
