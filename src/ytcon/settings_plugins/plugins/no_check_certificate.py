import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	# Links to test: https://badssl.com or https://stackoverflow.com/questions/1705198/example-sites-with-broken-security-certs
	title = "Do not check website certificates"
	description = "Ignore SSL errors like \"SSL: CERTIFICATE_VERIFY_FAILED\".\nUseful for some broken sites"
	section = "Fetching"

	savename = "yt-dlp.nocheckcertificate"

	widget_type = "checkbox"

	if_enabled = {"nocheckcertificate": True}
	if_enabled_type = "json_insert"
	# if_disabled = None

# - = - = -
dynamic_modules.register(MainClass)

