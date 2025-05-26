import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	title = "Extract cookies from Chromium"
	description = "give me fucking cookies"
	section = "Cookies"

	savename = "yt-dlp.cookiesfrombrowser"

	widget_type = "checkbox"

	if_enabled = {"cookiesfrombrowser": ('chromium', )}
	# if_disabled = None

# - = - = -
dynamic_modules.register(MainClass)

