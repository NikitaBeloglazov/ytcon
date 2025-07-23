import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	title = "Do not check website certificates"
	description = "Enable this if \"SSL: CERTIFICATE_VERIFY_FAILED\" error occurs"
	section = "Fetching"

	savename = "yt-dlp.nocheckcertificate"

	widget_type = "checkbox"

	if_enabled = {"nocheckcertificate": True}
	if_enabled_type = "json_insert"
	# if_disabled = None

# - = - = -
dynamic_modules.register(MainClass)

