#!/usr/bin/python

import serial
import socket

from escpos import *
from constants import *
from exceptions import *
from time import sleep

class Serial(Escpos):
    """ Define Serial printer """

    def __init__(self, devfile="/dev/ttyUSB0", baudrate=19200, bytesize=8, timeout=1):
        """
        @param devfile  : Device file under dev filesystem
        @param baudrate : Baud rate for serial transmission
        @param bytesize : Serial buffer size
        @param timeout  : Read/Write timeout
        """
        self.devfile  = devfile
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.timeout  = timeout
        self.open()


    def open(self):
        """ Setup serial port and set is as escpos device """
        self.device = serial.Serial(port=self.devfile, baudrate=self.baudrate, bytesize=self.bytesize, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=self.timeout, dsrdtr=True)

        if self.device is not None:
            print "Serial printer enabled"
        else:
            print "Unable to open serial printer on: %s" % self.devfile


    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.write(msg)


    def __del__(self):
        """ Close Serial interface """
        if self.device is not None:
            self.device.close()


