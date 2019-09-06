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
#include <readline/history.h>

#include "app_${proto.name.lower()}.h"

#define KNRM  "\033[1;0m"
#define KRED  "\033[1;31m"
#define KGRN  "\033[1;32m"
#define KYEL  "\033[1;33m"
#define KBLU  "\033[1;34m"
#define KMAG  "\033[1;35m"
#define KCYN  "\033[1;36m"
#define KWHT  "\033[1;37m"


void quit();
void input_handler(char* input);
void print_usage(const char* messageType);
void print_util_usage();

char **packet_name_completion(const char *, int, int);
char *packet_name_generator(const char *, int);

char *packet_names[] = {
%for packet in proto.packets:
    "${packet.name.lower()}",
%endfor
    NULL
};



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

  int interface_mode = UART_MODE;
  char* connString = NULL;
  printf(KGRN);


  /* Look for options. */
  while ((opt = getopt(argc, argv, "s:u:")) != -1)
  {
      switch (opt)
      {
          case 's':
            connString = optarg;
            break;
          case 'u':
            connString = optarg;
            interface_mode = UDP_MODE;
            break;
          default:
          {
              print_util_usage(NULL);
              quit();
              break;
          }
      }
  }

  if(connString == NULL)
  {
    print_util_usage();
    quit();
  }

  /* Initialize app/service */
  app_${proto.name.lower()}_init(connString, interface_mode);


  pthread_create(&thread_id, NULL, processThread, NULL);
  rl_attempted_completion_function = packet_name_completion;

  while(1)
  {
      input = readline("\033[1;32m>>");
      if((input != NULL) && (input[0] != 0))
      {
        add_history(input);
        input_handler(input);
        free(input);
      }
  }

  quit();
}



/*******************************************************************************
    Arguments to send messages directly
*******************************************************************************/

void input_handler(char* input)
{


  if(input[0] == '{')
  {
      //TODO send json
      return;
  }

  char* messageType = strtok(input," ");
  char* messageFields = strtok(NULL,"");
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
    if(messageFields != NULL)
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
  else if(!strcasecmp(messageType, "x"))
  {
    quit();
  }
  else
  {
      printf("%scommand not recognized..%s\n",KRED,KGRN);
  }

  if(!success)
  {
    print_usage(messageType);
  }
}

void print_util_usage()
{
  printf(KYEL);
  printf("./${proto.utilName} <Options>\n"
         "-u UDP connection string\n"
         "      localPort to open port and listen\n"
         "      localPort:remoteAddress:remotePort to open local port and connect to remote target\n"
         "      example 8010:localhost:8020\n\n"
         "-s Serial connection string\n"
         "      device:baud\n"
         "      example: /dev/ttyS1:9600\n");

}

void print_usage(const char* messageType)
{
    printf(KYEL);
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
    printf(KGRN);
}

char** packet_name_completion(const char *text, int start, int end)
{
    rl_attempted_completion_over = 1;
    return rl_completion_matches(text, packet_name_generator);
}

char* packet_name_generator(const char *text, int state)
{
    static int list_index, len;
    char *name;

    if (!state) {
        list_index = 0;
        len = strlen(text);
    }

    while ((name = packet_names[list_index++])) {
        if (strncmp(name, text, len) == 0) {
            return strdup(name);
        }
    }

    return NULL;
}


void quit()
{
  printf("closing!\n");
  app_${proto.name.lower()}_end();
  exit(0);
}
