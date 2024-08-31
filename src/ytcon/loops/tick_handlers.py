"""
	tick_handler just checks some conditions every few seconds and executes them.
	Directly not responsible for rendering, but changes some buttons color
"""

import sys
import time
import threading
import traceback

import urwid

from log import journal

from control.variables import variables

from render.colors import colors

from widgets.main_widgets import widgets
from settings.settings_processor import settings

from app_update import app_updates
from misc.clipboard import clipboard_checker

def tick_handler(loop, _):
	""" It just checks some conditions every few seconds and executes them. Directly not responsible for rendering, but changes some buttons color """

	# - = - = - = - = - = - = - = - = -
	# Autopaste button color changer
	if (settings.get_setting("clipboard_autopaste") is True and variables.clipboard_checker_state_launched is not True) or (settings.get_setting("clipboard_autopaste") is False and variables.clipboard_checker_state_launched is not False):
		widgets.main_footer_buttons.contents[2] = (urwid.AttrMap(widgets.main_footer_clipboard_autopaste_button, "yellow"), widgets.main_footer_buttons.contents[2][1])
		variables.temp["autopaste_button_color"] = "yellow" # some kind of cache

	elif variables.clipboard_checker_state_launched is not True and variables.temp["autopaste_button_color"] != "light_red":
		widgets.main_footer_buttons.contents[2] = (urwid.AttrMap(widgets.main_footer_clipboard_autopaste_button, "light_red"), widgets.main_footer_buttons.contents[2][1])
		variables.temp["autopaste_button_color"] = "light_red" # some kind of cache

	elif variables.clipboard_checker_state_launched is True and variables.temp["autopaste_button_color"] != "buttons_footer":
		widgets.main_footer_buttons.contents[2] = (urwid.AttrMap(widgets.main_footer_clipboard_autopaste_button, "buttons_footer"), widgets.main_footer_buttons.contents[2][1])
		variables.temp["autopaste_button_color"] = "buttons_footer" # some kind of cache
	# - = - = - = - = - = - = - = - = -

	# - = Clipboard thread activator = -
	if settings.get_setting("clipboard_autopaste") and variables.clipboard_checker_state_launched is False:
		threading.Thread(target=clipboard_checker, daemon=True).start()
	# - = - = - = - = - = - = - = - = -

	# - = - = - = - = - = - = - = - = -
	# The error handler, if it sees variables.exit = True,
	# then exits the program commenting this with the text from variables.exception.
	# The parent function of such actions: exit_with_exception()
	if variables.exit is True:
		loop.stop()
		print("An unknown error has occurred!\n")
		time.sleep(0.5)
		print(variables.exception)
		sys.exit(1)

	if variables.auto_update_safe_gui_stop is True:
		try:
			loop.stop()
		except:
			journal.debug(traceback.format_exc())

		try:
			app_updates.update_thread.join()
		except KeyboardInterrupt:
			print(" - Okay, canceled")
		sys.exit()
	# - = - = - = - = - = - = - = - = -

	# Prevent focus from remaining on footer buttons after pressing them
	widgets.main_footer.set_focus(widgets.input_widget)

	# - =
	loop.set_alarm_in(0.3, tick_handler)



def tick_handler_big_delay(loop, _):
	""" Same as tick_handler, but with bigger delay. Made for optimization purposes. """

	# - = - = - = - = - = - = - = - = -
	# Draw version in settings
	app_updates.update_settings_version_text()

	# New-update-avalible notificator
	if app_updates.auto_update_avalible is True:
		widgets.auto_update_avalible_text_indicator.set_text((colors.cyan, f"- - -\nAuto update {app_updates.version} -> {app_updates.pypi_version} is avalible! Write \"update\" to easy update right now!"))
	# - = - = - = - = - = - = - = - = -

	# - =
	loop.set_alarm_in(4, tick_handler_big_delay)
