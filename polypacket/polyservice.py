#!/usr/bin/python3
#
#@file polyservice.py
#@brief python module to run a command line utility for a protocol
#@author Jason Berger
#@date 02/19/2019
#

import sys
import pkgutil
import subprocess
from polypacket.protocol import *





class PolyPacket:
    def __init__(self):
        self.name = ""

class PolyIface:
    def __init__(self, connStr):
        connStr = connStr

class PolyService:
    def __init__(self, protocol):
        self.protocol = protocol
