""" The module that is responsible for rendering some things the settings menu """
import traceback
import urwid

from log import logger
from render.loop import loop_container
from render.render import render
RenderClass = render

from widgets.main_widgets import widgets

from control.exit import exit_with_exception, traceback

from settings.settings_processor import settings
from settings_menu.variables import settings_menu_variables
from settings_menu.sections import settings_sections

def update_checkboxes():
	"""
	!LEGACY!: update the checkboxes so that their status is not a lie
	"""
	if settings_menu_variables.settings_show is True:
		sett.update()

def gen_SimpleFocusListWalker_with_footer(contents, footer, width=20):
	"""
	Some analogue of urwid.Frame, it contains a body (contents) and footer,
	but at the same time we CAN switch the focus between them
	"""
	# Count body (contents) rows
	contents_rows = 0
	for i in contents:
		contents_rows = contents_rows + i.rows((width,))

	# Count footer rows
	footer_rows = 0
	for i in footer:
		footer_rows = footer_rows + i.rows((width,))

	filler_height = RenderClass.height - contents_rows - footer_rows
	filler_list = []

	# Filling the empty space between widgets using a urwid.Divider
	for i in range(0, filler_height):
		filler_list.append(urwid.Divider())
	return urwid.Pile(contents + filler_list + footer)

class SettingsRenderClass:
	""" The class that is responsible for rendering the settings menu """
	def __init__(self):
		self.exit_settings_button = urwid.Button("Exit from settings", on_press=settings.show_settings_call)
		self.save_settings_button = urwid.Button("Save to config file", on_press=settings.save)
		self.load_settings_button = urwid.Button("Load from config file", on_press=settings.load)

		self.footer_widget = urwid.Pile([
			widgets.error_widget,
			urwid.Text("- - -"),
			widgets.log_widget,
		])

		# - =
		# just placeholders. nevermind
		self.columns = None
		self.right_widget = None
		# - =

		# - = - Section buttons mapping - = - = - = - = - = - = -
		self.connected_sections = settings_sections.settings_sections

		self.section_buttons = [
				urwid.AttrMap(urwid.Text(" - = Categories = -"), "green_background", ""),
				]

		for i in self.connected_sections:
			self.section_buttons.append(
				urwid.AttrMap(
					urwid.Button(i.name, on_press=self.set_right_section, user_data=i),
					"", "reversed"
				)
			)
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - =

		self.left_widget_sflw = gen_SimpleFocusListWalker_with_footer(
			self.section_buttons,
			[
				urwid.AttrMap(self.load_settings_button, "cyan", "reversed"),
				urwid.AttrMap(self.save_settings_button, "cyan", "reversed"),
				urwid.Divider(),
				urwid.AttrMap(self.exit_settings_button, "light_cyan", "cyan_background"),
			]
			)

		self.left_widget = urwid.Filler(self.left_widget_sflw, valign="top")

		self.vertical_divider = urwid.Filler(urwid.Text(" " * 100))
		self.set_right_section(None, self.connected_sections[0], update=False)

	def set_right_section(self, _, section, update=True):
		""" A function that puts the specified section class on the right visible part of the interface """
		self.current_section = section
		if update:
			self.update()

	def soft_update(self):
		""" Update current section flags states without re-rendering it """
		try:
			self.current_section_initialized.update()
		except AttributeError:
			logger.debug("soft_update unsucceful because SettingsRenderClass doesn't have initialized settings section")

	def update(self):
		""" re-generate + re-render right visible part of the interface """
		self.current_section_initialized = self.current_section()
		self.right_widget = urwid.Frame(
			urwid.Padding(urwid.Filler(self.current_section_initialized.get(), valign='top'), left=2, right=2, align='center'),

			footer = urwid.Pile([
				urwid.LineBox(
					self.footer_widget,
					tlcorner='╭', trcorner='╮', # Rounding corners
					blcorner='', bline='', brcorner='' # Remove bottom line
					),
				]),

			header = urwid.AttrMap(urwid.Text(" - = " + self.current_section.name), "reversed", "") )

		# Create Columns for split screen
		self.columns = urwid.Columns(
			[
			# ALL INCOMING WIDGETS MUST BE BOX
			("fixed", 20, self.left_widget),
			("fixed", 1, self.vertical_divider),
			#("fixed", 1, urwid.AttrMap(self.vertical_divider, "reversed")),
			self.right_widget
			])

		loop_container.loop.widget = self.columns

	def tick_handler_settings(self, _, _1):
		""" Same as tick_handler, but responsible only for settings menu """
		if settings_menu_variables.settings_show is True:
			lol = sett.left_widget_sflw.focus_position - 1 # -1 because header is widget too
			if not lol > len(self.connected_sections)-1: # prevent crash on bottom buttons selection, -1 because len makes +1
				if self.current_section != self.connected_sections[lol]:
					self.set_right_section(None, self.connected_sections[lol])

		# - = - = - = - = - = - = - = - = -
		# Settings page show handler
		if settings_menu_variables.settings_show is True and settings_menu_variables.settings_showed is False:
			try:
				# - = - = -
				# Return to default position
				self.left_widget_sflw.set_focus(1)
				self.set_right_section(None, self.connected_sections[0], update=False)
				# - = - = -
				self.update()
				settings_menu_variables.settings_showed = True
			except:
				exit_with_exception(traceback.format_exc())
		if settings_menu_variables.settings_show is False and settings_menu_variables.settings_showed is True:
			try:
				loop_container.loop.widget = widgets.main_widget
				settings_menu_variables.settings_showed = False
			except:
				exit_with_exception(traceback.format_exc())
		# - = - = - = - = - = - = - = - = -

		# - = - = - = - = - = - = - = - = -
		# Soft checkbox updater
		if settings_menu_variables.settings_soft_update_scheduled is True:
			self.soft_update()
			settings_menu_variables.settings_soft_update_scheduled = False
		# - = - = - = - = - = - = - = - = -

		loop_container.loop.set_alarm_in(0.1, self.tick_handler_settings)

sett = SettingsRenderClass()
