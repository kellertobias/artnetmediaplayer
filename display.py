import sys
import time
import threading



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
		self.fontXxl 		= pygame.font.Font(self.fontpath, 165)
		self.fontXl 		= pygame.font.Font(self.fontpath, 40)
		self.fontMd 		= pygame.font.Font(self.fontpathNormal, 36)
		self.fontSm 		= pygame.font.Font(self.fontpathNormal, 26)

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
		else:
			TextRect.center = (x+TextRect.width/2,y+TextRect.height/2)

		self.screen.blit(TextSurf, TextRect)

	def draw_rect(self, xs, ys, x, y, color):
		pygame.draw.rect(self.screen, color, [x,y,xs,ys], 2)


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
		comm = self.comm
		while not self.stopped:
			try:
				print "Artnet: %s.%s on IP: %s" % (comm.get("universe"), comm.get("address"), comm.get("ip"))
				time.sleep(1)
			except KeyboardInterrupt:
				return False
		print "Display Terminated"


if __name__ == "__main__":
