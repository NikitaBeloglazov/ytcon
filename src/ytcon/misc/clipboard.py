""" The module that is responsible for the operation of the clipboard in ytcon """
import re
import sys
import time
import threading

import clipman

from log import journal, logger

from control.variables import variables
from control.exit import exit_with_exception, traceback

from settings.settings_processor import settings
from settings_menu.render import update_checkboxes

from downloader.main import downloader
#from render.loop import loop_container

# TODO: INIT NEEDS REWRITING.
# - also, separate control class for clipboard,
#   not variables.clipboard_checker_state_launched

# 	↓ shit
def clipboard_init():
	""" Initializes clipman in ytcon boot stage. If ytcon already booted, it clipman inits in clipboard_checker() """
	try:
		clipman.init()
	except Exception as e: # pylint: disable=broad-except
		logger.info(traceback.format_exc())
		print("[!!] An clipboard error occurred!\n")
		print(f"- {type(e).__name__}: {e}")
		print("\nYou can follow instructions in this error message, or ignore it")
		print("BUT, if you ignore it, clipboard auto-paste will be unavalible.\n")
		print("Also, if this error message doesn't contain instructions,")
		print("and does not contain any understandable text for your human language, please make an issue")
		print("https://github.com/NikitaBeloglazov/clipman/issues/new")
		print("Full traceback can be found in info.log\n")

		try:
			user_answer = input("Ignore it? [y/N] > ")
		except KeyboardInterrupt:
			print("Exiting..")
			sys.exit(1)

		if user_answer.lower() in ("yes", "y"):
			journal.error("[YTCON] If you don't want answer \"yes\" every time, solve the problem, or disable auto-paste in settings and PRESS \"Save to config file\"")
			settings.write_setting("clipboard_autopaste", False)
		else:
			print("Exiting..")
			sys.exit(1)

url_regex = r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$"
def clipboard_checker():
	"""
	Checks the clipboard for new entries against old ones.
	If it sees new content on the clipboard, it will check whether this is a site, if it detects site, download starts
	"""

	# Set the button yellow and DO NOT start daemon
	variables.clipboard_checker_state_launched = "Do not start"

	if clipman.dataclass.init_called is False:
		try:
			clipman.init()
		except:
			logger.info(traceback.format_exc())
			journal.error("[YTCON] An error occurred while initializing the clipboard. You can see the error in info.log. Or save the Auto-paste option enabled in the config file, restart ytcon, and after that you will see an error with detailed instructions.")

			# Keep setting ON for "save to config file" ability
			time.sleep(60)
			settings.write_setting("clipboard_autopaste", False)
			update_checkboxes()
			variables.clipboard_checker_state_launched = False
			return None

	try:
		variables.clipboard_checker_state_launched = True
		journal.info("[YTCON] Clipboard auto-paste is ON.")

		old_clip = ""

		while True:
			if settings.get_setting("clipboard_autopaste") is False:
				variables.clipboard_checker_state_launched = False
				journal.info("[YTCON] Clipboard auto-paste turned off.")
				return None

			new_clip = clipman.paste()
			if new_clip != old_clip:
				if re.fullmatch(url_regex, new_clip):
					journal.info("[CLIP] New URL detected: " + new_clip)
					threading.Thread(target=downloader, args=(new_clip,), daemon=True).start()
				else:
					logger.debug("clipboard content: %s", new_clip)
					journal.info("[CLIP] New clipboard content detected. But this is not URL. Ignoring..")
			old_clip = new_clip
			time.sleep(1)
	except:
		exit_with_exception(str(traceback.format_exc()))
		return None
