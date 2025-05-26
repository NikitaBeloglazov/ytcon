""" Responsible for control, registering and importing dynamic modules  """
import os
import sys

import urwid
import pprint

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
			#module_for_iteration = dynamic_modules.settings_map[i]
			self.settings_pile_list.append(urwid.CheckBox( # make checkbox widget
				[(colors.cyan, i.title), "\n"+i.description],  on_state_change=settings.setting_switch, user_data=i.savename)
				)
			self.settings_pile_list.append(urwid.Divider())

		# UPDATE CHECKBOXES
		self.update()

		settings_pile = urwid.Pile(self.settings_pile_list)
		return settings_pile

	def update(self):
		""" Update checkbox states for they don't lie """
		pass
		#for widget in self.settings_pile_list:
		#	if widget.__class__ is urwid.CheckBox: # Check widget is CheckBox
		#		user_data = widget._urwid_signals["change"][0][2] # get user_data from button class
		#		widget.set_state(settings.get_setting(user_data), do_callback=False) # update state

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
