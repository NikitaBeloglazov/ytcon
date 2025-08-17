"""
	The module which contains the settings category classes.

	They will be automatically found and placed in a special dynamic list (self.settings_sections)
	that will be shown to the user
"""

# TODO: Please consider rewrite to dynamic plug-ins system
import urwid

from log import logger
# from control.variables import variables
from render.colors import colors

from render.render import render
RenderClass = render

from settings.settings_processor import settings

from settings_plugins import get_all_sections

from app_update import settings_section

class SettingsSections:
	"""
	The module which contains the settings category classes.

	They will be automatically found and placed in a special dynamic list (self.settings_sections)
	that will be shown to the user
	"""
	def __init__(self):
		# Get all class attributes (sections)
		class_attributes = vars(SettingsSections)

		# Filter only classes
		self.settings_sections = [cls for cls in class_attributes.values() if isinstance(cls, type)]
		self.settings_sections.append(settings_section.Update_Status_SECTION)
		self.settings_sections.append(settings_section.Update_Settings_SECTION)
		self.settings_sections.extend(get_all_sections())

		logger.debug(self.settings_sections)

	class Appearance_SECTION: # pylint: disable=attribute-defined-outside-init # because get() initializes a class
		""" settings section related to appearance """
		name = "Appearance"
		def get(self):
			""" Get content of section """
			self.settings_checkbox_progresstype_detailed = urwid.CheckBox([
				(colors.cyan, "46% |███▍   | - Detailed"),
				"\nUse some unicode characters (▏;▍;▋;▉;█)\nto display the percentage more accurately.\nDoesn't fully work in tty",
				], on_state_change=settings.setting_change_content, user_data=("progressbar_appearance", "detailed"))
			self.settings_checkbox_progresstype_simple = urwid.CheckBox([
				(colors.cyan, "46% |████   | - Simple"),
				"\nUse only ACSII squares (█) to show percentage"
				], on_state_change=settings.setting_change_content, user_data=("progressbar_appearance", "simple"))
			self.settings_checkbox_progresstype_arrow = urwid.CheckBox([
				(colors.cyan, "46% |===>   | - Arrow"),
				"\nLet's just add some oldfag style 😎"
				], on_state_change=settings.setting_change_content, user_data=("progressbar_appearance", "arrow"))
			self.settings_checkbox_progresstype_pacman = urwid.CheckBox([
				(colors.cyan, "46% |--C o | - Pacman"),
				"\nPacman game"
				], on_state_change=settings.setting_change_content, user_data=("progressbar_appearance", "pacman"))

			# UPDATE CHECKBOXES
			self.update()

			settings_pile = urwid.Pile([
				urwid.Divider(),
				urwid.Text((colors.light_yellow, "Progress bar type")),
				urwid.Divider(),
				self.settings_checkbox_progresstype_detailed,
				urwid.Divider(),
				self.settings_checkbox_progresstype_simple,
				urwid.Divider(),
				self.settings_checkbox_progresstype_arrow,
				urwid.Divider(),
				self.settings_checkbox_progresstype_pacman,
				urwid.Divider(),
				])

			return settings_pile

		def update(self):
			""" Update checkbox states for they don't lie """
			self.settings_checkbox_progresstype_detailed.set_state(settings.get_setting("progressbar_appearance") == "detailed", do_callback=False)
			self.settings_checkbox_progresstype_simple.set_state(settings.get_setting("progressbar_appearance") == "simple", do_callback=False)
			self.settings_checkbox_progresstype_arrow.set_state(settings.get_setting("progressbar_appearance") == "arrow", do_callback=False)
			self.settings_checkbox_progresstype_pacman.set_state(settings.get_setting("progressbar_appearance") == "pacman", do_callback=False)

	# = - E X A M P L E - =
	#class Three_SECTION:
	#	# Test section
	#	name = "3"
	#	def get(self):
	#		# Get content of section
	#		return urwid.Text('helo3')

settings_sections = SettingsSections()
