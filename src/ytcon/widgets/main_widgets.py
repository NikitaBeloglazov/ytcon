import urwid
from log import logger
from control.control import ControlClass
from settings.settings_processor import settings
from widgets.input_handler import InputHandler

class Widgets:
	""" It stores main widgets inside it. """
	def __init__(self):
		self.top_pile = urwid.Pile([])

		#logger.debug(pprint.pformat(top_pile.contents))
		#logger.debug(pprint.pformat(calculate_widget_height(top_pile)))

		self.log_widget = urwid.Text("Initializing, please wait")
		self.error_widget = urwid.Text("Initializing, please wait")
		self.input_widget = InputHandler.InputBox("Enter URL > ")

		self.main_settings_button = urwid.Button("Settings", on_press=settings.show_settings_call)
		self.main_clear_button = urwid.Button("Clear", on_press=ControlClass.clear)
		self.main_footer_clipboard_autopaste_button = urwid.Button("Autopaste", on_press=settings.clipboard_autopaste_switch)

		self.main_footer_buttons = urwid.GridFlow(
			[self.main_settings_button, self.main_clear_button, self.main_footer_clipboard_autopaste_button],
			cell_width=13, h_sep=2, v_sep=1, align="left")
		logger.debug(self.main_footer_buttons.contents)
		self.main_footer_buttons_with_attrmap = urwid.AttrMap(self.main_footer_buttons, "buttons_footer")

		self.auto_update_avalible_text_indicator = urwid.Text("- - -")

		self.main_footer = urwid.Pile(
				[
				self.error_widget,
				urwid.Text("- - -"),
				self.log_widget,
				urwid.Text("- - -"),
				self.input_widget,
				urwid.Divider(),
				self.auto_update_avalible_text_indicator,
				self.main_footer_buttons_with_attrmap,
				])
		self.main_widget = urwid.Frame(
			urwid.Filler(self.top_pile, "top"),
			footer=self.main_footer,
			focus_part='footer')

widgets = Widgets()
