""" This module stores some information about colors and some color presets """
import urwid

class ColorsBase:
	""" Stores some information about colors and some color presets. """
	def __init__(self):
		# Init colors
		self.red = urwid.AttrSpec('dark red', 'default')
		self.light_red = urwid.AttrSpec('light red', 'default')
		self.yellow = urwid.AttrSpec('brown', 'default')
		self.light_yellow = urwid.AttrSpec('yellow', 'default')
		self.green = urwid.AttrSpec('dark green', 'default')
		self.cyan = urwid.AttrSpec('dark cyan', 'default')
		# self.light_white = urwid.AttrSpec('bold', 'default') # unused

		self.custom_palette = [
			# ('name_of_style', 'color_text', 'color_background')
			('reversed', 'standout', ''),
			('buttons_footer', 'light green', ''),
			('light_red', 'light red', ''),
			('yellow', 'yellow', ''),
			('light_green', 'light green', ''),
			('green', 'dark green', ''),
			('cyan', 'dark cyan', ''),
			('light_cyan', 'light cyan', ''),
			('bold_default', 'white', ''),

			('green_background', 'black', 'dark green'),
			('cyan_background',  'black', 'dark cyan'),
		]

colors = ColorsBase()
