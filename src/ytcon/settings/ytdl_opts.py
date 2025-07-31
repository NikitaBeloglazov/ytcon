"""
Created to simplify the distribution of yt-dlp options (ytdl_opts),
More correct retrieval of settings and their updating by setting status
"""

import copy # For copying in get(self)
import pprint

from downloader.hook import hook
from log import journal, logger

from settings.settings_processor import settings
from settings_plugins import dynamic_ytdl_options

class YtdlOptsStorage:
	"""
	This class stores yt-dlp options and some defs for getting them
	"""
	def __init__(self):
		self.default_ydl_opts = {
			'logger': journal,
			'progress_hooks': [hook],
			'color': 'no_color',
			#'outtmpl': '%(title)s [%(id)s].%(ext)s', # REALIZED IN own file handler
			'socket_timeout': 15,
			'retries': 20,
			'fragment_retries': 40,
			'retry_sleep': 'http,fragment:exp',
			#'download_archive': 'downloaded_videos.txt', # !!! DANGEROUS OPTION !!! # TODO?

			'extractor_args': {'generic': {'impersonate': ['']}}, # TODO
			# cloudflare avoider
			# --extractor-args "generic:impersonate"
			# Requires curl-cffi module, we can check it through yt_dlp.dependencies.curl_cffi is None
			# https://github.com/yt-dlp/yt-dlp#impersonation, pip install "yt-dlp[default,curl-cffi]"

			'skip_unavailable_fragments': False # DO NOT SKIP FRAGMENTS (relevant when loading on Twitter on weak internet) https://github.com/yt-dlp/yt-dlp/issues/6078#issuecomment-2647248422
		}

		# TODO LIST:
		# 'ratelimit': 207200
		#
		# Angry mode
		# 'retries': 999, # You can use float("inf") but this will lead to an endless retries
		# 'fragment_retries': 999,

		# --no-progress
		# https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#format-selection-examples
		# Desktop notifications

		# Replace ignore-errors with https://github.com/yt-dlp/yt-dlp/issues/4914
		# Replace EXISTS status yellow color to dark green(?) https://t.me/ru_openSUSE/248537/509523
		# limit debug.log file size

	def get(self):
		new_opts = copy.deepcopy(self.default_ydl_opts)

		# - = - = - = - = Dynamic plug-ins = - = - = - = -
		dynamic_opts = dynamic_ytdl_options.get()
		duplicates_check = list(set(new_opts) & set(dynamic_opts)) # check for duplicates: list(set(a) & set(a))
		if duplicates_check:
			journal.error(f"[YTCON] PLUGIN CONFLICT FOUND: FOUND DUPLICATES OF FOLLOWING yt-dlp opts: {str(duplicates_check)}. These opts will be OVERWRITTEN. DO NOT USE AS IS.")
		new_opts = new_opts | dynamic_opts
		# - = - = - = - = - = - = - = - = - = - = - = - = -

		logger.debug(pprint.pformat(self.default_ydl_opts))
		logger.debug("updated ydl_opts")
		logger.debug(pprint.pformat(new_opts))

		return new_opts

ytdl_opts = YtdlOptsStorage()
