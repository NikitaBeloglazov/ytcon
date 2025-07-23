import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	title = "Extract cookies from browser"
	description = "Use cookies from the browser you specified.\nChromium-based and Firefox are supported. Write with a lowercase letter"
	section = "Cookies"

	savename = "yt-dlp.cookiesfrombrowser"

	widget_type = "input_field"

	if_enabled = "cookiesfrombrowser"
	# if_disabled = None

# - = - = -
dynamic_modules.register(MainClass)

