import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, IfEnabledType
# - = - = -
from yt_dlp.cookies import SUPPORTED_BROWSERS

class MainClass(PluginBase):
	title = "Extract cookies from browser"
	description = "Use cookies from the browser you specified. Usually needed for sites that require login.\nChromium-based and Firefox are supported. Write with a lowercase letter\nExamples: chromium, firefox, vivaldi"
	section = "Cookies"

	savename = "yt-dlp.cookiesfrombrowser"

	widget_type = WidgetType.INPUT_FIELD

	if_enabled = "cookiesfrombrowser"
	if_enabled_type = IfEnabledType.CONTENT_TUPLE

	verify_input = VerifyInput.COMPARE_WITH_LIST
	verify_input_data = SUPPORTED_BROWSERS # allow only supported browsers by yt-dlp

# - = - = -
dynamic_modules.register(MainClass)

