#!/usr/bin/env python3

from polypacket.protocol import *
from polypacket.polyservice import *
import signal
import argparse
import os
import time

args = None
parser = None
SERVICE : PolyService = None

def exit_handler(signum,frame):
    print("Quit application. ")

    if(SERVICE) :
        SERVICE.close()
    exit(0)

# Initialize the argument parser
def init_args():
    global parser
    parser = argparse.ArgumentParser("PolyPacket example in python")
    parser.add_argument('-c', '--connection', type=str, help='Connection string', default="tcp:localhost:8020")
    parser.add_argument('-f', '--file', type=str, help='protocol file', default="sample_protocol.yml")


def main():
    global parser
    global args
    global SERVICE


    #set up exit handler for ctrl+c
    signal.signal(signal.SIGINT, exit_handler)

    #Get arguments
    init_args()
    args = parser.parse_args() 

    inputFile = args.file

    #parse input file
    if os.path.isfile(inputFile):
        SERVICE = PolyService(inputFile)
    else :
        print("Unable to read input file: " + inputFile)
        return 1

    #set handler for 'Data' type packets 
    SERVICE.handlers['Data'] = data_handler

    #set service prints to go to terminal 
    SERVICE.print = print 

    #attempt connection
    SERVICE.connect(args.connection)

    while not SERVICE.isConnected():
        time.sleep(1)
        timeout -=1
        if timeout <= 0:
            print("Connection Timedout, check connection string")
            exit(1)
    
    #Send a packet 
    SERVICE.sendPacket("SendCmd", {"src" : 0x01, "dst": 0x02, "cmd": "led_ON"})
    




def data_handler(service : PolyService, req : PolyPacket, resp : PolyPacket):

    #get field data
    sensorName = req.getField('sensorName')

    print( "Message from {0}: {1}".format(sensorName, req.toJSON))


if __name__ == '__main__':
    main()