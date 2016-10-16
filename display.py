import sys
import time
import threading

import os, syslog, sys, signal

import pygame

import string

import json

maxLineLength = 36;
display_width = 480;
display_height = 320;


class pitft :
	screen = None;
	colourBlack = (0, 0, 0)
	
	def __init__(self):
		"Ininitializes a new pygame screen using the framebuffer"
		# Based on "Python GUI in Linux frame buffer"
		# http://www.karoltomala.com/blog/?p=679
		print "Setting up TFT Screen"
		disp_no = os.getenv("DISPLAY")
		if disp_no:
			print "I'm running under X display = {0}".format(disp_no)

		os.putenv('SDL_FBDEV', '/dev/fb1')
		
		# Select frame buffer driver
		# Make sure that SDL_VIDEODRIVER is set
		driver = 'fbcon'
		if not os.getenv('SDL_VIDEODRIVER'):
			os.putenv('SDL_VIDEODRIVER', driver)
		try:
			pygame.display.init()
		except pygame.error:
			print 'Driver: {0} failed.'.format(driver)
			exit(0)
		
		print "Screen Initialized"

		size = (pygame.display.Info().current_w, pygame.display.Info().current_h)

		print "Got Size"
		self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
		pygame.mouse.set_visible(False)

		print "Mode is set"
		# Clear the screen to start
		self.screen.fill((0, 0, 0))        

		print "Screen is black"
		# Initialise font support
		pygame.font.init()
		print "Fonts Initialized"
		# Render the screen
		pygame.display.update()

		print "Loading Fonts"

		#u'droidsans', u'freemono', u'droidsansthai', u'droidsansarmenian', u'droidsansmono', u'freeserif', u'roboto', u'dejavuserif', u'droidsansethiopic', u'droidsanshebrew', u'dejavusans', u'droidsansgeorgian', u'droidsansfallback', u'robotocondensed', u'freesans', u'dejavusansmono', u'droidserif', u'droidsansjapanese', u'droidarabicnaskh'

		#self.fontpath = pygame.font.match_font('dejavusansmono')
		self.fontpath 		= "fonts/Roboto-Light.ttf"
		self.fontpathNormal = "fonts/Roboto-Regular.ttf"
		self.fontXxl 		= pygame.font.Font(self.fontpath, 34)
		self.fontXl 		= pygame.font.Font(self.fontpath, 30)
		self.fontMd 		= pygame.font.Font(self.fontpathNormal, 24)
		self.fontSm 		= pygame.font.Font(self.fontpathNormal, 18)

		print "Fonts Loaded"

	def __del__(self):
		"Destructor to make sure pygame shuts down, etc."

	def color_surface(self, surface, red, green, blue):
		arr = pygame.surfarray.pixels3d(surface)
		arr[:,:,0] = red
		arr[:,:,1] = green
		arr[:,:,2] = blue

	def text_objects(self, text, font, color):
		textSurface = font.render(text, True, color)
		return textSurface, textSurface.get_rect()

	def message_display(self, text, size, x, y, color):
		global display_width, display_height
		if size == "sm":
			sizeText  = self.fontSm
		elif size == "md":
			sizeText  = self.fontMd
		elif size == "xl":
			sizeText  = self.fontXl
		elif size == "xxl":
			sizeText  = self.fontXxl

		TextSurf, TextRect = self.text_objects(text, sizeText, color)

		if x == False:
			TextRect.center = ((display_width/2),y+TextRect.height/2)
		elif x < 0:
			TextRect.center = (display_width - TextRect.width/2 +x ,y+TextRect.height/2)
		else:
			TextRect.center = (x+TextRect.width/2,y+TextRect.height/2)

		self.screen.blit(TextSurf, TextRect)

	def draw_rect(self, xs, ys, x, y, color):
		pygame.draw.rect(self.screen, color, [x,y,xs,ys], 2)

	def draw_circle(self, x, y, r, color, width = 0):
		pygame.draw.circle(self.screen, color, [x,y], r, width)


	def showimage(self, image, x,y, xscale=False,yscale=False, color=False):
		global display_width, display_height
		icon = image
		logo = pygame.image.load(icon).convert_alpha()
		if xscale != False and yscale != False:
			logo = pygame.transform.scale(logo, (xscale,yscale))
		if color != False:
			self.color_surface(logo, color["r"],color["g"],color["b"])

		self.screen.blit(logo, (x, y))

class Display(threading.Thread):
	def __init__(self, comm):
		threading.Thread.__init__(self)
		self.comm = comm;
		self.stopped = False
		self.mytft = pitft()

	def stop(self):
		print "Display Ending"
		self.stopped = True

	def run(self): 
		colourBlack = (0, 0, 0)
		colourGreen = (0, 220, 0)
		colourYellow = (225, 200, 0)
		colourRed = (200, 0, 0)
		colourRedBright = (255, 0, 0)
		colourWhite = (255, 255, 255)

		blink = True

		comm = self.comm
		while not self.stopped:
			try:
				self.mytft.screen.fill(colourBlack)	
				self.mytft.message_display("TUDS ArtNet Media Player", "xl", False, 10, colourWhite)

				dmx = "Not Configured"

				if not comm.get("signal", False):
					dmx = "DMX: %s.%s - Kein Signal" % (comm.get("universe", "-"), comm.get("address", "-"))

					if blink:
						self.mytft.draw_circle(10, 300, 5, colourRed)
						blink = False
					else:
						self.mytft.draw_circle(10, 300, 5, colourRedBright)
						blink = True

				elif comm.get("universe", None) is not None and comm.get("address", None) is not None:
					dmx = "DMX: %s.%s" % (comm.get("universe"), comm.get("address"))
					self.mytft.draw_circle(10, 300, 5, colourGreen)
				else:
					dmx = "DMX: -/-"

				self.mytft.message_display(dmx, "sm", 25, 290, colourWhite)

				self.mytft.message_display("IP: %s" % comm.get("ip"), "sm", -10, 290, colourWhite)

				for 
				
				pygame.display.update()

				time.sleep(1)
			except KeyboardInterrupt:
				return False
		print "Display Terminated"


if __name__ == "__main__":
	disp = Display({
		"ip": "10.0.2.3",
		"universe": 0,
		"address": 100,
	})

	disp.run()