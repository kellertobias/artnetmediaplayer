import pygame
import time
import threading
import multiprocessing

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
			"poshigh": 		self.addr + 3,
			"poslow": 		self.addr + 4,
			"playstate": 	self.addr + 5
		}

		ArtNetReceiver.registerCallback(self.channels.get("volume", 	self.addr) , self.volume)
		ArtNetReceiver.registerCallback(self.channels.get("folder", 	self.addr) , self.load)
		ArtNetReceiver.registerCallback(self.channels.get("file",		self.addr) , self.load)
		ArtNetReceiver.registerCallback(self.channels.get("poshigh", 	self.addr) , self.position)
		ArtNetReceiver.registerCallback(self.channels.get("poslow", 	self.addr) , self.position)
		ArtNetReceiver.registerCallback(self.channels.get("playstate", 	self.addr) , self.playstate)

	def getDMXFootprint(self):
		return len(self.channels.keys())
	
	def printDMXFootprint(self):
		print self.channels

	def playerWorker(self, queue):
		pygame.init()
		position = 0
		while True:
			try:
				(command, value) = queue.get()
				print "AudioPlayer {0}: doing {1} with {2}".format(self.channelNumber, command, value)
				try:
					if   command == "play":
						pygame.mixer.music.play(value,position)
					elif command == "pause":
						pygame.mixer.music.pause()
					elif command == "unpause":
						pygame.mixer.music.unpause()
					elif command == "stop":
						pygame.mixer.music.stop()
					elif command == "load":
						pygame.mixer.music.load(value)
						pass
					elif command == "position":
						position = value
						pygame.mixer.music.rewind()
						pygame.mixer.music.set_pos(value)
						pass
					elif command == "volume":
						pygame.mixer.music.set_volume(value)
						pass
				except Exception as e:
					pass

			except KeyboardInterrupt:
				return False


	def volume(self, channel, value, change, dmx):
		print "Setting Volume to {0}".format(value/255.0)
		self.queue.put(("volume", value/255.0))

	def load(self, channel, value, change, dmx):
		folderChannel = self.channels.get("folder", 	self.addr)
		fileChannel   = self.channels.get("file",		self.addr)

		folderId = dmx[folderChannel]
		fileId = dmx[fileChannel]
		print "Loading File {0}/{1}".format(folderId, fileId)
		nextFile = self.playlist.get(folderId, {}).get(fileId, False)

		if not nextFile:
			# Stop Playback
			self.queue.put(("stop", 0))

		if self.playingFile != nextFile:
			# load file
			self.queue.put(("load", nextFile))
			self.playingFile = nextFile

			# Stop Playback
			self.queue.put(("stop", 0))

			# resume playback with last setup
			self.queue.put((self.actPlaystate, self.actPlaystateValue))

	def position(self, channel, value, change, dmx):
		poshigh = self.channels.get("poshigh", 	self.addr)
		poslog  = self.channels.get("poslow", 	self.addr)
		second = 256*dmx[poshigh] + dmx[poslog]
		print "Setting Position to Second {0}".format(second/10.0)
		self.queue.put(("position", second/10.0))

	def playstate(self, channel, value, change, dmx):
		print "Setting Playstate {0}".format(value)
		newPlayState = "stop"
		psvalue = 0
		if value < 32:
			newPlayState = "stop"	# stop
		elif value < 64:
			if self.actPlaystate == "pause":
				newPlayState = "unpause"
			else:
				newPlayState = "play"	# play
				psvalue = 0
		elif value < 128:			# loop
			newPlayState = "play"
			psvalue = -1
		elif value < 160:			# pause
			newPlayState = "pause"



		if self.actPlaystate != newPlayState:
			self.playstate = newPlayState
			self.actPlaystateValue = psvalue
			self.queue.put((newPlayState, psvalue))