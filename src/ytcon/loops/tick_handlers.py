"""
	tick_handler just checks some conditions every few seconds and executes them.
	Directly not responsible for rendering, but changes some buttons color
"""

import sys
import time
import threading
import traceback

import urwid

from log import logger

from control.variables import variables

from widgets.main_widgets import widgets
from settings.settings_processor import settings

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

	if variables.auto_update_safe_gui_stop is True: # TODO: looks like is it not working anymore
		logger.debug("auto_update_safe_gui_stop spotted")
		try:
			loop.stop()
		except:
			logger.debug(traceback.format_exc())
		sys.exit()
	# - = - = - = - = - = - = - = - = -

	# Prevent focus from remaining on footer buttons after pressing them
	widgets.main_footer.set_focus(widgets.input_widget)

	# - =
	loop.set_alarm_in(0.3, tick_handler)


# def tick_handler_big_delay(loop, _):
# 	# Same as tick_handler, but with bigger delay. Made for optimization purposes.
#
# 	# - = - = - = - = - = - = - = - = -
# 	# Auto-update has been here
# 	# - = - = - = - = - = - = - = - = -
#
# 	# - =
# 	loop.set_alarm_in(4, tick_handler_big_delay)
#
# loop_container.loop.set_alarm_in(1, tick_handlers.tick_handler_big_delay)
