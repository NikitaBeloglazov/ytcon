import os
import sys
import re
import time
import logging
import threading
import traceback
from pathlib import Path
import pprint
import pickle
import urwid
import pyperclip
import ffmpeg # | !!!! "ffmpeg-python", NOT "ffmpeg" !!! | # https://kkroening.github.io/ffmpeg-python/ # python310-ffmpeg-python
# import notify2 # TODO
import yt_dlp

# - = logging init - = - = - = - = - = - = - = - = - = - = - = - =
logger = logging.getLogger('main_logger')
logger.setLevel(logging.DEBUG)

# Create handler for the INFO level
info_file_handler = logging.FileHandler('/tmp/info.log', mode='w')
info_file_handler.setLevel(logging.INFO)

# Create handler for the DEBUG level
debug_file_handler = logging.FileHandler('/tmp/debug.log', mode='w')
debug_file_handler.setLevel(logging.DEBUG)

# Add formatter
formatter = logging.Formatter('%(levelname)s: %(message)s')
info_file_handler.setFormatter(formatter)
debug_file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(info_file_handler)
logger.addHandler(debug_file_handler)

# Write test logs
logger.debug('== DEBUG LOG FILE ==')
logger.info('== INFO LOG FILE ==')
# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - =
configpath = os.path.expanduser("~") + "/.config/ytcon/"

class JournalClass:
	"""
	A log wrapper for yt-dlp and a logging class for the whole application.
	info, warning and error will be added to the logs field. (logprinter())
	For debug messages it is highly recommended to use logger.debug instead of journal
	"""
	def debug(self, msg):
		""" !!! For yt-dlp """
		if msg.startswith('[debug] '):
			logger.debug(msg)
		else:
			self.info(msg)

	# show: show in logs field
	def info(self, msg, show=True):
		""" info log level """
		logger.info(msg)
		if show:
			self.add_to_logs_field(msg)
	def warning(self, msg, show=True):
		""" warning log level """
		logger.warning(msg)
		if show:
			self.add_to_logs_field(msg)
	def error(self, msg, show=True):
		""" error log level. The error message will also be added to the errorprinter() """
		if msg == "ERROR: kwallet-query failed with return code 1. Please consult the kwallet-query man page for details":
			return None # Outdated: does not appear in yt-dlp on python3.11

		logger.error(msg)
		ControlClass.last_error = msg
		ControlClass.error_countdown = 99
		if show:
			self.add_to_logs_field(msg)
		return None

	def clear_errors(self, _=None):
		""" Clear the errorprinter() field """
		ControlClass.last_error = ""
		ControlClass.error_countdown = 0

	def add_to_logs_field(self, msg):
		""" there logs will be added to the logprinter() field. """
		if "[download]" in msg and "%" in msg and "at" in msg:
			# awoid logging such as "[download] 100.0% of   52.05MiB at    3.07MiB/s ETA 00:00"
			return None

		del ControlClass.log[0]
		msg = str(msg).replace("\n", "")
		if len(msg) > RenderClass.width:
			temp1 = RenderClass.width - 3
			ControlClass.log.append(msg[0:temp1]+"...")
		else:
			ControlClass.log.append(msg)
		# logger.debug(ControlClass.log)
		return None

journal = JournalClass()

class SettingsClass:
	def __init__(self):

		# Default settings
		self.settings = {"special_mode": False, "clipboard_autopaste": True}

	class SettingNotFoundError(Exception):
		pass

	def show_settings_call(self, _=None):
		RenderClass.settings_show = not RenderClass.settings_show

	def get_setting(self, setting_name):
		# Здесь предполагается код для получения настройки из базы данных
		# Если настройка не найдена, вызываем исключение SettingNotFoundError
		try:
			return self.settings[setting_name]
		except KeyError:
			raise self.SettingNotFoundError

	def write_setting(self, setting_name, setting_content):
		self.settings[setting_name] = setting_content

	def save(self, button=None): # in the second argument urwid puts the button of which the function was called
		logger.debug(Path(configpath).mkdir(parents=True, exist_ok=True))
		pickle.dump(self.settings, open(configpath + "settings.db", "wb"))
		journal.info(f"[YTCON] {configpath}settings.db saved")
		RenderClass.flash_button_text(button, RenderClass.green)

	def load(self, button=None): # in the second argument urwid puts the button of which the function was called
		global update_checkboxes
		try:
			self.settings = pickle.load(open(configpath + "settings.db", "rb"))
			journal.info(f"[YTCON] {configpath}settings.db loaded")
			update_checkboxes()
			RenderClass.flash_button_text(button, RenderClass.green)
		except FileNotFoundError:
			journal.warning(f"[YTCON] Saved settings load failed: FileNotFoundError: {configpath}settings.db")
			RenderClass.flash_button_text(button, RenderClass.red)

	def special_mode_switch(self, _=None, _1=None):
		journal.info("")
		if self.get_setting("special_mode"): # true
			self.write_setting("special_mode", False)
			journal.info("[YTCON] special_mode: True -> False")
			journal.info("[YTCON] SP deactivated! now a default yt-dlp extractor settings will be used.")
		elif not self.get_setting("special_mode"): # false
			self.write_setting("special_mode", True)
			journal.info("[YTCON] special_mode: False -> True")
			journal.info("[YTCON] SP activated! now a different user agent will be used, and cookies will be retrieved from chromium")

	def clipboard_autopaste_switch(self, _=None, _1=None):
		journal.info("")
		if self.get_setting("clipboard_autopaste"): # true
			self.write_setting("clipboard_autopaste", False)
			journal.info("[YTCON] clipboard_autopaste: True -> False")
		elif not self.get_setting("clipboard_autopaste"): # false
			self.write_setting("clipboard_autopaste", True)
			journal.info("[YTCON] clipboard_autopaste: False -> True")
		journal.info("[YTCON] A signal to the clipboard processing thread has been sent.")

