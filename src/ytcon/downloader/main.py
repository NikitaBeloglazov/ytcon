"""
	The main component of ytcon, this class sets the basic parameters for the video,
	composes the title and starts downloading.

	For each link one thread (exception: playlists)
"""

import os
import re
import pprint
import threading
import yt_dlp

from log import journal, logger

from control.variables import variables
from control.exit import exit_with_exception, traceback

from settings.settings_processor import settings

from downloader.map_variables import map_variables

from render.progressbar_defs import progressbar_defs

def downloader(url, playlist_redirect=False): # pylint: disable=too-many-return-statements
	"""
	The main component of ytcon, this class sets the basic parameters for the video,
	composes the title and starts downloading.

	For each link one thread (exception: playlists)
	"""
	try:
		if url in variables.queue_list:
			if variables.queue_list[url]["status"] not in ("exists", "finished", "error"):
				# TODO: If you run two identical URLs at the same time before they are registered,
				# the elements in variables.queue_list will be overwritten and after this a file error will appear.
				journal.error(f"[YTCON] Video link \"{progressbar_defs.name_shortener(url, 40)}\" is already downloading!")
				return None
			if variables.queue_list[url]["status"] in ("error"):
				journal.error("[YTCON] Resuming download after error is not recommended, except cases when network error happened!")

		with yt_dlp.YoutubeDL(variables.ydl_opts) as ydl:
			# needed for some sites. you may need to replace it with the correct one
			if settings.get_setting("special_mode") is True:
				ydl.params["http_headers"]["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
				# TODO: CONSIDER USING ydl_opts = {'http_headers':   headers, # https://t.me/c/1799440303/59510
				# "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
			# - = - = - = Get downloading formats (yt) and generate filename (global) = -
			infolist = ydl.extract_info(url, download=False)

			# - = - = - log spam filter - = - = - = - =
			if infolist is None: # yt-dlp returns videos with errors as None :|| # TODO?
				journal.warning("ydl.extract_info RETURNED NONE", show=False)
				return None
			if "automatic_captions" in infolist:
				del infolist["automatic_captions"]
			if "formats" in infolist:
				del infolist["formats"]
			if "thumbnails" in infolist:
				del infolist["thumbnails"]
			if "heatmap" in infolist:
				del infolist["heatmap"]
			logger.debug(pprint.pformat(infolist))
			# - = - = - = - = - = - = - = - = - = - = -

			# - Playlists support - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			if "entries" in infolist:
				if playlist_redirect is True:
					journal.error("[YTCON] Playlist in playlist (recursion) detected! Aborting for security reasons.")
					return None

				playlist_entries = [] # collecting playlist entries urls
				for i in infolist["entries"]:
					if i is None: # yt-dlp returns videos with errors as None :||
						continue
					playlist_entries.append(i["webpage_url"]) # collecting playlist entries urls

				playlist_entries = list(dict.fromkeys(playlist_entries)) # REMOVE DUPLICATED URLS

				for i in playlist_entries:
					threading.Thread(target=downloader, args=(i, True,), daemon=True).start()
				return None
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

			# - Name fiter + assemble - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			temp1 = re.sub(r"[^A-Za-z0-9А-Яа-я \-_.,]", "", infolist["title"].replace("&", "and")) # get title, remove all characters except allowed # >"|" -> "｜" yt-dlp, wtf?
			temp1 = " ".join(temp1.removesuffix(" 1").split()) # remove space duplicates and remove 1 in the end because for some reason yt-dlp adds it on its own
			id_in_filename = infolist["id"].removesuffix("-1")
			filename = f'{temp1} [{id_in_filename}].{infolist["ext"]}'

			# Name too long handler (https://github.com/ytdl-org/youtube-dl/issues/29912 and more more more issues)
			if len(filename.encode('utf-8')) > 190:
				# ^^^^^^^^^^^^^^^^^^^^^^^ counting bytes in filename
				logger.debug("ERROR: FILENAME MORE THAN 190 BYTES. SHORTING...")
				while len(filename.encode('utf-8')) > 190:
					temp1 = " ".join(temp1.split()[:-1]) # remove 1 last word
					filename = f'{temp1} [{id_in_filename}].{infolist["ext"]}'
					logger.debug(filename)
					logger.debug(len(filename.encode('utf-8')))
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

			# Check if file exists
			exists = os.path.exists(filename)
			if exists:
				journal.warning(f'[YTCON] FILE "{filename}" EXISTS')

			# - = - = - = Set parameters = -
			multiple_formats = False
			if "requested_formats" in infolist: # and infolist["extractor"] == "youtube" (also happens on twitter)
				multiple_formats = True # P.S. I DON'T KNOW can this be allowed by DEFAULT for any sites, if there are some bugs, please create an issue!!!!

			temp1_index = map_variables.main(multiple_formats, infolist, filename)

			if exists: # TODO move to map_variables.py?
				variables.queue_list[infolist["original_url"]]["status"] = "exists"
				if multiple_formats:
					for i in infolist["requested_formats"]:
						temp1_index = infolist["original_url"] + ":" + i["format_id"]
						variables.queue_list[temp1_index]["status"] = "exists"
						variables.queue_list[temp1_index]["downloaded"] = variables.queue_list[temp1_index]["size"]
						variables.queue_list[temp1_index]["status_short_display"] = "Exist"
						variables.queue_list[temp1_index]["percent"] = "100.0%"
				else:
					variables.queue_list[temp1_index]["downloaded"] = variables.queue_list[temp1_index]["size"]
					variables.queue_list[temp1_index]["status_short_display"] = "Exist"
					variables.queue_list[temp1_index]["percent"] = "100.0%"
			# - = - = - = - = - = - = - = - = - = - = - = - =
			logger.debug(pprint.pformat(variables.queue_list))

			with yt_dlp.YoutubeDL(variables.ydl_opts | {"outtmpl": filename}) as ydl2:
				logger.debug(ydl2.download(url))
				if variables.last_error.find("[Errno 36] File name too long") > -1:
					raise yt_dlp.utils.DownloadError(variables.last_error)
			# - = Mark meta as finished = -
			if "meta_index" in variables.queue_list[infolist["original_url"]]:
				variables.queue_list[infolist["original_url"]]["status"] = "finished"

	except yt_dlp.utils.DownloadError as e:
		journal.error(str(e), show=False)
		map_variables.mark_as_error(url)
		return None
	except:
		exit_with_exception(traceback.format_exc())
		return None

	# - = - = - = [Post-processing] = - = - = - #
	try:
		if variables.queue_list[temp1_index]["status"] == "exists":
			return None # skip post-process if file already exists

		# = - = -
		if variables.queue_list[temp1_index]["status"] != "finished":
			# IF DOWNLOAD THREAD EXITS WITHOUT ERROR (this usually occurs due to the "ignoreerrors" flag)
			logger.debug("DOWNLOAD THREAD EXITED WITHOUT ERROR")
			map_variables.mark_as_error(url)
			return None
		# = - = -

		# Removes Last-modified header. Repeats --no-mtime functionality which is not present in yt-dlp embeded version
		os.utime(variables.queue_list[temp1_index]["file"])

		# Remove file after downloading
		if variables.delete_after_download is True:
			journal.warning(f"[YTCON] REMOVING {variables.queue_list[temp1_index]['file']}...")
			os.remove(variables.queue_list[temp1_index]["file"])
	except:
		exit_with_exception(traceback.format_exc())

	return None
