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

#include <pthread.h>
#include <readline/readline.h>


#include "app_${proto.name.lower()}.h"

void quit();
void input_handler(char* input);
void print_usage(const char* messageType);



void processThread(void *vargp)
{
    while(1)
    {
        app_${proto.name.lower()}_process();
        sleep(0.001);
    }
}


int main(int argc, char* argv[])
{
  int opt;
  char* input;
  pthread_t thread_id;

  int baud = 9600;
  char* portName = "/dev/ttyUSB0";


  /* Look for options. */
    while ((opt = getopt(argc, argv, "mb:p:")) != -1)
    {
        switch (opt)
        {
            case 'm':
              break;
            case 'p':
              portName = optarg;
              break;
            case 'b':
              baud = atoi(optarg);
              break;
            default:
            {
                print_usage(NULL);
                break;
            }
        }
    }

  /* Initialize app/service */
  app_${proto.name.lower()}_init("/dev/ttyUSB0", 9600);


  pthread_create(&thread_id, NULL, processThread, NULL);

  while(1)
  {
      input = readline(">>");
      add_history(input);
      input_handler(input);
      free(input);
  }

  quit();
}



/*******************************************************************************
    Arguments to send messages directly
*******************************************************************************/

void input_handler(char* input)
{

  if(*input!=0)
  {
      add_history(input);
  }

  if(input[0] == '{')
  {
      //TODO send json
      return;
  }

  char* messageType = strtok(input," ");
  char* messageFields = strtok(NULL,0);
  int fieldCount =0;
  bool success = false;

  /* all fields */
  %for field in proto.fields:
  ${field.getFieldDeclaration()}; //${field.desc}
  %endfor


  if(!strcasecmp(messageType, "ping"))
  {
    ${proto.prefix}_sendPing(0);
  }
%for packet in proto.packets:
%if not packet.standard:
  else if(!strcasecmp(messageType, "${packet.name}"))       //${packet.desc}
  {
%if len(packet.fields) >0:
    fieldCount = sscanf(messageFields, "\
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
    if(fieldCount == ${packet.globalName}->mFieldCount)
    {
      ${proto.prefix}_send${packet.camel()}(0\
  %for idx,field in enumerate(packet.fields):
, field_${field.name} \
  %endfor
);
      success = true;
    }
  }
%endif
%endfor

  if(!success)
  {
    print_usage(messageType);
  }
}

void print_usage(const char* messageType)
{

%for packet in proto.packets:
%if not packet.standard:

  if((messageType == NULL) || (!strcasecmp(messageType, "${packet.name}")))     //${packet.desc}
  {
    printf("${packet.name}  \
    %for field in packet.fields:
    <${field.name}> \
    %endfor
    \n"
  %for field in packet.fields:
           "\t${field.name} [${field.cType}] - ${field.desc} \n"
  %endfor
           );
  }
  %endif
%endfor
}


void quit()
{
  printf("closing!\n");
  app_${proto.name.lower()}_end();
  exit(0);
}
