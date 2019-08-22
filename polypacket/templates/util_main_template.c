/**
 * \file  lib_front.c
 *
 * \brief Front panel access utility.
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

#include "app_${proto.name.lower()}.h"

void sig_exit();
void catch_sigterm();
void run_${proto.prefix}_args(int argc, char* argv[],int idx);
void printUsage(const char* name);






int main(int argc, char* argv[])
{
  int opt;
  void catch_sigterm(); /* so we can exit gracefulyl with ctrl+c  */

  /* Look for options. */
    while ((opt = getopt(argc, argv, "mp")) != -1)
    {
        switch (opt)
        {
            case 'm':
            {
              break;
            }
            default:
            {
                printUsage(argv[0]);
                break;
            }
        }
    }

    /* Initialize app/service */
    app_${proto.name.lower()}_init("/dev/ttyUSB0", 9600);

    /* Parse non-flag options */
    if (optind < argc)
      run_${proto.prefix}_args(argc, argv,optind);


  while(1)
  {
    app_${proto.name.lower()}_process();
    sleep(0.001);
  }

  return 0;
}



/*******************************************************************************
    Arguments to send messages directly
*******************************************************************************/

void run_${proto.prefix}_args(int argc, char* argv[], int idx)
{
  char strArgs[128]={0};
  int paramCount = argc - (idx +1);

  /* all fields */
  %for field in proto.fields:
  ${field.getFieldDeclaration()}; //${field.desc}
  %endfor

  if(argc < idx)
    return;

  if(argc > 2)
  {
    //concat args so we can sscanf easily
    for (int i = idx+1; i < argc; ++i)
    {
      strcat(strArgs, argv[i]);
      strcat(strArgs, " ");
    }
  }

  if(!strcasecmp(argv[1], "ping"))
  {
    ${proto.prefix}_sendPing(0);
  }
%for packet in proto.packets:
%if not packet.standard:
  else if((!strcasecmp(argv[idx], "${packet.name}")) && (paramCount == ${packet.globalName}->mFieldCount))       //${packet.desc}
  {
    printf("%s\n",strArgs );
%if len(packet.fields) >0:
    sscanf(strArgs, "\
%for field in packet.fields:
${field.getFormat()} \
%endfor
" \
%for field in packet.fields:
%if field.isArray:
, field_${field.name} \
%else:
, &field_${field.name} \
%endif
%endfor
);
%endif
    ${proto.prefix}_send${packet.camel()}(0\
  %for idx,field in enumerate(packet.fields):
, field_${field.name} \
  %endfor
);
  }
%endif
%endfor
  else
  {
    printUsage(argv[0]);
  }
}

void printUsage(const char* name)
{
  printf("Usage: %s [OPTIONS] [PacketType] [Parameterss]\n", name );
  printf("Available Packet Types:\n" );

%for packet in proto.packets:
%if not packet.standard:

  printf("\n/*******************************************************************\n");
  printf("    ${packet.name}  - ${packet.desc}\n");
  printf("*******************************************************************/\n");
  printf("${packet.name}  \
  %for field in packet.fields:
  ${field.name} \
  %endfor
  \n");
%for field in packet.fields:
  printf("\t${field.name} [${field.cType}] - ${field.desc} \n");
%endfor
%endif
%endfor
  exit(1);
}


void sig_exit()
{
  printf("closing!\n");
  app_${proto.name.lower()}_end();
  exit(0);
}

void catch_sigterm()
{
    static struct sigaction _sigact;

    memset(&_sigact, 0, sizeof(_sigact));
    _sigact.sa_sigaction = sig_exit;
    _sigact.sa_flags = SA_SIGINFO;

    sigaction(SIGINT, &_sigact, NULL);
}
