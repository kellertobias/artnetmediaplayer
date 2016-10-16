import sys
import time
import threading

class Display(threading.Thread):
	def __init__(self, comm):
		threading.Thread.__init__(self)
		self.comm = comm;
		self.stopped = False

	def stop(self):
		print "Display Ending"
		self.stopped = True

	def run(self): 
		comm = self.comm
		while not self.stopped:
			try:
				print "Artnet: %s.%s on IP: %s" % (comm.get("universe"), comm.get("address"), comm.get("ip"))
				time.sleep(1)
				print self.comm
			except KeyboardInterrupt:
				self.sock.close()
				return False
		print "Display Terminated"