import os
import sys
import re
import time
import logging
import threading
import traceback
import pprint
import urwid
import pyperclip
import ffmpeg # | !!!! "ffmpeg-python", NOT "ffmpeg" !!! | # https://kkroening.github.io/ffmpeg-python/ # python310-ffmpeg-python
# import notify2
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
		logger.error(msg)
		ControlClass.last_error = msg
		ControlClass.error_countdown = 99
		if show:
			self.add_to_logs_field(msg)

	def clear_errors(self):
		""" Clear the errorprinter() field """
		ControlClass.last_error = "No errors:)"
		ControlClass.error_countdown = 0

	def add_to_logs_field(self, msg):
		""" there logs will be added to the logprinter() field. """
		if "[download]" in msg and "%" in msg and "at" in msg:
			# awoid logging such as "[download] 100.0% of   52.05MiB at    3.07MiB/s ETA 00:00"
			return None

		del ControlClass.log[0]
		msg = msg.replace("\n", "")
		if len(msg) > RenderClass.width:
			temp1 = RenderClass.width - 3
			ControlClass.log.append(msg[0:temp1]+"...")
		else:
			ControlClass.log.append(msg)
		# logger.debug(ControlClass.log)
		return None

journal = JournalClass()

class ControlClass_base:
	""" It stores information about the download queue and some information that must be passed through several functions. """
	def __init__(self):
		self.queue_list = {}
		self.ydl_opts = {}

		self.last_error = "No errors:)"
		self.error_countdown = 0
		self.prev_last_error = ""
		self.prev_error_countdown = 0

		self.log = ["", "", "", "", "", "Logs will appear there.."]
		self.oldlog = ["", "", "", "", "", ""]
		self.exit = False
		self.exception = ""
		self.special_mode = False
		self.clipboard_checker_state = True
		self.clipboard_checker_state_launched = False

