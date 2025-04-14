""" Stores most widgets, which are located on ytcon's main screen """
import urwid
from log import logger
from control.control import ControlClass
from settings.settings_processor import settings
from widgets.input_handler import InputHandler
from widgets.top_pile import widgets_tp

from render.static_methods import render_static
from render.colors import colors

class Widgets:
	""" It stores main widgets inside it. """
	def __init__(self):
		self.log_widget = urwid.Text("Initializing, please wait")
		self.error_widget = urwid.Text("Initializing, please wait")
		self.input_widget = InputHandler.InputBox("Enter URL > ")

		self.main_settings_button = urwid.Button("Settings", on_press=settings.show_settings_call)
		self.main_clear_button = urwid.Button("Clear", on_press=self.main_clear_button_ON_PRESS)
		self.main_footer_clipboard_autopaste_button = urwid.Button("Autopaste", on_press=settings.clipboard_autopaste_switch)

		self.main_footer_buttons = urwid.GridFlow(
			[self.main_settings_button, self.main_clear_button, self.main_footer_clipboard_autopaste_button],
			cell_width=13, h_sep=2, v_sep=1, align="left")
		logger.debug(self.main_footer_buttons.contents)
		self.main_footer_buttons_with_attrmap = urwid.AttrMap(self.main_footer_buttons, "buttons_footer")

		self.bottom_separator = urwid.Text("- - -")

		self.main_footer = urwid.Pile(
				[
				self.error_widget,
				urwid.Text("- - -"),
				self.log_widget,
				urwid.Text("- - -"),
				self.input_widget,
				urwid.Divider(),
				self.bottom_separator,
				self.main_footer_buttons_with_attrmap,
				])
		self.main_widget = urwid.Frame(
			urwid.Filler(widgets_tp.top_pile, "top"),
			footer=self.main_footer,
			focus_part='footer')

	def main_clear_button_ON_PRESS(self, _=None): # TODO: ?
		""" Funcion that called by < Clear > button press """
		ControlClass.clear()
		render_static.flash_button_text(self.main_clear_button, colors.light_yellow, 2)

widgets = Widgets()
