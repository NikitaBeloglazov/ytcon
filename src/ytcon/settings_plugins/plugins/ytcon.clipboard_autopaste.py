import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, YtdlOptsInjectModeType
# - = - = -

class MainClass(PluginBase):
	# https://pypi.org/project/clipman/
	title = "Clipboard auto-paste"
	description = "Automatically regularly checks the clipboard, and if link are there,\nstart downloading this link. Also works in the background.\n\nAdditional information about the module and support:\nhttps://pypi.org/project/clipman/"
	section = "Clipboard"

	savename = "ytcon.clipboard_autopaste"
	enabled_by_default = True

	widget_type = WidgetType.CHECKBOX

	ydl_opts = None
	ydl_opts_inject_mode = YtdlOptsInjectModeType.NONE

# - = - = -
dynamic_modules.register(MainClass)