class RenderClass_base:
	""" It stores some information about rendering, screen, some functions for working with widgets and some functions that are related to rendering. """
	def __init__(self):
		self.methods = self.MethodsClass()

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

		def progressbar_generator(self, percent):
			""" Generates progress bar """
			percent = int(percent.split(".")[0])
			progress = round(percent / 4)
			white_space = 25 - progress
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

		with yt_dlp.YoutubeDL(ControlClass.ydl_opts) as ydl:
			logger.debug(str(ydl.params))
			# needed for some sites. you may need to replace it with the correct one
			if ControlClass.special_mode:
				ydl.params["http_headers"]["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
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

			# - Name fiter + assemble - = - = - = - = - = - = - = - = - = - = -
			temp1 = re.sub(r"[^A-Za-z0-9А-Яа-я \-_.,]", "", infolist["title"].replace("&", "and")) # get title, remove all characters except allowed # >"|" -> "｜" yt-dlp, wtf?
			temp1 = " ".join(temp1.removesuffix(" 1").split()) # remove space duplicates and remove 1 in the end because for some reason yt-dlp adds it on its own
			filename = f'{temp1} [{infolist["id"].removesuffix("-1")}].{infolist["ext"]}'
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

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
			# - = Mark meta as finished = -
			if "meta_index" in ControlClass.queue_list[infolist["original_url"]]:
				ControlClass.queue_list[infolist["original_url"]]["status"] = "finished"

	except yt_dlp.utils.DownloadError as e:
		journal.error(str(e), show=False)
		return None
	except:
		exit_with_exception(traceback.format_exc())

	# - = - = - = [Post-processing] = - = - = - #
	if ControlClass.queue_list[temp1_index]["status"] == "exists":
		return None # skip post-process if file already exists
	# Removes Last-modified header. Repeats --no-mtime functionality which is not present in yt-dlp embeded version
	os.utime(ControlClass.queue_list[temp1_index]["file"])

	# Remove file after downloading for testing purposes
	# journal.warning(f"[NOTSAVE] Removing {ControlClass.queue_list[temp1_index]['file']}...")
	# os.remove(ControlClass.queue_list[temp1_index]["file"])
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

map_variables = MapVariablesClass()

def render_tasks(loop, _):
	"""
	Graphic part of ytcon - draws a colored video queue from ControlClass.queue_list
	Shows names, extractors, ETAs, generates progress bars, etc.
	"""
	if not ControlClass.queue_list: # if ControlClass.queue_list == {}
		RenderClass.edit_or_add_row((RenderClass.cyan, "No tasks"), 0)
	else:
		r = 0
		for _, i in ControlClass.queue_list.items():
			if "meta_index" in i:
				continue # just ignore meta-downloads

			rcm = RenderClass.methods
			ws = rcm.whitespace_stabilization
			temp1 = f'{ws(i["status_short_display"], 7)}{rcm.progressbar_generator(i["percent"])}{ws(i["speed"], 13)}|{ws(rcm.bettersize(i["downloaded"])+"/"+rcm.bettersize(i["size"]), 15)}| {ws(i["eta"], 9)} | {ws(i["site"], 7)} | {ws(i["resolution"], 9)} | '
			fileshortname = rcm.name_shortener(i["name"], RenderClass.width - len(temp1))
			temp1 = temp1 + fileshortname

			if i["status"] == "waiting":
				RenderClass.edit_or_add_row((RenderClass.cyan, temp1), r)
			elif i["status"] == "exists":
				RenderClass.edit_or_add_row((RenderClass.yellow, temp1), r)
			elif i["status"] == "finished":
				RenderClass.edit_or_add_row((RenderClass.green, temp1), r)
			else:
				RenderClass.edit_or_add_row(temp1, r)

			r = r+1
	loop.set_alarm_in(0.3, render_tasks)


class InputHandlerClass:
	"""
		In the days of curses, this was a full-fledged widget tucked into one function,
		but now it plays the role of just processing user input, another class is responsible for accepting
	"""
	class InputProcessed(Exception):
		""" Dummy exception, when called means that the processing of this request is completed. """

	def input(self, text):
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

			# - = Special mode handler = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			if text in ("sp", "specialmode"):
				journal.info("[YTCON] Specialmode status: " + str(ControlClass.special_mode))
				raise self.InputProcessed

			if text == "sp1":
				self.special_mode_status_set(True)
				raise self.InputProcessed
			if text == "sp0":
				self.special_mode_status_set(False)
				raise self.InputProcessed

			if text.split()[0] in ("sp", "specialmode"):
				if text.split()[1] == "1" or text.split()[1] == "true":
					self.special_mode_status_set(True)
				elif text.split()[1] == "0" or text.split()[1] == "false":
					self.special_mode_status_set(False)
				else:
					journal.error("[YTCON] failed to set SP status: input not recognized")
				raise self.InputProcessed
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			# - = Clipboard auto-paste status handler = - = - = - = - = - = - = - = - = - = - = - = - = - = - =
			if text in ("cb", "clipboard", "clip"):
				journal.info("[YTCON] Clipboard auto-paste status: " + str(ControlClass.clipboard_checker_state) + ", launched state: " + str(ControlClass.clipboard_checker_state_launched))
				raise self.InputProcessed

			if text in ("cb1", "clip1"):
				self.clipboard_status_set(True)
				raise self.InputProcessed
			if text in ("cb0", "clip0"):
				self.clipboard_status_set(False)
				raise self.InputProcessed

			if text.split()[0] in ("cb", "clipboard", "clip"):
				if text.split()[1] == "1" or text.split()[1] == "true":
					self.clipboard_status_set(True)
				elif text.split()[1] == "0" or text.split()[1] == "false":
					self.clipboard_status_set(False)
				else:
					journal.error("[YTCON] failed to set clipboard status: input not recognized")
				raise self.InputProcessed
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

			if text in ("clear", "cls"):
				journal.clear_errors()
				journal.info(f"[YTCON] {delete_finished()} item(s) removed from list!")

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

			else:
				threading.Thread(target=downloadd, args=(original_text,), daemon=True).start()

		except self.InputProcessed:
			pass
		except:
			exit_with_exception(traceback.format_exc())

	def special_mode_status_set(self, boool):
		"""
			special_mode_status_set(True) enables special mode,
			special_mode_status_set(False) disables it
		"""
		if boool: # true
			ControlClass.special_mode = True
			ControlClass.ydl_opts["cookiesfrombrowser"] = ('chromium', ) # needed for some sites with login only access. you may need to replace it with the correct one
			journal.info("[YTCON] SP activated! now a different user agent will be used, and cookies will be retrieved from chromium")
		elif not boool: # false
			ControlClass.special_mode = False
			if "cookiesfrombrowser" in ControlClass.ydl_opts:
				del ControlClass.ydl_opts["cookiesfrombrowser"]
			journal.info("[YTCON] SP deactivated! now a default yt-dlp extractor settings will be used.")
		else:
			journal.warning("[YTCON] failed to set SP status: input not recognized")

	def clipboard_status_set(self, boool):
		"""
			clipboard_status_set(True) enables clipboard auto-paste thread,
			clipboard_status_set(False) disables it
		"""
		if boool: # true
			if ControlClass.clipboard_checker_state: # == True
				journal.info("[YTCON] Already enabled.")
			else:
				ControlClass.clipboard_checker_state = True
				journal.info("[YTCON] A signal to the clipboard processing thread has been sent.")
		elif not boool: # false
			if ControlClass.clipboard_checker_state: # == False:
				journal.info("[YTCON] Already disabled.")
			else:
				ControlClass.clipboard_checker_state = False
				journal.info("[YTCON] A signal to the clipboard processing thread has been sent.")
		else:
			journal.error("[YTCON] failed to set clipboard status: input not recognized")

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
		# - = logic # TODO move to JournalClass?
		if ControlClass.last_error == "ERROR: kwallet-query failed with return code 1. Please consult the kwallet-query man page for details":
			ControlClass.error_countdown = 0
			journal.clear_errors()
		# - = - =

		if ControlClass.error_countdown != 0:
			error_text_generator = "[" + RenderClass.methods.whitespace_stabilization(str(ControlClass.error_countdown), 2) + "] " + str(ControlClass.last_error)
		else:
			error_text_generator = str(ControlClass.last_error)

		error_text_generator = error_text_generator.replace("; please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U", "")

		if ControlClass.last_error == "No errors:)":
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

		ControlClass.prev_last_error = ControlClass.last_error
		ControlClass.prev_error_countdown = ControlClass.error_countdown

		if ControlClass.error_countdown != 0:
			ControlClass.error_countdown = ControlClass.error_countdown - 1
			if ControlClass.error_countdown == 0:
				journal.clear_errors()

		error_widget.set_text(to_render)
		loop.set_alarm_in(0.3, errorprinter)
	except:
		exit_with_exception(str(traceback.format_exc()))

def logprinter(loop, _):
	""" Prints the last 6 lines of logs in log_widget """
	try:
		# - = Clipboard thread activator = -
		# it would be necessary to go somewhere else, but okay, let him stay here for now
		if ControlClass.clipboard_checker_state and ControlClass.clipboard_checker_state_launched is not True:
			threading.Thread(target=clipboard_checker, daemon=True).start()
		# - = - = - = - = - = - = - = - = -

		to_render = "- - -\n"

		# skip, do not re-render if it doesn't change - = - = - = - = -
		# if ControlClass.oldlog == ControlClass.log:
		#	time.sleep(0.5)
		#	continue
		# else:
		#	ControlClass.oldlog = ControlClass.log.copy()
		# - = - = - = - = - = - = - = - = - = - = - = - = - - = - = - =

		to_render += ControlClass.log[0] + "\n"
		to_render += ControlClass.log[1] + "\n"
		to_render += ControlClass.log[2] + "\n"
		to_render += ControlClass.log[3] + "\n"
		to_render += ControlClass.log[4] + "\n"
		to_render += ControlClass.log[5]
		log_widget.set_text(to_render)

		loop.set_alarm_in(0.3, logprinter)
	except:
		exit_with_exception(traceback.format_exc())

def delete_finished():
	""" Removes all completed operations from ControlClass.queue_list with a loop """
	try:
		temp1 = 0
		temp2_new = ControlClass.queue_list.copy()
		for item, item_content in ControlClass.queue_list.copy().items():
			if item_content["status"] == "exists" or item_content["status"] == "finished":
				del temp2_new[item]
				if "meta_index" not in item_content:
					temp1 = temp1 + 1
		ControlClass.queue_list = temp2_new
		logger.debug(ControlClass.queue_list)
		RenderClass.remove_all_widgets()
		return str(temp1)
	except:
		exit_with_exception(traceback.format_exc())
	return None

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
			if ControlClass.clipboard_checker_state is False:
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
		exit_with_exception(str(traceback.format_exc()) + "\n[!] There was a clear error with the clipboard. To fix it, you can use self.clipboard_checker_state = True in ControlClass_base and rewrite it to False if your system has issues with clipboard support. (Android, etc)")
		return None

def exit_with_exception(text): # TODO connect to all functions
	""" Terminates the pseudo-graphics API and prints an error message, then exits the program """
	journal.error(text)
	loop.stop()
	print("An unknown error has occurred!\n")
	time.sleep(0.5)
	print(text)
	sys.exit(1)

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
	'trim_file_name': 120, # TODO
	'retries': 20,
	'fragment_retries': 40,
	'retry_sleep': 'http,fragment:exp',
	#'download_archive': 'downloaded_videos.txt', # !!! DANGEROUS OPTION !!! # TODO?
	'ignoreerrors': True # !!! DANGEROUS OPTION !!! # Don't exit if there is private video in playlist
	}

