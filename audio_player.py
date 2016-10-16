import pygame
import time
import threading
import multiprocessing
import operator


audioChannels = 0

class AudioPlayer():
	def __init__(self, startAddress, playlist, ArtNetReceiver):
		global audioChannels
		audioChannels += 1

		self.addr = startAddress - 1 # using 1 based addresses
		self.playlist = playlist
		
		self.channelNumber = audioChannels
		
		self.queue = multiprocessing.Queue()
		self.playerProcess = multiprocessing.Process(target=self.playerWorker, args=(self.queue, ))
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

	def playerWorker(self, queue):
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

							pygame.mixer.music.stop()

						elif value < 128:		# PLAY (<64) and LOOP (<128)

							if pause:
								
								pygame.mixer.music.unpause()

							else:	
								loop = False

								pygame.mixer.music.load(actualFile)

								if value < 64:
									self.debugPrint( "MODE", "PLAY")
									pygame.mixer.music.play(0)
									loop = True

								else:
									self.debugPrint( "MODE", "LOOP")
									pygame.mixer.music.play(-1)
									loop = True

							play = True	
							pause = False
								
						elif value < 160:		# PAUSE
							self.debugPrint( "MODE", "PAUSE")

							play = False
							pause = True

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
						pygame.mixer.music.set_volume(value)
				except Exception as e:
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