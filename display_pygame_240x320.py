#!/usr/bin/env python3
'''
*****************************************
PiFire Display Interface Library
*****************************************

 Description: This library supports using pygame 
 on your Linux development PC for debug and development 
 purposes. Only works in a graphical desktop 
 environment.  Tested on Ubuntu 20.04.  

*****************************************
'''

'''
 Imported Libraries
'''
import time
import socket
import qrcode
import threading
import pygame 
from PIL import Image, ImageDraw, ImageFont

'''
Display class definition
'''
class Display:

	def __init__(self, buttonslevel='HIGH', rotation=0, units='F'):
		# Init Global Variables and Constants
		self.units = units
		self.displayactive = False
		self.in_data = None
		self.status_data = None
		self.displaytimeout = None 
		self.displaycommand = 'splash'

		# Init Display Device, Input Device, Assets
		self._init_globals()
		self._init_assets() 
		self._init_display_device()

	def _init_globals(self):
		# Init constants and variables 
		self.WIDTH = 320
		self.HEIGHT = 240
		self.inc_pulse_color = True 
		self.icon_color = 100
		self.fan_rotation = 0
		self.auger_step = 0

	def _init_display_device(self):
		# Setup & Start Display Loop Thread 
		display_thread = threading.Thread(target=self._display_loop)
		display_thread.start()

	def _display_loop(self):
		# Init Device
		pygame.init()
		# set the pygame window name 
		pygame.display.set_caption('PiFire Device Display')
		# Create Display Surface
		self.display_surface = pygame.display.set_mode(size=(self.WIDTH, self.HEIGHT), flags=pygame.SHOWN)
		self.displaycommand = 'splash'

		'''
		Main display loop
		'''
		while True:
			pygame.time.delay(100)
			events = pygame.event.get()  # Gets events (required for keypresses to be registered)

			''' Normal display loop'''
			if self.displaytimeout:
				if time.time() > self.displaytimeout:
					self.displaycommand = 'clear'

			if self.displaycommand == 'clear':
				self.displayactive = False
				self.displaytimeout = None 
				self.displaycommand = None
				self._display_clear()

			if self.displaycommand == 'splash':
				self.displayactive = True
				self._display_splash()
				self.displaytimeout = time.time() + 3
				self.displaycommand = None
				pygame.time.delay(3000) # Hold splash screen for 3 seconds

			if self.displaycommand == 'text': 
				self.displayactive = True
				self._display_text()
				self.displaycommand = None
				self.displaytimeout = time.time() + 10 

			if self.displaycommand == 'network':
				self.displayactive = True
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				s.connect(("8.8.8.8", 80))
				networkip = s.getsockname()[0]
				if (networkip != ''):
					self._display_network(networkip)
					self.displaytimeout = time.time() + 30
					self.displaycommand = None
				else:
					self.display_text("No IP Found")

			if self.displayactive:
				if not self.displaytimeout:
					if (self.in_data is not None) and (self.status_data is not None):
						self._display_current(self.in_data, self.status_data)
								
		pygame.quit()

	'''
	============== Graphics / Display / Draw Methods ============= 
	'''
	def _init_assets(self): 
		self._init_background()
		self._init_splash()

	def _init_background(self):
		self.background = Image.open('background.jpg')
		self.background = self.background.resize((self.WIDTH, self.HEIGHT))
	
	def _init_splash(self):
		self.splash = Image.open('color-boot-splash.png')
		(self.splash_width, self.splash_height) = self.splash.size
		self.splash_width *= 2
		self.splash_height *= 2
		self.splash = self.splash.resize((self.splash_width, self.splash_height))

	def _rounded_rectangle(self, draw, xy, rad, fill=None):
		x0, y0, x1, y1 = xy
		draw.rectangle([(x0, y0 + rad), (x1, y1 - rad)], fill=fill)
		draw.rectangle([(x0 + rad, y0), (x1 - rad, y1)], fill=fill)
		draw.pieslice([(x0, y0), (x0 + rad * 2, y0 + rad * 2)], 180, 270, fill=fill)
		draw.pieslice([(x1 - rad * 2, y1 - rad * 2), (x1, y1)], 0, 90, fill=fill)
		draw.pieslice([(x0, y1 - rad * 2), (x0 + rad * 2, y1)], 90, 180, fill=fill)
		draw.pieslice([(x1 - rad * 2, y0), (x1, y0 + rad * 2)], 270, 360, fill=fill)
		return (draw)

	def _create_icon(self, charid, size, color):
		# Get font and character size 
		font = ImageFont.truetype("FA-Free-Solid.otf", size)
		# Create canvas
		iconcanvas = Image.new('RGBa', font.getsize(charid))
		# Create drawing object
		draw = ImageDraw.Draw(iconcanvas)
		draw.text((0, 0), charid, font=font, fill=color)
		iconcanvas = iconcanvas.crop(iconcanvas.getbbox())
		return(iconcanvas)	

	def _paste_icon(self, icon, canvas, position, rotation, bgcolor):
		# First fill the background 
		bgfill = ImageDraw.Draw(canvas)
		# Rotate the icon
		icon = icon.rotate(rotation)
		(icon_width, icon_height) = icon.size
		#bgfill.rectangle([(position[0], position[1]), (position[0] + icon_width, position[1] + icon_height)], fill=bgcolor)
		# Set the position & paste the icon onto the canvas
		canvas.paste(icon, position, icon)
		return(canvas)

	def _draw_fan_icon(self, canvas):
		# F = Fan (Upper Left)
		icon_char = '\uf863'
		icon_color = (0, self.icon_color, 255)

		drawing = ImageDraw.Draw(canvas)
		# Draw Rounded Rectangle Border
		drawing = self._rounded_rectangle(drawing, (
			self.WIDTH // 8 - 22, self.HEIGHT // 6 - 22, self.WIDTH // 8 + 22, self.HEIGHT // 6 + 22), 5,
										icon_color)
		# Fill Rectangle with Black
		drawing = self._rounded_rectangle(drawing, (
			self.WIDTH // 8 - 20, self.HEIGHT // 6 - 20, self.WIDTH // 8 + 20, self.HEIGHT // 6 + 20), 5,
										(0, 0, 0))
		# Create Icon Image
		icon = self._create_icon(icon_char, 36, icon_color)
		position = (self.WIDTH // 8 - 18, self.HEIGHT // 6 - 18)
		canvas = self._paste_icon(icon, canvas, position, self.fan_rotation, (0,0,0))
		return(canvas)

	def _draw_auger_icon(self, canvas):
		# A = Auger (Center Left)
		icon_char = '\uf101'
		icon_color_tuple = (0, self.icon_color, 0)
		# Create a drawing object
		drawing = ImageDraw.Draw(canvas)
		# Draw Rounded Rectangle Border
		drawing = self._rounded_rectangle(drawing, (
			self.WIDTH // 8 - 22, self.HEIGHT // 2.5 - 22, self.WIDTH // 8 + 22, self.HEIGHT // 2.5 + 22), 5,
										icon_color_tuple)
		# Fill Rectangle with Black
		drawing = self._rounded_rectangle(drawing, (
			self.WIDTH // 8 - 20, self.HEIGHT // 2.5 - 20, self.WIDTH // 8 + 20, self.HEIGHT // 2.5 + 20), 5,
										(0, 0, 0))
		# Create Icon Image
		icon = self._create_icon(icon_char, 36, icon_color_tuple)
		(icon_width, icon_height) = icon.size 
		position = ((self.WIDTH // 8 - 18) + (icon_width // 8) + self.auger_step, (int(self.HEIGHT // 2.5) - 18) + (icon_height // 3))
		canvas = self._paste_icon(icon, canvas, position, 0, (0,0,0))
		return(canvas)

	def _display_clear(self):
		self.display_surface.fill((0,0,0))
		pygame.display.update() 

	def _display_canvas(self, canvas):
		# Convert to PyGame and Display
		strFormat = canvas.mode
		size = canvas.size
		raw_str = canvas.tobytes("raw", strFormat)
		
		self.display_image = pygame.image.fromstring(raw_str, size, strFormat)

		self.display_surface.fill((255,255,255))
		self.display_surface.blit(self.display_image, (0, 0))

		pygame.display.update() 

	def _display_splash(self):
		# Create canvas
		img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(0, 0, 0))

		# Set the position & paste the splash image onto the canvas
		position = ((self.WIDTH - self.splash_width) // 2, (self.HEIGHT - self.splash_height) // 2)
		img.paste(self.splash, position)

		self._display_canvas(img)

	def _display_text(self):
		# Create canvas
		img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(0, 0, 0))

		# Create drawing object
		draw = ImageDraw.Draw(img)

		font = ImageFont.truetype("impact.ttf", 42)
		(font_width, font_height) = font.getsize(self.displaydata)
		draw.text((self.WIDTH // 2 - font_width // 2, self.HEIGHT // 2 - font_height // 2), self.displaydata, font=font, fill=255)

		self._display_canvas(img)

	def _display_network(self, networkip):
		# Create canvas
		img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(255, 255, 255))
		img_qr = qrcode.make('http://' + networkip)
		img_qr_width, img_qr_height = img_qr.size
		img_qr_width *= 2
		img_qr_height *= 2
		w = min(self.WIDTH, self.HEIGHT)
		new_image = img_qr.resize((w, w))
		position = (int((self.WIDTH/2)-(w/2)), 0)
		img.paste(new_image, position)

		self._display_canvas(img)

	def _display_current(self, in_data, status_data):
		# Create canvas
		img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(0, 0, 0))

		# Set the position and paste the background image onto the canvas
		position = (0, 0)
		img.paste(self.background, position)

		# Create drawing object
		draw = ImageDraw.Draw(img)

		# Grill Temp Circle
		draw.ellipse((80, 10, 240, 170), fill=(50, 50, 50))  # Grey Background Circle
		if in_data['GrillTemp'] < 0:
			endpoint = 0
		elif self.units == 'F':
			endpoint = ((360 * in_data['GrillTemp']) // 600) + 90
		else:
			endpoint = ((360 * in_data['GrillTemp']) // 300) + 90
		draw.pieslice((80, 10, 240, 170), start=90, end=endpoint, fill=(200, 0, 0))  # Red Arc for Temperature
		if (in_data['GrillSetPoint'] > 0) and (status_data['mode'] == 'Hold'):
			if self.units == 'F':
				setpoint = ((360 * in_data['GrillSetPoint']) // 600) + 90
			else:
				setpoint = ((360 * in_data['GrillSetPoint']) // 300) + 90
			draw.pieslice((80, 10, 240, 170), start=setpoint - 2, end=setpoint + 2,
							fill=(0, 200, 255))  # Blue Arc for SetPoint
		if (in_data['GrillNotifyPoint'] > 0) and (status_data['notify_req']['grill']):
			if self.units == 'F':
				setpoint = ((360 * in_data['GrillNotifyPoint']) // 600) + 90
			else:
				setpoint = ((360 * in_data['GrillNotifyPoint']) // 300) + 90
			draw.pieslice((80, 10, 240, 170), start=setpoint - 2, end=setpoint + 2,
							fill=(255, 255, 0))  # Yellow Arc for Notify Point

		draw.ellipse((90, 20, 230, 160), fill=(0, 0, 0))  # Black Circle for Center


		# Grill Temp Label
		font = ImageFont.truetype("trebuc.ttf", 16)
		text = "Grill"
		(font_width, font_height) = font.getsize(text)
		draw.text((self.WIDTH // 2 - font_width // 2, 20), text, font=font, fill=(255, 255, 255))

		# Grill Set Point (Small Centered Top)
		if (in_data['GrillSetPoint'] > 0) and (status_data['mode'] == 'Hold'):
			font = ImageFont.truetype("trebuc.ttf", 16)
			text = ">" + str(in_data['GrillSetPoint'])[:5] + "<"
			(font_width, font_height) = font.getsize(text)
			draw.text((self.WIDTH // 2 - font_width // 2, 45 - font_height // 2), text, font=font,
						fill=(0, 200, 255))

		# Grill Temperature (Large Centered)
		if (self.units == 'F'):
			font = ImageFont.truetype("trebuc.ttf", 80)
			text = str(in_data['GrillTemp'])[:5]
			(font_width, font_height) = font.getsize(text)
			draw.text((self.WIDTH // 2 - font_width // 2, 40), text, font=font, fill=(255, 255, 255))
		else:
			font = ImageFont.truetype("trebuc.ttf", 55)
			text = str(in_data['GrillTemp'])[:5]
			(font_width, font_height) = font.getsize(text)
			draw.text((self.WIDTH // 2 - font_width // 2, 56), text, font=font, fill=(255, 255, 255))

		# Draw Grill Temp Scale Label
		text = "°" + self.units
		font = ImageFont.truetype("trebuc.ttf", 24)
		(font_width, font_height) = font.getsize(text)
		draw.text((self.WIDTH // 2 - font_width // 2, self.HEIGHT // 2 - font_height // 2 + 10), text, font=font,
					fill=(255, 255, 255))

		# PROBE1 Temp Circle
		draw.ellipse((10, self.HEIGHT // 2 + 10, 110, self.HEIGHT // 2 + 110), fill=(50, 50, 50))
		if in_data['Probe1Temp'] < 0:
			endpoint = 0
		elif self.units == 'F':
			endpoint = ((360 * in_data['Probe1Temp']) // 300) + 90
		else:
			endpoint = ((360 * in_data['Probe1Temp']) // 150) + 90
		draw.pieslice((10, self.HEIGHT // 2 + 10, 110, self.HEIGHT // 2 + 110), start=90, end=endpoint,
						fill=(3, 161, 252))
		if (in_data['Probe1SetPoint'] > 0):
			if self.units == 'F':
				setpoint = ((360 * in_data['Probe1SetPoint']) // 300) + 90
			else:
				setpoint = ((360 * in_data['Probe1SetPoint']) // 150) + 90
			draw.pieslice((10, self.HEIGHT // 2 + 10, 110, self.HEIGHT // 2 + 110), start=setpoint - 2,
							end=setpoint + 2, fill=(255, 255, 0))  # Yellow Arc for SetPoint
		draw.ellipse((20, self.HEIGHT // 2 + 20, 100, self.HEIGHT // 2 + 100), fill=(0, 0, 0))

		# PROBE1 Temp Label
		font = ImageFont.truetype("trebuc.ttf", 16)
		text = "Probe-1"
		(font_width, font_height) = font.getsize(text)
		draw.text((60 - font_width // 2, self.HEIGHT // 2 + 40 - font_height // 2), text, font=font,
					fill=(255, 255, 255))

		# PROBE1 Temperature (Large Centered)
		if (self.units == 'F'):
			font = ImageFont.truetype("trebuc.ttf", 36)
		else:
			font = ImageFont.truetype("trebuc.ttf", 30)
		text = str(in_data['Probe1Temp'])[:5]
		(font_width, font_height) = font.getsize(text)
		draw.text((60 - font_width // 2, self.HEIGHT // 2 + 60 - font_height // 2), text, font=font,
					fill=(255, 255, 255))

		# PROBE1 Set Point (Small Centered Bottom)
		if (in_data['Probe1SetPoint'] > 0):
			font = ImageFont.truetype("trebuc.ttf", 16)
			text = ">" + str(in_data['Probe1SetPoint'])[:5] + "<"
			(font_width, font_height) = font.getsize(text)
			draw.text((60 - font_width // 2, self.HEIGHT // 2 + 85 - font_height // 2), text, font=font,
						fill=(0, 200, 255))

		# PROBE2 Temp Circle
		draw.ellipse((self.WIDTH - 110, self.HEIGHT // 2 + 10, self.WIDTH - 10, self.HEIGHT // 2 + 110),
						fill=(50, 50, 50))
		if in_data['Probe2Temp'] < 0:
			endpoint = 0
		elif self.units == 'F':
			endpoint = ((360 * in_data['Probe2Temp']) // 300) + 90
		else:
			endpoint = ((360 * in_data['Probe2Temp']) // 150) + 90
		draw.pieslice((self.WIDTH - 110, self.HEIGHT // 2 + 10, self.WIDTH - 10, self.HEIGHT // 2 + 110), start=90,
						end=endpoint, fill=(3, 161, 252))
		if (in_data['Probe2SetPoint'] > 0):
			if self.units == 'F':
				setpoint = ((360 * in_data['Probe2SetPoint']) // 300) + 90
			else:
				setpoint = ((360 * in_data['Probe2SetPoint']) // 150) + 90
			draw.pieslice((self.WIDTH - 110, self.HEIGHT // 2 + 10, self.WIDTH - 10, self.HEIGHT // 2 + 110),
							start=setpoint - 2, end=setpoint + 2, fill=(255, 255, 0))  # Yellow Arc for SetPoint
		draw.ellipse((self.WIDTH - 100, self.HEIGHT // 2 + 20, self.WIDTH - 20, self.HEIGHT // 2 + 100),
						fill=(0, 0, 0))

		# PROBE2 Temp Label
		font = ImageFont.truetype("trebuc.ttf", 16)
		text = "Probe-2"
		(font_width, font_height) = font.getsize(text)
		draw.text((self.WIDTH - 60 - font_width // 2, self.HEIGHT // 2 + 40 - font_height // 2), text, font=font,
					fill=(255, 255, 255))

		# PROBE2 Temperature (Large Centered)
		if (self.units == 'F'):
			font = ImageFont.truetype("trebuc.ttf", 36)
		else:
			font = ImageFont.truetype("trebuc.ttf", 30)
		text = str(in_data['Probe2Temp'])[:5]
		(font_width, font_height) = font.getsize(text)
		draw.text((self.WIDTH - 60 - font_width // 2, self.HEIGHT // 2 + 60 - font_height // 2), text, font=font,
					fill=(255, 255, 255))

		# PROBE2 Set Point (Small Centered Bottom)
		if (in_data['Probe2SetPoint'] > 0):
			font = ImageFont.truetype("trebuc.ttf", 16)
			text = ">" + str(in_data['Probe2SetPoint'])[:5] + "<"
			(font_width, font_height) = font.getsize(text)
			draw.text((self.WIDTH - 60 - font_width // 2, self.HEIGHT // 2 + 85 - font_height // 2), text,
						font=font, fill=(0, 200, 255))

		# Active Outputs
		''' Test of pulsing color '''
		if self.inc_pulse_color == True: 
			if self.icon_color < 200:
				self.icon_color += 20
			else: 
				self.inc_pulse_color = False 
				self.icon_color -= 20 
		else:
			if self.icon_color < 100:
				self.inc_pulse_color = True
				self.icon_color += 20 
			else: 
				self.icon_color -= 20 

		font = ImageFont.truetype("FA-Free-Solid.otf", 36)
		if (status_data['outpins']['fan'] == 0):
			# F = Fan (Upper Left), 40x40, origin 10,10
			self._draw_fan_icon(img)
			self.fan_rotation += 30 
			if self.fan_rotation >= 360: 
				self.fan_rotation = 0
		if (status_data['outpins']['igniter'] == 0):
			# I = Igniter(Center Right)
			text = '\uf46a'
			(font_width, font_height) = font.getsize(text)
			draw = self._rounded_rectangle(draw, (
				7 * (self.WIDTH // 8) - 22, self.HEIGHT // 2.5 - 22, 7 * (self.WIDTH // 8) + 22,
					self.HEIGHT // 2.5 + 22), 5, (255, self.icon_color, 0))
			draw = self._rounded_rectangle(draw, (
				7 * (self.WIDTH // 8) - 20, self.HEIGHT // 2.5 - 20, 7 * (self.WIDTH // 8) + 20,
				self.HEIGHT // 2.5 + 20), 5, (0, 0, 0))
			draw.text((7 * (self.WIDTH // 8) - font_width // 2, self.HEIGHT // 2.5 - font_height // 2), text,
						  font=font, fill=(255, self.icon_color, 0))
		if (status_data['outpins']['auger'] == 0):
			# A = Auger (Center Left)
			self._draw_auger_icon(img)
			self.auger_step += 1 
			if self.auger_step >= 3: 
				self.auger_step = 0

		# Notification Indicator (Right)
		show_notify_indicator = False
		for item in status_data['notify_req']:
			if status_data['notify_req'][item] == True:
				show_notify_indicator = True
		if (show_notify_indicator == True):
			font = ImageFont.truetype("FA-Free-Solid.otf", 36)
			text = '\uf0f3'
			(font_width, font_height) = font.getsize(text)
			draw = self._rounded_rectangle(draw, (
				7 * (self.WIDTH // 8) - 22, self.HEIGHT // 6 - 22, 7 * (self.WIDTH // 8) + 22,
				self.HEIGHT // 6 + 22),
											5, (255, 255, 0))
			draw = self._rounded_rectangle(draw, (
				7 * (self.WIDTH // 8) - 20, self.HEIGHT // 6 - 20, 7 * (self.WIDTH // 8) + 20,
				self.HEIGHT // 6 + 20),
											5, (0, 0, 0))
			draw.text((7 * (self.WIDTH // 8) - font_width // 2 + 1, self.HEIGHT // 6 - font_height // 2), text,
						font=font, fill=(255, 255, 0))

		# Smoke Plus Inidicator
		if (status_data['s_plus'] == True) and (
				(status_data['mode'] == 'Smoke') or (status_data['mode'] == 'Hold')):
			draw = self._rounded_rectangle(draw, (
				7 * (self.WIDTH // 8) - 22, self.HEIGHT // 2.5 - 22, 7 * (self.WIDTH // 8) + 22,
				self.HEIGHT // 2.5 + 22), 5, (150, 0, 255))
			draw = self._rounded_rectangle(draw, (
				7 * (self.WIDTH // 8) - 20, self.HEIGHT // 2.5 - 20, 7 * (self.WIDTH // 8) + 20,
				self.HEIGHT // 2.5 + 20), 5, (0, 0, 0))
			font = ImageFont.truetype("FA-Free-Solid.otf", 32)
			text = '\uf0c2'  # FontAwesome Icon for Cloud (Smoke)
			(font_width, font_height) = font.getsize(text)
			draw.text((7 * (self.WIDTH // 8) - font_width // 2, self.HEIGHT // 2.5 - font_height // 2), text,
						font=font, fill=(100, 0, 255))
			font = ImageFont.truetype("FA-Free-Solid.otf", 24)
			text = '\uf067'  # FontAwesome Icon for PLUS
			(font_width, font_height) = font.getsize(text)
			draw.text((7 * (self.WIDTH // 8) - font_width // 2, self.HEIGHT // 2.5 - font_height // 2 + 3), text,
						font=font, fill=(0, 0, 0))

		# Grill Hopper Level (Lower Center)
		font = ImageFont.truetype("trebuc.ttf", 16)
		text = "Hopper:" + str(status_data['hopper_level']) + "%"
		(font_width, font_height) = font.getsize(text)
		if (status_data['hopper_level'] > 70):
			hopper_color = (0, 255, 0)
		elif (status_data['hopper_level'] > 30):
			hopper_color = (255, 150, 0)
		else:
			hopper_color = (255, 0, 0)
		draw = self._rounded_rectangle(draw, (
			self.WIDTH // 2 - font_width // 2 - 7, 156 - font_height // 2, self.WIDTH // 2 + font_width // 2 + 7,
			166 + font_height // 2), 5, hopper_color)
		draw = self._rounded_rectangle(draw, (
			self.WIDTH // 2 - font_width // 2 - 5, 158 - font_height // 2, self.WIDTH // 2 + font_width // 2 + 5,
			164 + font_height // 2), 5, (0, 0, 0))
		draw.text((self.WIDTH // 2 - font_width // 2, 160 - font_height // 2), text, font=font, fill=hopper_color)

		# Current Mode (Bottom Center)
		font = ImageFont.truetype("trebuc.ttf", 36)
		text = status_data['mode']  # + ' Mode'
		(font_width, font_height) = font.getsize(text)
		draw = self._rounded_rectangle(draw, (
			self.WIDTH // 2 - font_width // 2 - 7, self.HEIGHT - font_height - 2,
			self.WIDTH // 2 + font_width // 2 + 7,
			self.HEIGHT - 2), 5, (3, 161, 252))
		draw = self._rounded_rectangle(draw, (
			self.WIDTH // 2 - font_width // 2 - 5, self.HEIGHT - font_height, self.WIDTH // 2 + font_width // 2 + 5,
			self.HEIGHT - 4), 5, (255, 255, 255))
		draw.text((self.WIDTH // 2 - font_width // 2, self.HEIGHT - font_height - 6), text, font=font,
					fill=(0, 0, 0))

		self._display_canvas(img)

	'''
	================ Externally Available Methods ================
	'''

	def display_status(self, in_data, status_data):
		'''
		- Updates the current data for the display loop, if in a work mode 
		'''
		self.units = status_data['units']
		self.displayactive = True
		self.in_data = in_data 
		self.status_data = status_data 

	def display_splash(self):
		''' 
		- Calls Splash Screen 
		'''
		self.displaycommand = 'splash'

	def clear_display(self):
		''' 
		- Clear display and turn off backlight 
		'''
		self.displaycommand = 'clear'

	def display_text(self, text):
		''' 
		- Display some text 
		'''
		self.displaycommand = 'text'
		self.displaydata = text

	def display_network(self):
		''' 
		- Display Network IP QR Code 
		'''
		self.displaycommand = 'network'
