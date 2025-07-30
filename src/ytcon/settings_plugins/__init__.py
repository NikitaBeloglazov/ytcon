""" Responsible for control, registering and importing dynamic modules  """
import os
import sys
import re
import importlib.util # for importing py files

import pprint
import urwid

from log import logger, journal

from render.colors import colors
# from settings_menu import sections
from settings.settings_processor import settings, configpath # first for switches, 2nd for importring from saves path

class Dynamic:
	""" Responsible for control and registering dynamic modules  """
	def __init__(self):
		self.settings_map = []
		# self.settings_map_by_savename = {}
		logger.debug("Dynamic modules class initiated!")

	def register(self, module):
		""" Registers dynamic module in json object """
		logger.debug("[plugins] loading: %s", module.savename)
		self.settings_map.append(module)
		# self.settings_map_by_savename[module.savename] = module
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

		# - = - = - = - = - = -
		# Make a widget for module
		self.make_widget(module)
		# - = - = - = - = - = -

		logger.debug(pprint.pformat(self.settings_map))
		journal.info("[YTCON][plugins] Loaded: " + module.savename)

	def make_widget(self, module):
		""" Based on the plugin type, it assembles a widget with the required style and ready-made triggers, and places it in the plugin class """
		if module.widget_type == "checkbox":
			module.widget = urwid.CheckBox([(colors.cyan, module.title), "\n"+module.description], on_state_change=settings.setting_switch_for_plugins, user_data=module)
		elif module.widget_type == "input_field":
			module_note = urwid.Text([(colors.cyan, module.title), "\n"+module.description])
			module.original_widget = DymanicEdit((colors.cyan, " > "), multiline=True)
			#module_bottom = urwid.Text("└─── ── ──  ──  ─  ─  ─")
			module_edit = urwid.AttrMap(urwid.LineBox(module.original_widget), "dark_gray", "")

			# .original_widget.original_widget two times because we using two decorations: urwid.LineBox then urwid.AttrMap
			urwid.connect_signal(module_edit.original_widget.original_widget, "change", dynamic_verifier.edit_field, module)

			module.widget = urwid.Pile((module_note, module_edit))#, module_bottom))
		else:
			raise NotImplementedError(f"[YTCON][PLUGINS] issue with plugin {module.savename}: \"{module.widget_type}\" is a unknown widget type!")

dynamic_modules = Dynamic()

def get_all_sections():
	""" Initializes each section with the corresponding plugins and gives all these sections in one list """
	modules_sorted_by_sections = {}
	ready_sections_list = []

	for i in dynamic_modules.settings_map:
		if i.section not in modules_sorted_by_sections:
			modules_sorted_by_sections[i.section] = []
		modules_sorted_by_sections[i.section].append(i)

	logger.debug("modules_sorted_by_sections:")
	logger.debug(pprint.pformat(modules_sorted_by_sections))

	for section_name, modules_list in modules_sorted_by_sections.items(): # i contains json keys (names of section)
		ready_sections_list.append(DynamicSection(section_name+"*", modules_list))

	logger.debug(pprint.pformat(ready_sections_list))
	return ready_sections_list

class DynamicSection():
	""" Base section class for use in a dynamic system. Takes a bunch of modular settings and builds a separate category with plugins widgets from them """
	def __init__(self, name, modules_list):
		self.name = name
		self.modules_list = modules_list # modules for this section
		self.settings_pile_list = [urwid.Divider()]

		for i in self.modules_list: # work with modules only for this section
			self.settings_pile_list.append(i.widget)
			self.settings_pile_list.append(urwid.Divider())

		self.settings_pile = urwid.Pile(self.settings_pile_list)

	def get(self):
		""" Get content of section """

		# UPDATE CHECKBOXES
		self.update()

		return self.settings_pile

	def update(self):
		""" Update checkbox states for they don't lie """
		for widget in self.settings_pile_list:
			if isinstance(widget, urwid.CheckBox):
				# get user_data from button class
				# Pylint disabled because there is no normal way to get user_data
				user_data = widget._urwid_signals["change"][0][2] # pylint: disable=protected-access # there must be module class result
				if user_data.widget_type == "checkbox":
					widget.set_state(settings.get_setting(user_data.savename), do_callback=False) # update state
			if isinstance(widget, urwid.Pile):
				# possibly, this is a input_field
				original_widget = widget.contents[1][0].original_widget.original_widget # unpacking pile

				# Pylint disabled because there is no normal way to get user_data
				user_data = original_widget._urwid_signals["change"][0][2] # pylint: disable=protected-access # there must be module class result
				if user_data.widget_type == "input_field":
					if settings.get_setting(user_data.savename) is not False:
						user_data.original_widget.edit_text = str(settings.get_setting(user_data.savename))
						user_data.original_widget.set_edit_pos(999) # Spawn cursor at the end and not at the beginning

# - = - = - = - = - = - = - = - = - = - = - = -

class DymanicEdit(urwid.Edit):
	""" A modified urwid.Edit Widget. Made for getting enter/f10 press """
	def keypress(self, size, key):
		""" Overrides a regular class. """
		# journal.info(key)

		if key == 'f10':
			dynamic_verifier.edit_field(None, self.get_edit_text(), self._urwid_signals["change"][0][2], verbose=True, force=True) # pylint: disable=no-member # lying. this is just shitty code
		elif key == "enter":
			dynamic_verifier.edit_field(None, self.get_edit_text(), self._urwid_signals["change"][0][2], verbose=True) # pylint: disable=no-member # lying. this is just shitty code
		else:
			super().keypress(size, key)


# - = - = - = - = - = - = - = - = - = - = - = -

