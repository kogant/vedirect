#!/usr/bin/python
# -*- coding: utf-8 -*-
# Modified to upload(post) data to Emoncms.org - Kogant
# Run in cron
# # m h  dom mon dow   command
# * * * * * /opt/vedirect/vedirect.py  2>&1 | /usr/bin/logger -t veDirectStats

import os, serial, datetime, time, httplib, sys

# apikey emoncms account (change it)
apikey = "" # ie: ff227081609c5f57f2f536b4411a915ba

class vedirect:
    def __init__(self, serialport):
        self.serialport = serialport
        self.ser = serial.Serial(serialport, 19200, timeout=10)
        self.header1 = '\r'
        self.header2 = '\n'
        self.delimiter = '\t'
        self.key = ''
        self.value = ''
        self.bytes_sum = 0;
        self.state = self.WAIT_HEADER
        self.dict = {}

    (WAIT_HEADER, IN_KEY, IN_VALUE, IN_CHECKSUM) = range(4)

    def input(self, byte):
        if self.state == self.WAIT_HEADER:
            self.bytes_sum += ord(byte)
            if byte == self.header1:
                self.state = self.WAIT_HEADER
            elif byte == self.header2:
                self.state = self.IN_KEY

            return None
        elif self.state == self.IN_KEY:
            self.bytes_sum += ord(byte)
            if byte == self.delimiter:
                if (self.key == 'Checksum'):
                    self.state = self.IN_CHECKSUM
                else:
                    self.state = self.IN_VALUE
            else:
                self.key += byte
            return None
        elif self.state == self.IN_VALUE:
            self.bytes_sum += ord(byte)
            if byte == self.header1:
                self.state = self.WAIT_HEADER
                self.dict[self.key] = self.value;
                self.key = '';
                self.value = '';
            else:
                self.value += byte
            return None
        elif self.state == self.IN_CHECKSUM:
            self.bytes_sum += ord(byte)
            self.key = ''
            self.value = ''
            self.state = self.WAIT_HEADER
            if (self.bytes_sum % 256 == 0):
                self.bytes_sum = 0
                return self.dict
            else:
                self.bytes_sum = 0

        else:
            raise AssertionError()

    def read_data(self):
        while True:
            byte = self.ser.read(1)
            packet = self.input(byte)

    def read_data_single(self):
        while True:
            byte = self.ser.read(1)
            packet = self.input(byte)
            if (packet != None):
                return packet
            

    def read_data_callback(self, callbackFunction):
        while True:
            byte = self.ser.read(1)
            packet = self.input(byte)
            if (packet != None):
                callbackFunction(packet)
        
domain="emoncms.org"
baseurl="/input/post.json?apikey="+apikey+"&json="

def print_data_callback(data):
    # global variable
    data=repr(data)
    data=data.replace(" ","") # no spaces allowed
    print(data)
    try:
       conn = httplib.HTTPSConnection(domain)
    except:
       print("Failed connecting to "+domain)
       sys.exit(1)
    else:
       print("Connected successfully to "+domain)
    try:
       conn.request("POST", baseurl+data)
    except:
       print("Failed uploading data")
       sys.exit(1)
    else:
       print("Uploaded data OK")
       sys.exit(0)
    #time.sleep(60)

if __name__ == '__main__':
    ve = vedirect('/dev/ttyUSB0') # Verify this simply by looking at /var/log/syslog when inserting cable.
    ve.read_data_callback(print_data_callback)
