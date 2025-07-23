import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -
from yt_dlp.cookies import SUPPORTED_BROWSERS

class MainClass():
	title = "Extract cookies from browser"
	description = "Use cookies from the browser you specified.\nChromium-based and Firefox are supported. Write with a lowercase letter"
	section = "Cookies"

	savename = "yt-dlp.cookiesfrombrowser"

	widget_type = "input_field"

	if_enabled = "cookiesfrombrowser"
	if_enabled_type = "content_tuple" # json_insert or content or content_tuple
	# if_disabled = None

	verify_input = "compare_with_list"
	verify_input_data = SUPPORTED_BROWSERS # allow only supported browsers by yt-dlp

# - = - = -
dynamic_modules.register(MainClass)

