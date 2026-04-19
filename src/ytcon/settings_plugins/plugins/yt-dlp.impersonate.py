import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, YtdlOptsInjectModeType
# - = - = -
from yt_dlp.networking.impersonate import ImpersonateTarget
from yt_dlp.dependencies import curl_cffi

class MainClass(PluginBase):
	# Also --extractor-args "generic:impersonate" can be used
	# https://github.com/yt-dlp/yt-dlp#impersonation, pip install "yt-dlp[default,curl-cffi]"
	title = "Impersonate requests / Cloudflare avoider"
	description = "Use this if error \"HTTP Error 403 caused by Cloudflare anti-bot challenge\" occurs.\nNote that forcing impersonation for all requests may have a detrimental impact on speed and stability of download.\n\nRequires pip3 install \"yt-dlp[default,curl-cffi]\"\nDetails: https://github.com/yt-dlp/yt-dlp#impersonation"

	section = "Cookies"

	savename = "yt-dlp.impersonate"

	widget_type = WidgetType.CHECKBOX

	ydl_opts = {"impersonate": ImpersonateTarget()}
	ydl_opts_inject_mode = YtdlOptsInjectModeType.JSON_INSERT

	verify_input = VerifyInput.EXEC
	# verify_input_data = lambda : curl_cffi is not None

	@staticmethod
	def verify_input_data():
		""" This plugin requires curl-cffi module, we can check it through yt_dlp.dependencies.curl_cffi is None """
		if curl_cffi is not None:
			return True
		return (False, "curl-cffi depency required! pip3 install \"yt-dlp[default,curl-cffi]\"")

# - = - = -
dynamic_modules.register(MainClass)
