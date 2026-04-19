import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, IfEnabledType
# - = - = -

class MainClass(PluginBase):
	""" <YTCON INTERNALS> Remove downloaded video/audio/etc from folder after download is complete. Useful for testing. """
	title = "Delete files after download"
	description = "Remove downloaded video/audio/etc from folder after download is complete.\nUseful for testing.\n\nThis means that the downloaded files WILL NOT BE SAVED!"
	section = "Debug"

	savename = "ytcon.debug.delete_after_download"

	widget_type = WidgetType.CHECKBOX

	if_enabled = None
	if_enabled_type = IfEnabledType.NONE

# - = - = -
dynamic_modules.register(MainClass)
