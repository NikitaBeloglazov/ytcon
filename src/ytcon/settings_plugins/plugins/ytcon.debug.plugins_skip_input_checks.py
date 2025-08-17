import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	""" <YTCON INTERNALS> Allow saving non-allowed values settings or activate options without required dependencies installed """
	title = "Skip input checks for ytcon plugins"
	description = "Allow saving non-allowed values settings or activate options without required dependencies installed.\nPotentially can break ytcon."
	section = "Debug"

	savename = "ytcon.debug.plugins_skip_input_checks"

	widget_type = "checkbox"

	if_enabled = None
	if_enabled_type = "internals"

	verify_input = "ignore"

# - = - = -
dynamic_modules.register(MainClass)
