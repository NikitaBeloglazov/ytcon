""" Сontains settings data and methods for them """
import os
import sys
import pickle
import traceback
from pathlib import Path

from log import journal, logger
from control.variables import variables
from render.colors import colors
from render.static_methods import render_static
from settings_menu.variables import settings_menu_variables

class SettingsClass:
	""" Сontains settings data and methods for them """
	def __init__(self, configpath):

		# Default settings
		self.settings = {
			"special_mode": False,
			"clipboard_autopaste": True,
			"no_check_certificate": False,
			"ignoreerrors": False,
			"progressbar_appearance": "detailed",
			"check_updates_on_boot": True,
			"show_updates_bottom_sign": True,
			}
		self.configpath = configpath

	class SettingNotFoundError(Exception):
		""" Called if the specified setting is not found (see def get_setting) """

	def show_settings_call(self, _=None):
		""" Settings display state switch, made for urwid.Button(on_press=show_settings_call) """
		settings_menu_variables.settings_show = not settings_menu_variables.settings_show

	def get_setting(self, setting_name):
		""" Get setting, if it not found, calls SettingNotFoundError """
		try:
			return self.settings[setting_name]
		except KeyError as exc:
			raise self.SettingNotFoundError(f"Setting with name \"{setting_name}\" not found. Maybe someone forgot put it in defaults?") from exc

	def write_setting(self, setting_name, setting_content):
		""" Writes the settings to the memory. Made for the possible use of some "hooks" in the future """
		self.settings[setting_name] = setting_content

	def save(self, button=None): # in the second argument urwid puts the button of which the function was called
		""" Uses pickle for saving settings from memory to ~/.config/settings.db"""
		logger.debug(Path(self.configpath).mkdir(parents=True, exist_ok=True)) # Create dirs if they don't already exist
		with open(self.configpath + "settings.db", "wb") as filee:
			pickle.dump(self.settings, filee)
		journal.info(f"[YTCON] {self.configpath}settings.db saved")
		render_static.flash_button_text(button, colors.green)

	def load(self, button=None): # in the second argument urwid puts the button of which the function was called
		""" Uses pickle for loading settings from ~/.config/settings.db to memory """
		try:
			with open(self.configpath + "settings.db", "rb") as filee:
				self.settings.update(pickle.load(filee))
			journal.info(f"[YTCON] {self.configpath}settings.db loaded")
			settings_menu_variables.settings_soft_update_scheduled = True # update checkboxes
			self.update_ydl_opts()
			render_static.flash_button_text(button, colors.green)
		except FileNotFoundError:
			# If file not found
			journal.warning(f"[YTCON] Saved settings load failed: FileNotFoundError: {self.configpath}settings.db")
			render_static.flash_button_text(button, colors.red)
		except EOFError as exc:
			# If save file is corrupted
			logger.debug(traceback.format_exc())
			journal.warning(f"[YTCON] Saved settings load FAILED: EOFError: {exc}: {self.configpath}settings.db")
			journal.error("[YTCON] YOUR SETTINGS FILE IS CORRUPTED. Default settings restored and corrupted save file removed.")
			self.write_setting("clipboard_autopaste", False)
			settings_menu_variables.settings_soft_update_scheduled = True # update checkboxes
			journal.warning("[YTCON] Clipboard autopaste has been turned off for security reasons. You can it enable it in settings")
			logger.debug(os.remove(f"{self.configpath}settings.db"))

	def clipboard_autopaste_switch(self, _=None, _1=None):
		""" Clipboard autopaste switch function for urwid.Button's. FOR BACK COMPABILITY """
		self.setting_switch(None, None, name="clipboard_autopaste")

	def setting_switch(self, _=None, state=None, name=None):
		""" Switches state to negative current state or to state set by state argument. Made for for urwid.Button's """
		if name is None:
			raise TypeError

		if state is None:
			state = not self.get_setting(name)

		journal.info("")
		journal.info(f"[YTCON] {name}: {self.get_setting(name)} -> {state}")
		self.write_setting(name, state)
		self.update_ydl_opts()
		settings_menu_variables.settings_soft_update_scheduled = True

	def setting_change_content(self, _=None, _1=None, data=None):
		"""
		Change content in setting where negative state cannot be determined.
		Made for for urwid.Button's with pre-writed arguments
		"""
		if data is None:
			raise TypeError

		name = data[0]
		set_data = data[1]

		journal.info("")
		journal.info(f"[YTCON] {name}: {self.get_setting(name)} -> {set_data}")
		self.write_setting(name, set_data)
		self.update_ydl_opts()
		settings_menu_variables.settings_soft_update_scheduled = True

	def update_ydl_opts(self):
		""" Updates some setting-related ydl_opts. Maybe something like post-change scripts? """
		#journal.info(pprint.pformat(variables.ydl_opts))
		#journal.info("updated ydl_opts")

		# - = Special mode cookie extractor activator = -
		if settings.get_setting("special_mode") is True and "cookiesfrombrowser" not in variables.ydl_opts:
			variables.ydl_opts["cookiesfrombrowser"] = ('chromium', ) # needed for some sites with login only access. you may need to replace it with the correct one
		elif settings.get_setting("special_mode") is False and "cookiesfrombrowser" in variables.ydl_opts:
			del variables.ydl_opts["cookiesfrombrowser"]
		# - = - = - = - = - = - = - = - = - = - = - = - =

		# - = Certificates ignore activator = -
		if settings.get_setting("no_check_certificate") is True and "nocheckcertificate" not in variables.ydl_opts:
			variables.ydl_opts["nocheckcertificate"] = True
		elif settings.get_setting("no_check_certificate") is False and "nocheckcertificate" in variables.ydl_opts:
			del variables.ydl_opts["nocheckcertificate"]
		# - = - = - = - = - = - = - = - = - = - = - = - =

		# - = Certificates ignore activator = -
		if settings.get_setting("ignoreerrors") is True and "ignoreerrors" not in variables.ydl_opts:
			variables.ydl_opts["ignoreerrors"] = True
		elif settings.get_setting("ignoreerrors") is False and "ignoreerrors" in variables.ydl_opts:
			del variables.ydl_opts["ignoreerrors"]
		# - = - = - = - = - = - = - = - = - = - = - = - =

		#journal.info(pprint.pformat(variables.ydl_opts))

# - - - - - - - - - - - - -
# Save file folder check
if "XDG_CONFIG_HOME" in os.environ:
	configpath = os.path.expanduser(os.environ["XDG_CONFIG_HOME"] + "/ytcon/")
else:
	configpath = os.path.expanduser("~/.config/ytcon/")

try:
	Path(configpath).mkdir(parents=True, exist_ok=True)
	with open(configpath + "write_test", "wb") as filee:
		pass
	os.remove(configpath + "write_test")
except:
	print(traceback.format_exc())
	print("= = =\n[!!] An error was occurred!\n")
	print("Save file folder check failed. Maybe XDG_CONFIG_HOME env or dir permissions broken?")
	print("The following path has problems: " + configpath)
	sys.exit(1)

logger.debug("config path: %s", configpath)
# - = - = - = - = - = - = - = - = - = - = - = - = - = - =
settings = SettingsClass(configpath)
