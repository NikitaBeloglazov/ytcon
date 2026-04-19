import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, IfEnabledType
# - = - = -

class MainClass(PluginBase):
	title = "User-Agent"
	description = "Overwrite the default user-agent provided by yt-dlp.\nWhen using сookies from browser, it would be nice to use the same User-Agent as browser"
	section = "Cookies"

	savename = "yt-dlp.user_agent"

	widget_type = WidgetType.INPUT_FIELD

	if_enabled = ("http_headers", "User-Agent") # -> {'http_headers': {'User-Agent': 'test'}}
	if_enabled_type = IfEnabledType.CONTENT_IN_NESTED_JSON
	# if_disabled = None

	verify_input = VerifyInput.REGEX
	verify_input_data = r"^Mozilla\/[0-9.]+\s+\([^)]+\)\s+.+$" # written with neural network so that it can work really bad

# - = - = -
dynamic_modules.register(MainClass)

