import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -
from render.colors import colors

class MainClass():
	# https://github.com/yt-dlp/yt-dlp/issues/4914
	title = "Do not abort download on error"
	description = ((colors.light_red, "<!!> Dangerous option - can make ytcon a little unstable (untested)\nPlease use only if necessary <!!>"),
					"\nUse this so as not to interrupt the download if\none of the video in the playlist is not available")
	section = "Playlists"

	savename = "yt-dlp.ignoreerrors"

	widget_type = "checkbox"

	if_enabled = {"ignoreerrors": "only_download"}
	if_enabled_type = "json_insert"
	# if_disabled = None

# - = - = -
dynamic_modules.register(MainClass)
