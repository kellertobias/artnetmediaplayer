import sys
import time

from socket import (socket, AF_INET, SOCK_DGRAM)
from struct import unpack

import threading

UDP_IP = "" # listen on all sockets- INADDR_ANY
UDP_PORT = 0x1936 # Art-net is supposed to only use this address




class ArtnetPacket:

    ARTNET_HEADER = b'Art-Net\x00'
    OP_OUTPUT = 0x0050

    def __init__(self):
        self.op_code = None
        self.ver = None
        self.sequence = None
        self.physical = None
        self.universe = None
        self.length = None
        self.data = None

    @staticmethod
    def unpack_raw_artnet_packet(raw_data):

        if unpack('!8s', raw_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            return None

        packet = ArtnetPacket()

        # We can only handle data packets
        (packet.op_code,) = unpack('!H', raw_data[8:10])
        if packet.op_code != ArtnetPacket.OP_OUTPUT:
            return None
 
 
        (packet.op_code, packet.ver, packet.sequence, packet.physical,
            packet.universe, packet.length) = unpack('!HHBBHH', raw_data[8:18])
 
        (packet.universe,) = unpack('<H', raw_data[14:16])
 
        (packet.data,) = unpack(
            '{0}s'.format(int(packet.length)),
            raw_data[18:18+int(packet.length)])
 
        return packet

class ArtNetReceiver(threading.Thread):
    def __init__(self, universe, listenStart = 0, listenStop = 512, ip = UDP_IP, port = UDP_PORT):
        threading.Thread.__init__(self)
        self.universe       = universe
        self.listenStart    = listenStart
        self.listenStop     = listenStop

        print(("Listening for ArtNet Packages in {0}:{1}").format(ip, port))    

        self.sock = socket(AF_INET, SOCK_DGRAM)  # UDP
        self.sock.bind((ip, port))
        # self.sock.setblocking(False)

        self.actualData     = [0] * (listenStop + 1)
        self.lastTime       = time.time()
        self.lastSequence   = 0

        self.callbacks = [False] * (listenStop + 1)
        self.callbacksToRun = []

        self.lastPacketTime = time.time();
        self.status = False

    def watchdog(self):
        threading.Timer(0.5, self.watchdog).start();
        actTime = time.time();

        statusChanged = False

        if actTime - self.lastPacketTime > 2:
            statusChanged = self.status != False
            self.status = False

        else:
            statusChanged = self.status != True
            self.status = True

        if statusChanged and self.status:
            print "Now Receiving ArtNET Signal"

        if statusChanged and not self.status:
            print "ArtNET Signal LOST!!!"




    def registerCallback(self, address, function):
        '''
            Function needs this footprint:
            function(address, value, changeAmount, completeUniverse)
        '''
        self.callbacks[address] = function


    def run(self):
        self.watchdog()
        while True:
            try:
           
                data, addr = self.sock.recvfrom(1024)
           

                packet = ArtnetPacket.unpack_raw_artnet_packet(data)
                if packet != None:
                    self.lastPacketTime = time.time();

                if packet != None and packet.universe == self.universe:
                    if packet.sequence != self.lastSequence:
                        pass
                    i = 0;
                    for newData in packet.data:
                        if i >= self.listenStop:
                            break;
                        oldDataValue = self.actualData[i]
                        newDataValue = unpack('B',newData)[0]
                        self.actualData[i] = newDataValue
                        if newDataValue != oldDataValue and self.callbacks[i]:
                            print "Change in Data for Channel {0} went to {1}".format(i, newDataValue)
                            difference = newDataValue - oldDataValue;
                            self.callbacksToRun.append((i, newDataValue, difference, self.callbacks[i]));
                        i += 1

                    # Do the callbacks
                    for cbSet in self.callbacksToRun:
                        (channel, value, difference, function) = cbSet;

                        function(channel, value, difference, self.actualData)
                    
                    self.callbacksToRun = []
                    self.lastSequence = packet.sequence

            except KeyboardInterrupt:
                self.sock.close()
                return False