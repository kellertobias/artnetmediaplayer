import pygame
import time
import threading
import multiprocessing
import operator


audioChannels = 0

class AudioPlayer(threading.Thread):
	def __init__(self, startAddress, playlist, ArtNetReceiver, systemCommunication):
		threading.Thread.__init__(self)
		global audioChannels
		audioChannels += 1


		self.addr = startAddress - 1 # using 1 based addresses
		self.playlist = playlist
		
		self.channelNumber = audioChannels
		self.comm = systemCommunication

		self.comm["audio"][self.channelNumber] = {}
		
		self.queue = multiprocessing.Queue()
		self.outqueue = multiprocessing.Queue()
		self.playerProcess = multiprocessing.Process(target=self.playerWorker, args=(self.queue, self.outqueue))
		self.playerProcess.start()
		
		self.actPlaystate = "stop"
		self.actPlaystateValue = 0
		self.playingFile  = False

		self.channels = {
			"volume": 		self.addr + 0,
			"folder": 		self.addr + 1,
			"file": 		self.addr + 2,
			"playstate": 	self.addr + 3
		}

		ArtNetReceiver.registerCallback(self.channels.get("volume", 	self.addr) , self.volume)
		ArtNetReceiver.registerCallback([
			self.channels.get("folder", 	self.addr),
			self.channels.get("file",		self.addr)
		] , self.load)
		ArtNetReceiver.registerCallback(self.channels.get("playstate", 	self.addr) , self.playstate)

		self.stopped = False
		self.start()


	def stop(self):
		print "Audioplayer %s Ending" % self.channelNumber
		self.stopped = True

	def run(self):
		while not self.stopped:
			try:
				if self.outqueue.empty():
					time.sleep(0.1)
				else:
					(param, value) = self.outqueue.get(False, 0.75)
					self.comm["audio"][self.channelNumber][param] = value
					time.sleep(0.01)

			except KeyboardInterrupt:
				self.stopped = True
				return False

		print "Audioplayer %s Terminated" % self.channelNumber
		

	def getDMXFootprint(self):
		return len(self.channels.keys())
	
	def printDMXFootprint(self):
		sorted_out = sorted(self.channels.items(), key=operator.itemgetter(1))
		print "AudioPlayer {0}: ".format(self.channelNumber)
		print "  +------------+---------+"
		print "  | {0:10s} | {1} |".format("Parameter", "Address")
		print "  +------------+---------+"
		for item in sorted_out:
			print "  | {0:10s} | {1:4d}    |".format(item[0], item[1]+1)
		print "  +------------+---------+"
		print ""
		

	def debugPrint(self, method, message):
		print "[Player {0:2d}, {1:6s}]: {2}".format(self.channelNumber, method, message)

	def playerWorker(self, queue, comm):
		actualFile = False
		pygame.init()
		position = 0
		pause = False
		play  = False
		loop = False
		while True:
			try:
				(command, value) = queue.get()
				try:
					if   command == "playmode":
						if value < 32:		# STOP
							self.debugPrint( "MODE", "STOP")

							pause = False
							play = False
							loop = False

							comm.put(("state", "stop"))

							pygame.mixer.music.stop()

						elif value < 128:		# PLAY (<64) and LOOP (<128)

							if pause:
								
								pygame.mixer.music.unpause()
								comm.put(("state", "unpause"))

							else:	
								loop = False

								pygame.mixer.music.load(actualFile)

								if value < 64:
									self.debugPrint( "MODE", "PLAY")
									pygame.mixer.music.play(0)
									loop = True
									comm.put(("state", "play"))

								else:
									self.debugPrint( "MODE", "LOOP")
									pygame.mixer.music.play(-1)
									loop = True
									comm.put(("state", "loop"))

							play = True	
							pause = False
								
						elif value < 160:		# PAUSE
							self.debugPrint( "MODE", "PAUSE")

							play = False
							pause = True
							comm.put(("state", "pause"))
							pygame.mixer.music.pause()

						else:					# Do Nothing Mode / Reserved
							self.debugPrint( "MODE", "No Change")


					elif command == "load":
						(folderId, fileId, nextFile) = value

						if not nextFile:
							self.debugPrint( "LOAD", "{0}/{1}: No File at Index".format(folderId, fileId))
							actualFile = False
							continue;
						self.debugPrint( "LOAD", "{0}/{1}: {2}".format(folderId, fileId, nextFile))
						
						pygame.mixer.music.load(nextFile)
						actualFile = nextFile

						comm.put(("folder", folderId))
						comm.put(("fileNo", fileId))
						comm.put(("file", nextFile))

						if play or pause:
							if loop:
								pygame.mixer.music.play(-1)
								self.debugPrint( "LOAD", "Resuming Looped")
							else:
								pygame.mixer.music.play(0)
								self.debugPrint( "LOAD", "Resuming Play")

						if pause:
							pygame.mixer.music.pause()
							self.debugPrint( "LOAD", "Resuming Pause")




					elif command == "volume":
						self.debugPrint( "VOLUME", "{0:5.1f}%".format(value * 100))
						comm.put(("volume", value * 100))
						pygame.mixer.music.set_volume(value)

				except Exception as e:
					print "Error in audioplayer %s" % self.channelNumber
					print e
					pass

			except KeyboardInterrupt:
				return False


	def volume(self, channel, value, dmx):
		self.queue.put(("volume", value/255.0))

	def load(self, channel, value, dmx):
		folderId = value[0]
		fileId   = value[1]

		nextFile = self.playlist.get(str(folderId), {}).get(str(fileId), False)
		self.queue.put(("load", (folderId, fileId, nextFile)))

	def playstate(self, channel, value, dmx):
		self.queue.put(("playmode", value))