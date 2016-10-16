# The ArtNET Receiver is based upon the work of 
# https://github.com/Blinkinlabs/BlinkyTape_Python/blob/master/artnet-receiver.py by Matt Mets

import sys
import time

import socket
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
	def __init__(self, universe, comm = None, listenStart = 0, listenStop = 512, ip = UDP_IP, port = UDP_PORT):
		threading.Thread.__init__(self)
		self.universe       = universe
		self.listenStart    = listenStart
		self.listenStop     = listenStop
		self.stopped = False

		self.comm = comm

		print(("Listening for ArtNet Packages in {0}:{1}").format(ip, port))    

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
		self.sock.bind((ip, port))
		self.sock.setblocking(False)

		self.actualData     = [-1] * (listenStop + 1)
		self.lastTime       = time.time()
		self.lastSequence   = 0

		self.callbacks = [False] * (listenStop + 1)

		self.lastPacketTime = time.time()-3;
		self.status = False

	def watchdog(self):
		if self.stopped:
			print "Watchdog ended"
			return
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
			self.comm["signal"] = True

		if statusChanged and not self.status:
			print "ArtNET Signal LOST!!!"
			self.comm["signal"] = False




	def registerCallback(self, address, function):
		'''
			Function needs this footprint:
			function(address, value, changeAmount, completeUniverse)
		'''


		if type(address) is list:
			for singleAddress in address:
				self.callbacks[singleAddress] = (function, True, address)

		else:
			self.callbacks[address] = (function, False, address)

	def stop(self):
		print "Stopping Artnet Receiver"
		self.stopped = True

	def run(self):
		self.watchdog()
		self.callbacksToRun = {}
		while not self.stopped:
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
						# if newDataValue != oldDataValue:
						#     print "Change in Data for Channel {0} went to {1}".format(i + 1, newDataValue)
						if newDataValue != oldDataValue and self.callbacks[i]:
							(callback, isWide, addresses) = self.callbacks[i]
							if isWide:
								self.callbacksToRun[addresses[0]]   = (callback, addresses, isWide)
							else:
								self.callbacksToRun[addresses]      = (callback, addresses, isWide)
						i += 1

					# Do the callbacks
					for cbStartAdrr in self.callbacksToRun:
						(callback, addresses, isWide) = self.callbacksToRun[cbStartAdrr];
						if isWide:
							callback(addresses, [self.actualData[i] for i in addresses], self.actualData)

						else:
							callback(addresses, self.actualData[addresses], self.actualData)

					self.callbacksToRun = {}
					self.lastSequence = packet.sequence

			except socket.error as e:
				time.sleep(0.01);
			except KeyboardInterrupt:
				self.sock.close()
				return False
		print "Artnet Receiver Terminated"