settings = SettingsClass()

class ControlClass_base:
	""" It stores information about the download queue and some information that must be passed through several functions. """
	def __init__(self):
		self.queue_list = {}
		self.ydl_opts = {}

		self.last_error = ""
		self.error_countdown = 0
		self.prev_last_error = ""
		self.prev_error_countdown = 0

		self.log = ["", "", "", "", "", "Logs will appear there.."]
		self.oldlog = ["", "", "", "", "", ""]
		self.exit = False
		self.exception = ""
		self.clipboard_checker_state_launched = False

	def delete_finished(self):
		""" Removes all completed operations from ControlClass.queue_list with a loop """
		try:
			temp1 = 0
			temp2_new = self.queue_list.copy()
			for item, item_content in self.queue_list.copy().items():
				if item_content["status"] == "exists" or item_content["status"] == "finished":
					del temp2_new[item]
					if "meta_index" not in item_content:
						temp1 = temp1 + 1
			self.queue_list = temp2_new
			logger.debug(self.queue_list)
			RenderClass.remove_all_widgets()
			return str(temp1)
		except:
			exit_with_exception(traceback.format_exc())
		return None

	def clear(self, _=None):
		journal.clear_errors()
		journal.info(f"[YTCON] {self.delete_finished()} item(s) removed from list!")

class RenderClass_base:
	""" It stores some information about rendering, screen, some functions for working with widgets and some functions that are related to rendering. """
	def __init__(self):
		self.methods = self.MethodsClass()
		self.settings_show = False

		self.errorprinter_animation = 3

		# Init colors
		self.red = urwid.AttrSpec('dark red', 'default')
		self.yellow = urwid.AttrSpec('brown', 'default')
		self.green = urwid.AttrSpec('dark green', 'default')
		self.cyan = urwid.AttrSpec('dark cyan', 'default')

	def add_row(self, text):
		""" Add an additional widget to top_pile for drawing a new task """
		top_pile.contents = top_pile.contents + [[urwid.Text(text), top_pile.options()],]

	def edit_or_add_row(self, text, pos):
		""" Edit a widget with a specific serial number, and if there is none, then create a new one """
		if pos > self.calculate_widget_height(top_pile) - 1:
			self.add_row(text)
		else:
			top_pile.contents[pos][0].set_text(text)

	def remove_all_widgets(self):
		"""
		If there are obsolete widgets in top_pile that will not be changed, they are considered garbage,
		for this you need to call remove_all_widgets, all widgets, including unnecessary old ones, 
		will be removed, but will be recreated if needed
		"""
		top_pile.contents = []

	def calculate_widget_height(self, widget):
		""" (recursively) Counts how many rows the widget occupies in height """
		if isinstance(widget, urwid.Text):
			# Returns the number of lines of text in the widget
			return len(widget.text.split('\n'))
		if isinstance(widget, urwid.Pile):
			# Recursively sums the heights of widgets inside a urwid.Pile container
			return sum(self.calculate_widget_height(item[0]) for item in widget.contents)
		return 0 # Return 0 for unsupported widget types (?)

	def flash_button_text(self, button, color):
		if button == None:
			return None
		temp1 = button.get_label()
		for i in range(1, 5): # 4 times
			button.set_label((color, temp1))
			RenderClass.loop.draw_screen()
			time.sleep(0.1)
			button.set_label(temp1)
			RenderClass.loop.draw_screen()
			time.sleep(0.1)

	class MethodsClass:
		""" Minor methods mostly needed by render_tasks """
		def __init__(self):
			logger.debug("MethodsClass init")

		def name_shortener(self, name, symbols):
			""" Shortens filenames so they fit in the console """
			if len(name) < symbols:
				return name
			return name[0:symbols-3].strip() + "..."

		def bettersize(self, text):
			""" Rounds up file sizes """
			if text == "NaN":
				return "NaN"
			if len(text.split(".")) == 1:
				return text
			return text.split(".")[0] + text[-3:-1] + text[-1]

		def divide_without_remainder(self, num):
			"""
			Division without remainder. Used for centering in the whitespace_stabilization function
				print(divide(22))  # Out: [11, 11]
				print(divide(23))  # Out: [11, 12]
			"""
			quotient = num // 2
			remainder = num % 2
			return [quotient, quotient + remainder]

		def whitespace_stabilization(self, text, needed_space):
			""" Reserves space for a certain number of spaces, and centers the information within a line,
			using divide_without_remainder to count the free space.

			If the free space cannot be divided entirely, then the text is centered slightly to the left
			"""
			if len(text) == needed_space:
				return text
			if len(text) > needed_space:
				return text[0:needed_space-2] + ".."
			white_space = needed_space - len(text)
			white_space = self.divide_without_remainder(white_space)
			return ' '*white_space[0] + text + ' '*white_space[1]

		def progressbar_generator(self, percent, error=False):
			""" Generates progress bar """
			percent = int(percent.split(".")[0])
			progress = round(percent / 4)
			white_space = 25 - progress
			if error:
				return f"| {'='*(white_space-2)} |"
			return f"|{'█'*progress}{' '*white_space}|"

