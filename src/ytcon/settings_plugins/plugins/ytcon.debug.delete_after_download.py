import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	""" <YTCON INTERNALS> Remove downloaded video/audio/etc from folder after download is complete. Useful for testing. """
	title = "Delete files after download"
	description = "Remove downloaded video/audio/etc from folder after download is complete.\nUseful for testing.\n\nThis means that the downloaded files WILL NOT BE SAVED!"
	section = "Debug"

	savename = "ytcon.debug.delete_after_download"

	widget_type = "checkbox"

	if_enabled = None
	if_enabled_type = "internals"

	verify_input = "ignore"

# - = - = -
dynamic_modules.register(MainClass)
