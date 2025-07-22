""" Responsible for control, registering and importing dynamic modules  """
import os
import sys

import pprint
import urwid

from log import logger, journal

from render.colors import colors
# from settings_menu import sections
from settings.settings_processor import settings # for switches

class Dynamic:
	""" Responsible for control and registering dynamic modules  """
	def __init__(self):
		self.settings_map = []
		logger.debug("Dynamic modules class initiated!")

	def register(self, module):
		""" Registers dynamic module in json object """
		logger.debug("[plugins] loading: %s", module.savename)
		self.settings_map.append(module)
		# self.settings_map[module.savename] = {
			# "title": module.title,
			# "description": module.description,
			# "section": module.section,

			# "savename": module.savename,

			# "widget_type": module.widget_type,
			# "if_enabled": module.if_enabled,
			# # "if_disabled": module.if_disabled,
			# }

		# - = - = - = - = - = -
		# Add to settings_processor, for saving ability
		settings.write_setting(module.savename, False)
		# - = - = - = - = - = -

		logger.debug(pprint.pformat(self.settings_map))
		journal.info("[YTCON][plugins] Loaded: " + module.savename)

dynamic_modules = Dynamic()

class DynamicParser:
	name = "Dynamic"
	def __init__(self):
		self.settings_pile_list = [urwid.Divider()]
		#self.sections_hierarchy = {}

	def get(self):
		""" Get content of section """
		for i in dynamic_modules.settings_map:
			widget = urwid.CheckBox([(colors.cyan, i.title), "\n"+i.description], on_state_change=settings.setting_switch, user_data=i.savename)
			# i.widget = widget
			self.settings_pile_list.append(widget)
			self.settings_pile_list.append(urwid.Divider())

		# UPDATE CHECKBOXES
		self.update()

		settings_pile = urwid.Pile(self.settings_pile_list)
		return settings_pile

	def update(self):
		""" Update checkbox states for they don't lie """
		for widget in self.settings_pile_list:
			if isinstance(widget, urwid.CheckBox):
				# get user_data from button class
				# Pylint disabled because there is no normal way to get user_data
				user_data = widget._urwid_signals["change"][0][2] # pylint: disable=protected-access
				widget.set_state(settings.get_setting(user_data), do_callback=False) # update state

class DynamicOpts:
	def __init__(self):
		pass

	def get(self):
		ydl_opts_from_plugins = {}

		for plugin in dynamic_modules.settings_map:
			if settings.get_setting(plugin.savename) is True:
				if next(iter(plugin.if_enabled)) not in	ydl_opts_from_plugins: # get first keys to check duplicates
					ydl_opts_from_plugins = ydl_opts_from_plugins | plugin.if_enabled
				else:
					journal.error(f"[YTCON] PLUGIN CONFLICT FOUND: SOME PLUGIN ALREADY USES {next(iter(plugin.if_enabled))}. One of the conflict plugins: {plugin.savename}. It will not be activated.")

		logger.debug("DynamicOpts:")
		logger.debug(ydl_opts_from_plugins)

		return ydl_opts_from_plugins

dynamic_ytdl_options = DynamicOpts()

# - = - = - = - = - = - = - = - = - = - = - = -
# Unstead of "from plugins import *"
sys.path.append(os.path.dirname(__file__) + "/plugins")

for module in os.listdir(os.path.dirname(__file__) + "/plugins"):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    __import__(module[:-3])
# - = - = - = - = - = - = - = - = - = - = - = -

# sections.settings_sections.settings_sections.append(DynamicParser())
#section = DynamicParser