RenderClass = RenderClass_base()

class InputBox(urwid.Edit):
	""" TODO """ # TODO
	def keypress(self, size, key):
		if key != 'enter':
			return super().keypress(size, key)
		InputHandler.input(self.get_edit_text())
		#RenderClass.add_row("test")
		#logger.debug(pprint.pformat(top_pile.contents))
		self.set_edit_text("")
		return None

#processes_widget = urwid.Text("Initializing...")
#lol = urwid.Text("lol")

top_pile = urwid.Pile([])

#logger.debug(pprint.pformat(top_pile.contents))
#logger.debug(pprint.pformat(calculate_widget_height(top_pile)))

log_widget = urwid.Text("Initializing...")
error_widget = urwid.Text("Initializing...")
input_widget = InputBox("Enter URL > ")

#fill = urwid.Frame(urwid.Filler(lol, "top"), header=processes_widget, footer=urwid.Pile([log_widget, error_widget, input_widget]), focus_part='footer')
fill = urwid.Frame(urwid.Filler(top_pile, "top"), footer=urwid.Pile([log_widget, error_widget, input_widget]), focus_part='footer')

loop = urwid.MainLoop(fill)

RenderClass.width, RenderClass.height = loop.screen.get_cols_rows()

logger.debug(RenderClass.width)
logger.debug(RenderClass.height)
loop.set_alarm_in(0, render_tasks)
loop.set_alarm_in(0, logprinter)
loop.set_alarm_in(0, errorprinter)

# for testing purposes?
# threading.Thread(target=downloadd, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

loop.run()
