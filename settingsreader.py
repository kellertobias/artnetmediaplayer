import sys
import os
import fnmatch
import threading
import json
import time

class Settings():
	def __init__(self):
		self.stopped = False
		self.initialized = False
		try:
			with open('config.json') as data_file:    
				config = json.load(data_file)

		except Exception as e:
			pass

		if config.get("useInternal", False):
			return config
		
	def stop(self):
		self.stopped = True

	def get_settings(self):
		print "Start Checking Drives"
		while (not self.stopped):
			try:
				self.drive = ""
				matches = []

				for root, folders, files in os.walk("/media/"):
					#print root
					for file in fnmatch.filter(files, "config.json"):
						matches.append(os.path.join(root))

				# Check if we found excactly one USB Flashdrive
				if len(matches) == 1:
					print "Possible candidate found. Path:"
					print matches[0]
					self.drive = matches[0]

				elif len(matches) > 1:
					print "Too much candidates found. Please plug only one USB drive in."
					print matches

				if (self.initialized == False and len(self.drive) > 1):
					with open('%s/config.json' % self.drive) as data_file:
						config = json.load(data_file)

					config["basedir"] = self.drive


					for outer in config.get("audio_playlist", []):
						for inner in config.get("audio_playlist").get(outer, []):
							file = config.get("audio_playlist").get(outer).get(inner, False)
							if not file:
								continue
							
							if type(file) is not str and type(file) is not unicode:
								continue

							if file.startswith("/"):
								continue

							config["audio_playlist"][outer][inner] = self.drive + "/" + file

					self.initialized = True
					self.stopped = True

					print "Flashdrive initialised."

					return config
					

				time.sleep(1)
			except KeyboardInterrupt:
				print "Aborting"
				return False