def hook(d):
	""" A hook that is called every time by yt-dlp when the state of the task changes (example percent changed),
	and the hook writes the necessary information to the class in order to draw it later """
	try:
		# - = - = - log spam filter - = - = - = - =
		if "automatic_captions" in d["info_dict"]:
			del d["info_dict"]["automatic_captions"]
		if "formats" in d["info_dict"]:
			del d["info_dict"]["formats"]
		if "thumbnails" in d["info_dict"]:
			del d["info_dict"]["thumbnails"]
		if "heatmap" in d["info_dict"]:
			del d["info_dict"]["heatmap"]
		# - = - = - = - = - = - = - = - = - = - = -

		logger.debug(pprint.pformat(d))
		if "multiple_formats" in ControlClass.queue_list[d["info_dict"]["original_url"]]:
			indexx = d["info_dict"]["original_url"] + ":" + d["info_dict"]["format_id"]
		else:
			indexx = d["info_dict"]["original_url"]

		# - = - resolution detector - = - = - = - = - = - = - = - = - = -
		if ControlClass.queue_list[indexx]["resolution"].find("???") > -1 and (ControlClass.queue_list[indexx].get("resolution_detection_tried_on_byte", 0) + 4000000) < int(d.get("downloaded_bytes", 0)) and ControlClass.queue_list[indexx].get("resolution_detection_tries", 0) < 5:
			# int(d["downloaded_bytes"]) > 4000000 # if the file size is too smol, it does not have the needed metadata and ffprobe gives an error
			logger.debug("DOWNBYTES: %s", str(d["downloaded_bytes"]))
			temp1 = get_resolution_ffprobe(d["tmpfilename"])
			temp2 = str(ControlClass.queue_list[indexx].get("resolution_detection_tries", 0)+1)

			if temp1 is not None:
				ControlClass.queue_list[indexx]["resolution"] = temp1
				journal.info(f"[YTCON] Detected resolution: {temp1} (on try {temp2})" )
			else:
				journal.warning(f'[YTCON] Resolution detection failed: ffprobe gave an error (try {temp2})')
			ControlClass.queue_list[indexx]["resolution_detection_tried_on_byte"] = int(d["downloaded_bytes"])
			ControlClass.queue_list[indexx]["resolution_detection_tries"] = ControlClass.queue_list[indexx].get("resolution_detection_tries", 0) + 1
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

		ControlClass.queue_list[indexx]["file"] = d["info_dict"]['_filename']
		if ControlClass.queue_list[indexx]["status"] == "exists" and d["status"] == "finished":
			raise InputHandler.InputProcessed
		ControlClass.queue_list[indexx]["status"] = d["status"]

		if int(d["_percent_str"].strip().split(".")[0]) > 100:
			journal.warning("[YTCON] yt-dlp returned percent more than 100%: \"" + d["_percent_str"].strip() + "\". Values remain unchanged...")
		else:
			ControlClass.queue_list[indexx]["status_short_display"] = d["_percent_str"].strip()
			ControlClass.queue_list[indexx]["percent"] = d["_percent_str"].strip()
		ControlClass.queue_list[indexx]["speed"] = d["_speed_str"].strip()

		try:
			if ControlClass.queue_list[indexx]["eta"].count(":") > 1:
				ControlClass.queue_list[indexx]["eta"] = d["_eta_str"].strip()
			else:
				ControlClass.queue_list[indexx]["eta"] = "ETA " + d["_eta_str"].strip()
		except KeyError:
			if d["status"] == "finished":
				ControlClass.queue_list[indexx]["eta"] = "ETA 00:00"

		try:
			if d["_total_bytes_estimate_str"].strip() == "N/A":
				ControlClass.queue_list[indexx]["size"] = d["_total_bytes_str"].strip()
			else:
				ControlClass.queue_list[indexx]["size"] = d["_total_bytes_estimate_str"].strip()
		except KeyError:
			pass

		try:
			ControlClass.queue_list[indexx]["downloaded"] = d["_downloaded_bytes_str"].strip()
		except:
			pass

		d["info_dict"]["formats"] = []
		d["info_dict"]["thumbnails"] = []
		d["info_dict"]["subtitles"] = []
		d["info_dict"]["fragments"] = []

		logger.debug(pprint.pformat(ControlClass.queue_list))
	except InputHandler.InputProcessed:
		pass
	except:
		exit_with_exception(traceback.format_exc())

