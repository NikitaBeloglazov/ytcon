import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, YtdlOptsInjectModeType
# - = - = -

class MainClass(PluginBase):
	title = "User-Agent"
	description = "Overwrite the default user-agent provided by yt-dlp.\nWhen using сookies from browser, it would be nice to use the same User-Agent as browser"
	section = "Cookies"

	savename = "yt-dlp.user_agent"

	widget_type = WidgetType.INPUT_FIELD

	ydl_opts = ("http_headers", "User-Agent") # -> {'http_headers': {'User-Agent': 'test'}}
	ydl_opts_inject_mode = YtdlOptsInjectModeType.CONTENT_IN_NESTED_JSON

	verify_input = VerifyInput.REGEX
	verify_input_data = r"^Mozilla\/[0-9.]+\s+\([^)]+\)\s+.+$" # written with ai so that it can work really bad

# - = - = -
dynamic_modules.register(MainClass)

