import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
from settings_plugins.types import PluginBase, WidgetType, VerifyInput, YtdlOptsInjectModeType
# - = - = -
from render.colors import colors

class MainClass(PluginBase):
	# https://github.com/yt-dlp/yt-dlp/issues/4914
	title = "Do not abort download on error"
	description = ((colors.light_red, "<!!> Dangerous option - can make ytcon a little unstable (untested)\nPlease use only if necessary <!!>"),
					"\nUse this so as not to interrupt the download if\none of the video in the playlist is not available")
	section = "Playlists"

	savename = "yt-dlp.ignoreerrors"

	widget_type = WidgetType.CHECKBOX

	ydl_opts = {"ignoreerrors": "only_download"}
	ydl_opts_inject_mode = YtdlOptsInjectModeType.JSON_INSERT

# - = - = -
dynamic_modules.register(MainClass)