def downloadd(url):
	""" 
	The main component of ytcon, this class sets the basic parameters for the video,
	composes the title and starts downloading.

	For each link one thread (exception: playlists)
	"""
	try:
		if url in ControlClass.queue_list:
			if ControlClass.queue_list[url]["status"] not in ("exists", "finished"):
				journal.error(f"[YTCON] Video link \"{RenderClass.methods.name_shortener(url, 40)}\" is already downloading!")
				return None

		# TODOOOOOO
		with yt_dlp.YoutubeDL(ControlClass.ydl_opts) as ydl:
			logger.debug(str(ydl.params))
			# needed for some sites. you may need to replace it with the correct one
			if settings.get_setting("special_mode") is True:
				ydl.params["http_headers"]["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
				# "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
			# - = - = - = Get downloading formats (yt) and generate filename (global) = -
			infolist = ydl.extract_info(url, download=False)

			# - = - = - log spam filter - = - = - = - =
			if infolist is None: # yt-dlp returns videos with errors as None :||
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

			# - Playlists support - = - = - = - = - = - = - = - = - = - = -
			if "entries" in infolist:
				for i in infolist["entries"]:
					if i is None: # yt-dlp returns videos with errors as None :||
						continue
					threading.Thread(target=downloadd, args=(i["webpage_url"],), daemon=True).start()
				return None
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

			# - Name fiter + assemble - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			temp1 = re.sub(r"[^A-Za-z0-9А-Яа-я \-_.,]", "", infolist["title"].replace("&", "and")) # get title, remove all characters except allowed # >"|" -> "｜" yt-dlp, wtf?
			temp1 = " ".join(temp1.removesuffix(" 1").split()) # remove space duplicates and remove 1 in the end because for some reason yt-dlp adds it on its own
			id_in_filename = infolist["id"].removesuffix("-1")
			filename = f'{temp1} [{id_in_filename}].{infolist["ext"]}'

			# Name too long handler (https://github.com/ytdl-org/youtube-dl/issues/29912 and more more more issues)
			if len(filename.encode('utf-8')) > 254:
				# ^^^^^^^^^^^^^^^^^^^^^^^ counting bytes in filename
				logger.debug("ERROR: FILENAME MORE THAN 255 BYTES. SHORTING...")
				while len(filename.encode('utf-8')) > 254:
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
			if infolist["extractor"] == "youtube" and "requested_formats" in infolist:
				multiple_formats = True

			temp1_index = map_variables.main(multiple_formats, infolist, filename)

			if exists:
				ControlClass.queue_list[infolist["original_url"]]["status"] = "exists"
				if multiple_formats:
					for i in infolist["requested_formats"]:
						temp1_index = infolist["original_url"] + ":" + i["format_id"]
						ControlClass.queue_list[temp1_index]["status"] = "exists"
						ControlClass.queue_list[temp1_index]["downloaded"] = ControlClass.queue_list[temp1_index]["size"]
						ControlClass.queue_list[temp1_index]["status_short_display"] = "Exist"
						ControlClass.queue_list[temp1_index]["percent"] = "100.0%"
				else:
					ControlClass.queue_list[temp1_index]["downloaded"] = ControlClass.queue_list[temp1_index]["size"]
					ControlClass.queue_list[temp1_index]["status_short_display"] = "Exist"
					ControlClass.queue_list[temp1_index]["percent"] = "100.0%"
			# - = - = - = - = - = - = - = - = - = - = - = - =
			logger.debug(pprint.pformat(ControlClass.queue_list))

			with yt_dlp.YoutubeDL(ControlClass.ydl_opts | {"outtmpl": filename}) as ydl2:
				logger.debug(ydl2.download(url))
				if ControlClass.last_error.find("[Errno 36] File name too long") > -1:
					raise yt_dlp.utils.DownloadError(ControlClass.last_error)
			# - = Mark meta as finished = -
			if "meta_index" in ControlClass.queue_list[infolist["original_url"]]:
				ControlClass.queue_list[infolist["original_url"]]["status"] = "finished"

	except yt_dlp.utils.DownloadError as e:
		journal.error(str(e), show=False)
		map_variables.mark_as_error(url)
		return None
	except:
		exit_with_exception(traceback.format_exc())

	# - = - = - = [Post-processing] = - = - = - #
	try:
		del ydl
		if ControlClass.queue_list[temp1_index]["status"] == "exists":
			return None # skip post-process if file already exists
		# Removes Last-modified header. Repeats --no-mtime functionality which is not present in yt-dlp embeded version
		os.utime(ControlClass.queue_list[temp1_index]["file"])

		# Remove file after downloading for testing purposes
		# journal.warning(f"[NOTSAVE] Removing {ControlClass.queue_list[temp1_index]['file']}...")
		# os.remove(ControlClass.queue_list[temp1_index]["file"])
	except:
		exit_with_exception(traceback.format_exc())

	return None

class MapVariablesClass:
	""" Created to simplify the distribution of parameters, work is organized here with playlists and requesting several formats on youtube """

	def main(self, multiple_formats, infolist, filename):
		""" Finding some specific parameters and using a loop assign if there are several files """
		if multiple_formats:
			ControlClass.queue_list[infolist["original_url"]] = {}
			ControlClass.queue_list[infolist["original_url"]]["meta_index"] = True
			ControlClass.queue_list[infolist["original_url"]]["multiple_formats"] = True
			ControlClass.queue_list[infolist["original_url"]]["formats"] = []
			ControlClass.queue_list[infolist["original_url"]]["status"] = "waiting"
			for i in infolist["requested_formats"]:
				temp1_index = infolist["original_url"] + ":" + i["format_id"]
				ControlClass.queue_list[infolist["original_url"]]["formats"].append(i["format_id"])
				self.map_variables(temp1_index, infolist, i, filename)
			return temp1_index
		# else:
		temp1_index = infolist["original_url"]
		self.map_variables(temp1_index, infolist, infolist, filename)
		return temp1_index

	def map_variables(self, temp1_index, infolist, i, filename):
		""" Main parameter assigner. In some cases, it can be used in a loop """
		ControlClass.queue_list[temp1_index] = {}
		ControlClass.queue_list[temp1_index]["status"] = "waiting"
		ControlClass.queue_list[temp1_index]["status_short_display"] = "Wait"
		ControlClass.queue_list[temp1_index]["percent"] = "0.0%"
		ControlClass.queue_list[temp1_index]["speed"] = "0KiB/s"
		try:
			ControlClass.queue_list[temp1_index]["size"] = str(round(i["filesize"]/1e+6)) + "MiB"
		except KeyError:
			ControlClass.queue_list[temp1_index]["size"] = "???MiB"
		ControlClass.queue_list[temp1_index]["downloaded"] = "0MiB"
		ControlClass.queue_list[temp1_index]["eta"] = "ETA ??:??"
		ControlClass.queue_list[temp1_index]["name"] = infolist["fulltitle"]
		if i["resolution"] == "audio only":
			ControlClass.queue_list[temp1_index]["resolution"] = "audio"
		else:
			if i.get("width", None) is None and i.get("height", None) is None:
				ControlClass.queue_list[temp1_index]["resolution"] = "???х???"
			else:
				ControlClass.queue_list[temp1_index]["resolution"] = (str(i.get("width", None)) + "x" + str(i.get("height", None))).replace("None", "???")
		ControlClass.queue_list[temp1_index]["site"] = infolist["extractor"].lower()
		ControlClass.queue_list[temp1_index]["file"] = filename

	def mark_as_error(self, url):
		""" Change the status of the downloaded link to Error if such link exists """
		if url in ControlClass.queue_list:
			ControlClass.queue_list[url]["status"] = "error"
			if "multiple_formats" in ControlClass.queue_list[url]:
				for i in url["formats"]:
					temp1_index = url + ":" + i
					ControlClass.queue_list[temp1_index]["status"] = "error"
					ControlClass.queue_list[temp1_index]["status_short_display"] = "Error"
			else:
				ControlClass.queue_list[url]["status_short_display"] = "Error"

map_variables = MapVariablesClass()

def render_tasks(loop, _):
	"""
	Graphic part of ytcon - draws a colored video queue from ControlClass.queue_list
	Shows names, extractors, ETAs, generates progress bars, etc.
	"""
	try:
		if not ControlClass.queue_list: # if ControlClass.queue_list == {}
			RenderClass.edit_or_add_row((RenderClass.cyan, "No tasks"), 0)
		else:
			r = 0
			for _, i in ControlClass.queue_list.items():
				if "meta_index" in i:
					continue # just ignore meta-downloads

				rcm = RenderClass.methods
				ws = rcm.whitespace_stabilization
				if i["status"] == "error":
					errorr = True
				else:
					errorr = False
				temp1 = f'{ws(i["status_short_display"], 7)}{rcm.progressbar_generator(i["percent"], errorr)}{ws(i["speed"], 13)}|{ws(rcm.bettersize(i["downloaded"])+"/"+rcm.bettersize(i["size"]), 15)}| {ws(i["eta"], 9)} | {ws(i["site"], 7)} | {ws(i["resolution"], 9)} | '
				fileshortname = rcm.name_shortener(i["name"], RenderClass.width - len(temp1))
				temp1 = temp1 + fileshortname

				if i["status"] == "waiting":
					RenderClass.edit_or_add_row((RenderClass.cyan, temp1), r)
				elif i["status"] == "error":
					RenderClass.edit_or_add_row((RenderClass.red, temp1), r)
				elif i["status"] == "exists":
					RenderClass.edit_or_add_row((RenderClass.yellow, temp1), r)
				elif i["status"] == "finished":
					RenderClass.edit_or_add_row((RenderClass.green, temp1), r)
				else:
					RenderClass.edit_or_add_row(temp1, r)

				r = r+1
		loop.set_alarm_in(0.3, render_tasks)
	except:
		exit_with_exception(traceback.format_exc())


class InputHandlerClass:
	"""
		Class for processing user input.
		Contains a modified Urwid.edit widget and functions for processing commands and URLs
	"""
	class InputBox(urwid.Edit):
		""" 
			A modified urwid.Edit Widget.
			If the user presses Enter, it collects text and sent text to input_handler,
			and after that is it cleans the input field
		"""
		def keypress(self, size, key): # TODO alt key handler?
			if key != 'enter':
				return super().keypress(size, key)
			InputHandler.input_handler(self.get_edit_text())
			self.set_edit_text("")
			return None

	class InputProcessed(Exception):
		""" Dummy exception, when called means that the processing of this request is completed. """

	def input_handler(self, text):
		""" Main input handler logic """
		try:
			original_text = text
			text = text.lower()

			if text == "":
				# Force refreshing screen...
				loop.draw_screen()
				raise self.InputProcessed

			journal.info("")
			journal.info("[YTCON] [INPUT] " + original_text)

			# - = Special mode handler = -
			if text in ("sp", "specialmode"):
				settings.special_mode_switch()
				raise self.InputProcessed
			# - = - = - = - = - = - = - = 

			# - = Clipboard auto-paste = -
			if text in ("cb", "clipboard", "clip"):
				settings.clipboard_autopaste_switch()
				raise self.InputProcessed
			# - = - = - = - = - = - = - = 

			if text in ("clear", "cls"):
				ControlClass.clear()

			elif text == "logtest":
				logger.debug("[TEST] 1")
				journal.info("[TEST] 2")
				journal.warning("[TEST] 3")
				journal.error("[TEST] 4")
				journal.error("[TEST] 5", show=False)
				journal.info("😘😘😘😘 6") # can break something, emojis have problems calculating sizes

			elif text == "makecrash":
				try:
					0/0
				except:
					exit_with_exception(traceback.format_exc())

			elif text == "set 0":
				RenderClass.settings_show = False
			elif text == "set 1":
				RenderClass.settings_show = True

			elif text == "set ls":
				journal.info(settings.settings)

			elif text == "save":
				settings.save()
				journal.info(settings.settings)
			elif text == "load":
				settings.load()
				journal.info(settings.settings)

			else:
				threading.Thread(target=downloadd, args=(original_text,), daemon=True).start()

		except self.InputProcessed:
			pass
		except:
			exit_with_exception(traceback.format_exc())

InputHandler = InputHandlerClass()


def errorprinter(loop, _):
	""" Draws errors in error_widget in red, after some time (specified in the timer) removes error messages """
	try:
		# - = skip, do not re-render if there is no errors - = - = - = - = -
		# if ControlClass.prev_last_error == ControlClass.last_error and ControlClass.prev_error_countdown == ControlClass.error_countdown:
		#	time.sleep(0.6)
		#	continue
		# - = - = - = - = - = - = - = - = - = - = - = - = - - = - = - = -
		to_render = []
		to_render.append("- - -\n")

		if ControlClass.error_countdown != 0:
			error_text_generator = "[" + RenderClass.methods.whitespace_stabilization(str(ControlClass.error_countdown), 2) + "] " + str(ControlClass.last_error)
		else:
			error_text_generator = str(ControlClass.last_error)

		error_text_generator = error_text_generator.replace("; please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U", "")

		if ControlClass.last_error == "":
			to_render.append((RenderClass.cyan, error_text_generator))
		else:
			to_render.append((RenderClass.red, error_text_generator))

		#to_render.append((RenderClass.red, error_text_generator))
		if (RenderClass.width) > len(error_text_generator):
			to_render.append("\n\n")
		elif (RenderClass.width * 2) > len(error_text_generator):
			to_render.append("\n")
		#elif (RenderClass.width * 3) > len(error_text_generator):
		#	pass

		# - = - = - = - = - = - unfold animation - = - = - = - = - = - 
		if RenderClass.errorprinter_animation == 0:
			error_widget.set_text(to_render)
		elif RenderClass.errorprinter_animation == 1:
			error_widget.set_text(to_render[:-1])
		elif RenderClass.errorprinter_animation == 2:
			if to_render[:-2] == ["- - -\n"]:
				error_widget.set_text("- - -")
			else:
				error_widget.set_text(to_render[:-2])
		elif RenderClass.errorprinter_animation == 3:
			if to_render[:-3] == []:
				error_widget.set_text("")
			else:
				error_widget.set_text(to_render[:-3])

		if ControlClass.last_error == "":
			if RenderClass.errorprinter_animation < 3 and RenderClass.errorprinter_animation >= 0:
				RenderClass.errorprinter_animation += 1
		else:
			if RenderClass.errorprinter_animation <= 3 and RenderClass.errorprinter_animation > 0:
				RenderClass.errorprinter_animation = RenderClass.errorprinter_animation - 1
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

		ControlClass.prev_last_error = ControlClass.last_error
		ControlClass.prev_error_countdown = ControlClass.error_countdown

		if ControlClass.error_countdown != 0:
			ControlClass.error_countdown = ControlClass.error_countdown - 1
			if ControlClass.error_countdown == 0:
				journal.clear_errors()

		#error_widget.set_text(to_render)
		loop.set_alarm_in(0.3, errorprinter)
	except:
		exit_with_exception(str(traceback.format_exc()))

def logprinter(loop, _):
	""" Prints the last 6 lines of logs in log_widget """
	try:
		# skip, do not re-render if it doesn't change - = - = - = - = -
		# if ControlClass.oldlog == ControlClass.log:
		#	time.sleep(0.5)
		#	continue
		# else:
		#	ControlClass.oldlog = ControlClass.log.copy()
		# - = - = - = - = - = - = - = - = - = - = - = - = - - = - = - =

		to_render = ControlClass.log[0] + "\n"
		to_render += ControlClass.log[1] + "\n"
		to_render += ControlClass.log[2] + "\n"
		to_render += ControlClass.log[3] + "\n"
		to_render += ControlClass.log[4] + "\n"
		to_render += ControlClass.log[5]
		log_widget.set_text(to_render)

		loop.set_alarm_in(0.3, logprinter)
	except:
		exit_with_exception(traceback.format_exc())

def tick_handler(loop, _):
	""" It just checks some conditions every few seconds and executes them. Not responsible for rendering. """

	# - = Clipboard thread activator = -
	if settings.get_setting("clipboard_autopaste") and ControlClass.clipboard_checker_state_launched is not True:
		threading.Thread(target=clipboard_checker, daemon=True).start()
	# - = - = - = - = - = - = - = - = -

	# - = Special mode cookie extractor activator = -
	if settings.get_setting("special_mode") is True and "cookiesfrombrowser" not in ControlClass.ydl_opts:
		ControlClass.ydl_opts["cookiesfrombrowser"] = ('chromium', ) # needed for some sites with login only access. you may need to replace it with the correct one
	elif settings.get_setting("special_mode") is False and "cookiesfrombrowser" in ControlClass.ydl_opts:
		del ControlClass.ydl_opts["cookiesfrombrowser"]
	# - = - = - = - = - = - = - = - = - = - = - = - =

	# - = - = - = - = - = - = - = - = -
	# The error handler, if it sees ControlClass.exit = True,
	# then exits the program commenting this with the text from ControlClass.exception.
	# The parent function of such actions: exit_with_exception()
	if ControlClass.exit is True:
		loop.stop()
		print("An unknown error has occurred!\n")
		time.sleep(0.5)
		print(ControlClass.exception)
		sys.exit(1)
	# - = - = - = - = - = - = - = - = -

	# - = - = - = - = - = - = - = - = -
	if RenderClass.settings_show is True and loop.widget is not settings_widget:
		try:
			update_checkboxes()
			loop.widget = settings_widget
		except:
			exit_with_exception(traceback.format_exc())
	if RenderClass.settings_show is False and loop.widget is not main_widget:
		try:
			loop.widget = main_widget
		except:
			exit_with_exception(traceback.format_exc())
	# - = - = - = - = - = - = - = - = -

	main_footer.set_focus(input_widget)
	# - =
	loop.set_alarm_in(0.3, tick_handler)

def clipboard_checker():
	"""
	Checks the clipboard for new entries against old ones.
	If it sees new material on the clipboard, it will check whether this is a site, if it detects site, download starts
	"""
	try:
		ControlClass.clipboard_checker_state_launched = True
		journal.info("[YTCON] Clipboard auto-paste is ON.")

		new_clip = pyperclip.paste()
		if re.fullmatch(r"(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", new_clip):
			journal.info("[CLIP] URL detected: " + new_clip)
			threading.Thread(target=downloadd, args=(new_clip,), daemon=True).start()
		old_clip = new_clip

		while True:
			if settings.get_setting("clipboard_autopaste") is False:
				ControlClass.clipboard_checker_state_launched = False
				journal.info("[YTCON] Clipboard auto-paste turned off.")
				return None

			new_clip = pyperclip.paste()
			if new_clip != old_clip:
				if re.fullmatch(r"(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", new_clip):
					journal.info("[CLIP] New URL detected: " + new_clip)
					threading.Thread(target=downloadd, args=(new_clip,), daemon=True).start()
				else:
					logger.debug(new_clip)
					journal.info("[CLIP] New content detected. But this is not URL. Ignoring..")
			old_clip = new_clip
			time.sleep(1)
	except:
		exit_with_exception(str(traceback.format_exc()) + "\n[!] There was a clear error with the clipboard. To fix it, you can use self.clipboard_checker_state = True in ControlClass_base and rewrite it to False if your system has issues with clipboard support. (Android, etc)") # TODO REWRITE
		return None

def exit_with_exception(text):
	""" Terminates the pseudo-graphics API and prints an error message, then exits the program """
	journal.error(text)
	ControlClass.exit = True
	ControlClass.exception = text

def get_resolution_ffprobe(file):
	""" Uses ffprobe to get video (even not fully downloaded) resolution """
	try:
		probe = ffmpeg.probe(file)
	except ffmpeg._run.Error as e:
		logger.debug("ffprobe error:")
		logger.debug(e.stderr)
		return None
	logger.debug("ffprobe response:")
	logger.debug(pprint.pformat(probe))
	for i in probe["streams"]:
		if "width" in i and "height" in i:
			return str(i["width"]) + "x" + str(i["height"])
	return None

# - = - = -
ControlClass = ControlClass_base()

ControlClass.ydl_opts = {
	'logger': journal,
	'progress_hooks': [hook],
	'no_color': True,
	#'outtmpl': '%(title)s [%(id)s].%(ext)s', # REALIZED IN own file handler
	'socket_timeout': 15,
	'retries': 20,
	'fragment_retries': 40,
	'retry_sleep': 'http,fragment:exp',
	#'download_archive': 'downloaded_videos.txt', # !!! DANGEROUS OPTION !!! # TODO?
	'ignoreerrors': True # !!! DANGEROUS OPTION !!! # Don't exit if there is private video in playlist
	}

RenderClass = RenderClass_base()

#processes_widget = urwid.Text("Initializing...")
#lol = urwid.Text("lol")

top_pile = urwid.Pile([])

#logger.debug(pprint.pformat(top_pile.contents))
#logger.debug(pprint.pformat(calculate_widget_height(top_pile)))

log_widget = urwid.Text("Initializing...")
error_widget = urwid.Text("Initializing...")
input_widget = InputHandler.InputBox("Enter URL > ")

main_settings_button = urwid.Button("Settings", on_press=settings.show_settings_call)
main_clear_button = urwid.Button("Clear", on_press=ControlClass.clear)

main_footer_buttons = urwid.GridFlow([main_settings_button, main_clear_button, urwid.Button("Button3")], cell_width=12, h_sep=2, v_sep=1, align="left")
main_footer_buttons_with_attrmap = urwid.AttrMap(main_footer_buttons, "buttons_footer")
#fill = urwid.Frame(urwid.Filler(lol, "top"), header=processes_widget, footer=urwid.Pile([log_widget, error_widget, input_widget]), focus_part='footer')

main_footer = urwid.Pile(
		[
		error_widget,
		urwid.Text("- - -"),
		log_widget,
		urwid.Text("- - -"),
		input_widget,
		urwid.Divider(),
		urwid.Text("- - -"),
		main_footer_buttons_with_attrmap,
		])
main_widget = urwid.Frame(
	urwid.Filler(top_pile, "top"),
	footer=main_footer, 
	focus_part='footer')

# - = SETTINGS - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = 

def on_checkbox_change(checkbox, state, user_data=None):
	if state:
		status_text.set_text("CheckBox включен")
	else:
		status_text.set_text("CheckBox выключен")

# Создаем CheckBox для каждой опции настроек
def update_checkboxes():
	checkbox1.set_state(settings.get_setting("clipboard_autopaste"), do_callback=False)
	checkbox2.set_state(settings.get_setting("special_mode"), do_callback=False)
	#checkbox1.set_state(settings.get_setting(clipboard_autopaste))
	#checkbox1.set_state(settings.get_setting(clipboard_autopaste))

checkbox1 = urwid.CheckBox("Clipboard auto-paste", on_state_change=settings.clipboard_autopaste_switch)
checkbox2 = urwid.CheckBox("Special mode", on_state_change=settings.special_mode_switch)
checkbox3 = urwid.CheckBox("Delete after download", on_state_change=on_checkbox_change)
checkbox4 = urwid.CheckBox("!just test", on_state_change=on_checkbox_change)
update_checkboxes()

# Создаем виджет urwid.Text для отображения состояния CheckBox
status_text = urwid.Text("")

# Создаем Pile-контейнер, который содержит CheckBox и заполнители
settings_pile = urwid.Pile([
	urwid.Divider(),
	checkbox1,
	urwid.Divider(),
	checkbox2,
	urwid.Divider(),
	checkbox3,
	urwid.Divider(),
	checkbox4,
	urwid.Divider(),
	status_text
])

# Создаем Filler-контейнер, чтобы отцентрировать Pile по вертикали
settings_filler = urwid.Filler(settings_pile, valign='top')

# Оборачиваем содержимое в urwid.Padding с отступами по 2 символа с каждой стороны
settings_padding = urwid.Padding(settings_filler, left=4, right=4, align='center')

header_widget = urwid.AttrMap(urwid.Padding(urwid.Text(" - = Settings = - "), align='center'), 'reversed')

exit_settings_button = urwid.AttrMap(urwid.Button("Exit from settings", on_press=settings.show_settings_call), "reversed")

save_settings_button = urwid.Button("Save to config file", on_press=settings.save)
load_settings_button = urwid.Button("Load from config file", on_press=settings.load)

footer_buttons = urwid.GridFlow([exit_settings_button, save_settings_button, load_settings_button], cell_width=25, h_sep=2, v_sep=1, align="left")

footer_widget = urwid.Pile([
	urwid.Text("- - -"),
	log_widget,
	urwid.Text("- - -"),
	footer_buttons
])

# Создаем фрейм с обрамлением
settings_widget = urwid.Frame(settings_padding, header=header_widget, footer=footer_widget)
# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - =

custom_palette = [
	('reversed', 'standout', ''),  # ('name_of_style', 'color_text', 'color_background')
	# tip: standout = reversed
	('buttons_footer', 'light green', '')
]

loop = urwid.MainLoop(main_widget, palette=custom_palette)

RenderClass.width, RenderClass.height = loop.screen.get_cols_rows()
RenderClass.loop = loop

logger.debug(RenderClass.width)
logger.debug(RenderClass.height)

settings.load()

loop.set_alarm_in(0, render_tasks)
loop.set_alarm_in(0, logprinter)
loop.set_alarm_in(0, errorprinter)
loop.set_alarm_in(0, tick_handler)

# for testing purposes?
# threading.Thread(target=downloadd, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

loop.run()
