import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, YtdlOptsInjectModeType
# - = - = -

class MainClass(PluginBase):
	""" <YTCON INTERNALS> Allow saving non-allowed values settings or activate options without required dependencies installed """
	title = "Skip input checks for ytcon plugins"
	description = "Allow saving non-allowed values settings or activate options without required dependencies installed.\nPotentially can break ytcon."
	section = "Debug"

	savename = "ytcon.debug.plugins_skip_input_checks"

	widget_type = WidgetType.CHECKBOX

	ydl_opts = None
	ydl_opts_inject_mode = YtdlOptsInjectModeType.NONE

# - = - = -
dynamic_modules.register(MainClass)