class DynamicVerifier:
	""" Checks widget for right input """
	def __init__(self):
		self.allow_non_matching_values = False

	def edit_field(self, _=None, data=None, module=None, verbose=False, force=False):
		""" Input validator for plugins with module.widget_type == "input_field" """
		if data == "":
			self.edit_field_changecolor(module, colors.cyan)
			if settings.get_setting(module.savename) is not False:
				settings.setting_switch_for_plugins(None, False, module)
			return None

		if force is True:
			journal.info("[YTCON] Forcing value for " + module.savename)
			settings.setting_switch_for_plugins(None, data, module)
			self.edit_field_changecolor(module, colors.yellow)
			return None

		if self.allow_non_matching_values is True or module.verify_input == "ignore":
			settings.setting_switch_for_plugins(None, data, module)
			self.edit_field_changecolor(module, colors.light_green)
			return None

		if module.verify_input == "compare_with_list":
			if data not in module.verify_input_data:
				self.edit_field_changecolor(module, colors.light_red)
				if verbose is True:
					journal.info("")
					journal.warning("[YTCON][!!] " + module.savename + " not saved - input does not match the allowed values.")
					journal.warning("Allowed values can be viewed in the description or in debug.log")
					logger.debug("If you are really sure of what you do, click F10 for forced save.")
					logger.debug("Allowed values: %s", str(module.verify_input_data))
			else:
				settings.setting_switch_for_plugins(None, data, module)
				self.edit_field_changecolor(module, colors.light_green)
			return None

		if module.verify_input == "regex":
			# journal.info(re.match(module.verify_input_data, data))
			if re.match(module.verify_input_data, data) is None:
				self.edit_field_changecolor(module, colors.light_red)
				if verbose is True:
					journal.info("")
					journal.warning("[YTCON][!!] " + module.savename + " not saved - input does not match with the allowing rules (regex).")
					journal.warning("If you are really sure of what you do, click F10 for forced save")
					logger.debug("Regex: %s", str(module.verify_input_data))
			else:
				settings.setting_switch_for_plugins(None, data, module)
				self.edit_field_changecolor(module, colors.light_green)
			return None

		settings.setting_switch_for_plugins(None, data, module)
		return None

	def edit_field_changecolor(self, module, color):
		""" Changes the color of the urwid.Edit caption """
		module.original_widget.set_caption( (color, " > ") )

dynamic_verifier = DynamicVerifier()

def allow_non_matching_values_switch(_, data):
	""" TODO REMAKE DEBUG SECTION TO PLUGINS """
	dynamic_verifier.allow_non_matching_values = data # TODO REMAKE DEBUG SECTION TO PLUGINS

# - = - = - = - = - = - = - = - = - = - = - = -

class DynamicOpts:
	""" Responsible for applying plugin parameters in ytdl options. Used by downloader """
	def __init__(self):
		pass

	def get(self):
		""" Get options provided by active plugins """
		ydl_opts_from_plugins = {}
		logger.debug(dynamic_modules.settings_map)

		for plugin in dynamic_modules.settings_map:
			if settings.get_setting(plugin.savename) is not False:
				if next(iter(plugin.if_enabled)) not in	ydl_opts_from_plugins: # get first keys to check duplicates

					if plugin.if_enabled_type == "json_insert": # for checkboxes
						ydl_opts_from_plugins = ydl_opts_from_plugins | plugin.if_enabled

					# Sets if_enabled in yt-dlp options with contents of ytcon setting
					# content mostly used for edit fields
					elif plugin.if_enabled_type == "content": # mostly for edit fields
						ydl_opts_from_plugins = ydl_opts_from_plugins | {plugin.if_enabled: settings.get_setting(plugin.savename)}
					elif plugin.if_enabled_type == "content_tuple":
						ydl_opts_from_plugins = ydl_opts_from_plugins | {plugin.if_enabled: (settings.get_setting(plugin.savename), )}
					elif plugin.if_enabled_type == "content_in_nested_json":
						# Currently only supports single-level nesting. Maybe there is a way to nest multiple levels, but I'm too lazy.
						if plugin.if_enabled[0] not in ydl_opts_from_plugins:
							ydl_opts_from_plugins[plugin.if_enabled[0]] = {}
						ydl_opts_from_plugins[plugin.if_enabled[0]] = ydl_opts_from_plugins[plugin.if_enabled[0]] | {plugin.if_enabled[-1]: settings.get_setting(plugin.savename)}

				else:
					journal.error(f"[YTCON] PLUGIN CONFLICT FOUND: SOME PLUGIN ALREADY USES {next(iter(plugin.if_enabled))}. One of the conflict plugins: {plugin.savename}. It will not be activated.")

		logger.debug("DynamicOpts:")
		logger.debug(ydl_opts_from_plugins)

		return ydl_opts_from_plugins

dynamic_ytdl_options = DynamicOpts()

# - = - = - = - = - = - = - = - = - = - = - = -
# Import plugins from folders

def import_plugins_from_folder(folder):
	""" Lists folder for .py files and imports them. Done via importlib because sys.path.append is too ridiculous """
	for module in os.listdir(folder):
		# - = - Skip non-valid files - = -
		if module == '__init__.py' or module[-3:] != '.py':
			continue
		# - = - = - = - = - = - = - - = -
		# Making "specification" (stupid name)
		spec = importlib.util.spec_from_file_location(module.removesuffix('.py'), folder + module)

		# Importing and running (+ registering) plugin
		imported_module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(imported_module)

for i in (
	os.path.dirname(__file__) + "/plugins/", # ytcon build-in plugins
	configpath + "/plugins/", # import plugins from saves folder
	):
	import_plugins_from_folder(i)
# - = - = - = - = - = - = - = - = - = - = - = -
