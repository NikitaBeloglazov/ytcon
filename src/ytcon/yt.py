# - = Standart modules = -
import os
import re
import sys
import time
import pickle
import pprint
import logging
import threading
import traceback
import subprocess
from pathlib import Path
# - = - = - = - = - = - = -
import urwid
import pyperclip
import ffmpeg # | !!!! "ffmpeg-python", NOT "ffmpeg" !!! | # https://kkroening.github.io/ffmpeg-python/ # python310-ffmpeg-python

# - = - Check ffmpeg installed in system - = -
try:
	# Try to launch it
	subprocess.run("ffmpeg -version", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	subprocess.run("ffprobe -version", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except subprocess.CalledProcessError as e:
	# If there was a command execution error, ffmpeg is not installed
	print("\n[!!] FFMPEG and FFPROBE is not installed in your system. Install it with system package manager:\n  sudo apt install ffmpeg\n  sudo dnf install ffmpeg\n  sudo zypper install ffmpeg\n  sudo pacman -S ffmpeg.\n\nProgram execution cannot be continued. YTCON will be exit now.\n")
	sys.exit(1)
# - = - = - = - = - = - = - = - = - = - = - = -

import yt_dlp
#import notify2

# - = CHECK SYSTEM PATHS PART 1 - = - = - = - = - = - = - = - =
logs_that_will_be_printed_later = []
# - - - - - - - - - - - - -
# Check if it is android termux emulator and change dir to user-reachable internal storage
this_is_android_device = False
if os.getcwd().find("com.termux") != -1:
	print("[YTCON] Termux not user-reachable directory detected. Changing to /storage/emulated/0...")
	logs_that_will_be_printed_later.append("[YTCON] Termux not user-reachable directory detected.")
	logs_that_will_be_printed_later.append("[YTCON] Changing to /storage/emulated/0...")
	os.chdir("/storage/emulated/0")
	this_is_android_device = True
# - - - - - - - - - - - - -
# Current folder permissions check
try:
	with open("write_test", "wb") as filee:
		pass
	os.remove("write_test")
except:
	print(os.getcwd())
	print("[!!] Current folder is unwritable!")
	if this_is_android_device:
		print("Maybe Termux doesn't have storage permissions?")
	sys.exit(1)
# - - - - - - - - - - - - -
# /tmp folder check (For android and windows compability)
try:
	with open("/tmp/write_test", "wb") as filee:
		pass
	os.remove("/tmp/write_test")
	log_folder = "/tmp/"
except:
	print("[YTCON] /tmp folder is unavalible (windows, android?). setting current dir for logs..")
	logs_that_will_be_printed_later.append("[YTCON] /tmp folder is unavalible (windows, android?). setting current dir for logs..")
	log_folder = ""
# - - - - - - - - - - - - -
# Save file folder check
if "XDG_CONFIG_HOME" in os.environ:
	configpath = os.path.expanduser(os.environ["XDG_CONFIG_HOME"] + "/ytcon/")
else:
	configpath = os.path.expanduser("~/.config/ytcon/")

try:
	Path(configpath).mkdir(parents=True, exist_ok=True)
	with open(configpath + "write_test", "wb") as filee:
		pass
	os.remove(configpath + "write_test")
except:
	print(traceback.format_exc())
	print("= = =\n[!!] An error was occurred!\n")
	print("Save file folder check failed. Maybe XDG_CONFIG_HOME env or dir permissions broken?")
	print("The following path has problems: " + configpath)
	sys.exit(1)
# - = - = - = - = - = - = - = - = - = - = - = - = - = - =

# - = logging init - = - = - = - = - = - = - = - = - = - = - = - =
logger = logging.getLogger('main_logger')
logger.setLevel(logging.DEBUG)

# Create handler for the INFO level
info_file_handler = logging.FileHandler(log_folder+'info.log', mode='w')
info_file_handler.setLevel(logging.INFO)

# Create handler for the DEBUG level
debug_file_handler = logging.FileHandler(log_folder+'debug.log', mode='w')
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
	""" Сontains settings data and methods for them """
	def __init__(self):

		# Default settings
		self.settings = {"special_mode": False, "clipboard_autopaste": True}

	class SettingNotFoundError(Exception):
		""" Called if the specified setting is not found (see def get_setting) """

	def show_settings_call(self, _=None):
		""" Settings display state switch, made for urwid.Button(on_press=show_settings_call) """
		RenderClass.settings_show = not RenderClass.settings_show

	def get_setting(self, setting_name):
		""" Get setting, if it not found, calls SettingNotFoundError """
		try:
			return self.settings[setting_name]
		except KeyError as exc:
			raise self.SettingNotFoundError from exc

	def write_setting(self, setting_name, setting_content):
		""" Writes the settings to the memory. Made for the possible use of some "hooks" in the future """
		self.settings[setting_name] = setting_content

	def save(self, button=None): # in the second argument urwid puts the button of which the function was called
		""" Uses pickle for saving settings from memory to ~/.config/settings.db"""
		logger.debug(Path(configpath).mkdir(parents=True, exist_ok=True)) # Create dirs if they don't already exist
		with open(configpath + "settings.db", "wb") as filee:
			pickle.dump(self.settings, filee)
		journal.info(f"[YTCON] {configpath}settings.db saved")
		RenderClass.flash_button_text(button, RenderClass.green)

	def load(self, button=None): # in the second argument urwid puts the button of which the function was called
		""" Uses pickle for loading settings from ~/.config/settings.db to memory """
		try:
			with open(configpath + "settings.db", "rb") as filee:
				self.settings = pickle.load(filee)
			journal.info(f"[YTCON] {configpath}settings.db loaded")
			update_checkboxes()
			RenderClass.flash_button_text(button, RenderClass.green)
		except FileNotFoundError:
			# If file not found
			journal.warning(f"[YTCON] Saved settings load failed: FileNotFoundError: {configpath}settings.db")
			RenderClass.flash_button_text(button, RenderClass.red)
		except EOFError as exc:
			# If save file is corrupted
			logger.debug(traceback.format_exc())
			journal.warning(f"[YTCON] Saved settings load FAILED: EOFError: {exc}: {configpath}settings.db")
			journal.error("[YTCON] YOUR SETTINGS FILE IS CORRUPTED. Default settings restored and corrupted save file removed.")
			self.write_setting("clipboard_autopaste", False)
			update_checkboxes()
			journal.warning("[YTCON] Clipboard autopaste has been turned off for security reasons. You can it enable it in settings")
			logger.debug(os.remove(f"{configpath}settings.db"))

	def special_mode_switch(self, _=None, _1=None):
		""" Special mode switch function for urwid.Button's """
		journal.info("")
		if self.get_setting("special_mode"): # true
			self.write_setting("special_mode", False)
			journal.info("[YTCON] special_mode: True -> False")
			journal.info("[YTCON] SP deactivated! now a default yt-dlp extractor settings will be used.")
		elif not self.get_setting("special_mode"): # false
			self.write_setting("special_mode", True)
			journal.info("[YTCON] special_mode: False -> True")
			journal.info("[YTCON] SP activated! now a different user agent will be used, and cookies will be retrieved from chromium")
		update_checkboxes()

	def clipboard_autopaste_switch(self, _=None, _1=None):
		""" Clipboard autopaste switch function for urwid.Button's """
		journal.info("")
		if self.get_setting("clipboard_autopaste"): # true
			self.write_setting("clipboard_autopaste", False)
			journal.info("[YTCON] clipboard_autopaste: True -> False")
		elif not self.get_setting("clipboard_autopaste"): # false
			self.write_setting("clipboard_autopaste", True)
			journal.info("[YTCON] clipboard_autopaste: False -> True")
		journal.info("[YTCON] A signal to the clipboard processing thread has been sent.")
		update_checkboxes()

settings = SettingsClass()

class ControlClass_base:
	""" It stores information about the download queue and some information that must be passed through several functions. """
	def __init__(self):
		self.queue_list = {}
		self.ydl_opts = {}

		self.temp = {}
		self.temp["autopaste_button_color"] = "" # some kind of cache, see tick_handler

		self.last_error = ""
		self.error_countdown = 0
		self.prev_last_error = ""
		self.prev_error_countdown = 0

		self.delete_after_download = False

		self.log = ["", "", "", "", "", "Logs will appear there.."]
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
		""" Clears errors and finished downloads from memory """
		journal.clear_errors()
		journal.info(f"[YTCON] {self.delete_finished()} item(s) removed from list!")
		RenderClass.flash_button_text(main_clear_button, RenderClass.light_yellow, 2)

	def delete_after_download_switch(self, _=None, _1=None):
		""" Special mode switch function for urwid.Button's """
		journal.info("")
		if self.delete_after_download: # true
			self.delete_after_download = False
			journal.info("[YTCON] Delete after download disabled!")
		elif not self.delete_after_download: # false
			self.delete_after_download = True
			journal.error("[YTCON] Delete after download ENABLED! This means that the downloaded files WILL NOT BE SAVED!")
			journal.warning("[YTCON] Anyway this setting state will NOT be saved in the settings save file.")
			journal.warning("[YTCON] It resets every time when the utility is restarted. Made for test purposes.")

class RenderClass_base:
	""" It stores some information about rendering, screen, some functions for working with widgets and some functions that are related to rendering. """
	def __init__(self):
		self.version = "?.?.?"
		self.install_source = "???"
		self.pypi_version = "?.?.?"
		self.tried_check_pypi_version = False

		self.methods = self.MethodsClass()
		self.settings_show = False

		self.errorprinter_animation = 3

		# Init colors
		self.red = urwid.AttrSpec('dark red', 'default')
		self.light_red = urwid.AttrSpec('light red', 'default')
		self.yellow = urwid.AttrSpec('brown', 'default')
		self.light_yellow = urwid.AttrSpec('yellow', 'default')
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

	def flash_button_text(self, button, color, times=4):
		""" Makes the button to blink in the specified color """
		if button is None:
			return None
		temp1 = button.get_label()
		for _ in range(1, times+1):
			button.set_label((color, temp1))
			RenderClass.loop.draw_screen()
			time.sleep(0.1)
			button.set_label(temp1)
			RenderClass.loop.draw_screen()
			time.sleep(0.1)
		return None

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

		# Remove file after downloading
		if ControlClass.delete_after_download is True:
			journal.warning(f"[YTCON] REMOVING {ControlClass.queue_list[temp1_index]['file']}...")
			os.remove(ControlClass.queue_list[temp1_index]["file"])
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

				errorr = i["status"] == "error"

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

			# - = Delete after download = -
			if text in ("dad", "delete after download"):
				ControlClass.delete_after_download_switch()
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
			if not to_render[:-3]:
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
		# - = skip, do not re-render if it doesn't change - = - = - =
		# if ControlClass.oldlog == ControlClass.log:
		#	time.sleep(0.5)
		#	continue
		# else:
		#	ControlClass.oldlog = ControlClass.log.copy()
		#
		# controlclass snippet:
		# self.oldlog = ["", "", "", "", "", ""]
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
	""" It just checks some conditions every few seconds and executes them. Directly not responsible for rendering, but changes some buttons color """

	# - = - = - = - = - = - = - = - = -
	# Autopaste button color changer
	if (settings.get_setting("clipboard_autopaste") is True and ControlClass.clipboard_checker_state_launched is not True) or (settings.get_setting("clipboard_autopaste") is False and ControlClass.clipboard_checker_state_launched is not False):
		main_footer_buttons.contents[2] = (urwid.AttrMap(main_footer_clipboard_autopaste_button, "yellow"), main_footer_buttons.contents[2][1])
		ControlClass.temp["autopaste_button_color"] = "yellow" # some kind of cache
	elif ControlClass.clipboard_checker_state_launched is not True and ControlClass.temp["autopaste_button_color"] != "light_red":
		main_footer_buttons.contents[2] = (urwid.AttrMap(main_footer_clipboard_autopaste_button, "light_red"), main_footer_buttons.contents[2][1])
		ControlClass.temp["autopaste_button_color"] = "light_red" # some kind of cache
	elif ControlClass.clipboard_checker_state_launched is True and ControlClass.temp["autopaste_button_color"] != "buttons_footer":
		main_footer_buttons.contents[2] = (urwid.AttrMap(main_footer_clipboard_autopaste_button, "buttons_footer"), main_footer_buttons.contents[2][1])
		ControlClass.temp["autopaste_button_color"] = "buttons_footer" # some kind of cache
	# - = - = - = - = - = - = - = - = -

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
	# Settings page show handler
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

	# - = - = - = - = - = - = - = - = -
	# GET LATEST VERSION NUMBER FROM PYPI
	if RenderClass.tried_check_pypi_version is False:
		#print("Check updates.. :)")
		try:
			import requests
			RenderClass.pypi_version = requests.get("https://pypi.org/pypi/ytcon/json", timeout=20).json()["info"]["version"]
		except:
			pass

		textt = f"Your YTCON version: {RenderClass.version} (from {RenderClass.install_source}) / Actual YTCON version: {RenderClass.pypi_version}"

		if RenderClass.version == "?.?.?" or RenderClass.pypi_version == "?.?.?":
			settings_version_text.set_text((RenderClass.yellow, textt))
		elif RenderClass.version == RenderClass.pypi_version:
			settings_version_text.set_text((RenderClass.green, textt))
		elif RenderClass.version != RenderClass.pypi_version:
			if RenderClass.install_source == "pip":
				textt = textt + "\n\nUpdate using pipx or pip:\n - pipx upgrade ytcon\n OR\n - pip3 install -U ytcon\n"
			if RenderClass.install_source == "git":
				textt = textt + "\n\nUpdate using git:\n - git clone https://github.com/NikitaBeloglazov/ytcon\n"

			settings_version_text.set_text((RenderClass.red, textt))
	# - = - = - = - = - = - = - = - = -

	# Prevent focus from remaining on footer buttons after pressing them
	main_footer.set_focus(input_widget)
	# - =
	loop.set_alarm_in(0.3, tick_handler)

def clipboard_checker():
	"""
	Checks the clipboard for new entries against old ones.
	If it sees new material on the clipboard, it will check whether this is a site, if it detects site, download starts
	""" # TODO: move to tick_handler?
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

			new_clip = pyperclip.paste() # TODO change paste method
			if new_clip != old_clip:
				if re.fullmatch(r"(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", new_clip):
					journal.info("[CLIP] New URL detected: " + new_clip)
					threading.Thread(target=downloadd, args=(new_clip,), daemon=True).start()
				else:
					logger.debug(new_clip)
					journal.info("[CLIP] New content detected. But this is not URL. Ignoring..")
			old_clip = new_clip
			time.sleep(1)
	except pyperclip.PyperclipException:
		logger.debug(traceback.format_exc())
		journal.error("[YTCON] pyperclip module says your platform is unsupported (android?). Turning off Clipboard auto-paste..")
		settings.write_setting("clipboard_autopaste", False)
		update_checkboxes()
		ControlClass.clipboard_checker_state_launched = False
		return None
	except:
		exit_with_exception(str(traceback.format_exc()))
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

RenderClass = RenderClass_base()
# - = - = -
# YTCON VERSION CHECKER
import importlib.util

try:
	# Trying to use relative paths to look at __version__
	from .__version__ import __version__
	RenderClass.version = __version__
	RenderClass.install_source = "pip"
except:
	pass

if RenderClass.version == "!!{PLACEHOLDER}!!" or RenderClass.version == "?.?.?":
	try:
		# Find the directory in which the ytcon startup file is located
		ytcon_files_path = os.path.abspath(__file__).replace("yt.py", "")

		# Try to load __version__.py from the directory where ytcon is located
		spec = importlib.util.spec_from_file_location("version", ytcon_files_path + "__version__.py")
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		RenderClass.version = module.__version__
	except:
		pass

if RenderClass.version == "!!{PLACEHOLDER}!!" or RenderClass.version == "?.?.?":
	try:
		# Use GIT to check tags, makes sense if git clone was used to install
		tag = subprocess.check_output(f'git -C "{ytcon_files_path}" describe --tags', shell=True, encoding="UTF-8")

		# Formating it a little
		# v0.0.11-3-g0ada3b4 -->> 0.0.11
		tag = tag.replace("\n", "").replace("v", "")
		if tag.find("-") > 1:
			tag = tag[0:tag.find("-")]

		RenderClass.version = tag
		RenderClass.install_source = "git"
	except:
		pass

#print(RenderClass.version) # TODO CLEAN TRASH
#print(RenderClass.install_source)
#print(RenderClass.pypi_version)
#input(">> ")
# - = - = -
ControlClass = ControlClass_base()

ControlClass.ydl_opts = {
	'logger': journal,
	'progress_hooks': [hook],
	'color': 'no_color',
	#'outtmpl': '%(title)s [%(id)s].%(ext)s', # REALIZED IN own file handler
	'socket_timeout': 15,
	'retries': 20,
	'fragment_retries': 40,
	'retry_sleep': 'http,fragment:exp',
	#'download_archive': 'downloaded_videos.txt', # !!! DANGEROUS OPTION !!! # TODO?
	'ignoreerrors': True # !!! DANGEROUS OPTION !!! # Don't exit if there is private video in playlist
	}

top_pile = urwid.Pile([])

#logger.debug(pprint.pformat(top_pile.contents))
#logger.debug(pprint.pformat(calculate_widget_height(top_pile)))

log_widget = urwid.Text("Initializing, please wait")
error_widget = urwid.Text("Initializing, please wait")
input_widget = InputHandler.InputBox("Enter URL > ")

main_settings_button = urwid.Button("Settings", on_press=settings.show_settings_call)
main_clear_button = urwid.Button("Clear", on_press=ControlClass.clear)
main_footer_clipboard_autopaste_button = urwid.Button("Autopaste", on_press=settings.clipboard_autopaste_switch)

main_footer_buttons = urwid.GridFlow([main_settings_button, main_clear_button, main_footer_clipboard_autopaste_button], cell_width=13, h_sep=2, v_sep=1, align="left")
logger.debug(main_footer_buttons.contents)
main_footer_buttons_with_attrmap = urwid.AttrMap(main_footer_buttons, "buttons_footer")

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
def update_checkboxes():
	""" Update the state of the checkboxes to setting state, for prevention telling wrong info """
	settings_checkbox_clipboard.set_state(settings.get_setting("clipboard_autopaste"), do_callback=False)
	settings_checkbox_sp.set_state(settings.get_setting("special_mode"), do_callback=False)
	settings_checkbox_delete_af.set_state(ControlClass.delete_after_download, do_callback=False)

settings_checkbox_clipboard = urwid.CheckBox("Clipboard auto-paste", on_state_change=settings.clipboard_autopaste_switch)
settings_checkbox_sp = urwid.CheckBox("Special mode", on_state_change=settings.special_mode_switch)
settings_checkbox_delete_af = urwid.CheckBox((RenderClass.red, "Delete after download"), on_state_change=ControlClass.delete_after_download_switch)
update_checkboxes()

settings_pile = urwid.Pile([
	urwid.Divider(),
	settings_checkbox_clipboard,
	urwid.Divider(),
	settings_checkbox_sp,
	urwid.Divider(),
	settings_checkbox_delete_af,
	urwid.Divider(),
])

# Filler container to center Pile vertically
settings_filler = urwid.Filler(settings_pile, valign='top')

# Wrap content in urwid.Padding with 4 character padding on each side
settings_padding = urwid.Padding(settings_filler, left=4, right=4, align='center')

header_widget = urwid.AttrMap(urwid.Padding(urwid.Text(" - = Settings = - "), align='center'), 'reversed')

exit_settings_button = urwid.AttrMap(urwid.Button("Exit from settings", on_press=settings.show_settings_call), "reversed")

save_settings_button = urwid.Button("Save to config file", on_press=settings.save)
load_settings_button = urwid.Button("Load from config file", on_press=settings.load)

footer_buttons = urwid.GridFlow([exit_settings_button, save_settings_button, load_settings_button], cell_width=25, h_sep=2, v_sep=1, align="left")

settings_version_text = urwid.Text("YTCON version: " + RenderClass.version)

footer_widget = urwid.Pile([
	error_widget,
	urwid.Text("- - -"),
	log_widget,
	urwid.Text("- - -"),
	settings_version_text,
	footer_buttons
])

settings_widget = urwid.Frame(settings_padding, header=header_widget, footer=footer_widget)
# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - =

custom_palette = [
	# ('name_of_style', 'color_text', 'color_background')
	('reversed', 'standout', ''),
	('buttons_footer', 'light green', ''),
	('light_red', 'light red', ''),
	('yellow', 'yellow', ''),
]

loop = urwid.MainLoop(main_widget, palette=custom_palette)

RenderClass.width, RenderClass.height = loop.screen.get_cols_rows()
RenderClass.loop = loop

# - = - = - = - = - = - = -
# Some debug info writer
logger.debug("width: %s", RenderClass.width)
logger.debug("height: %s", RenderClass.height)
logger.debug("config path: %s", configpath)

# Output collected to-later-print logs
for i in logs_that_will_be_printed_later:
	journal.info(i)
# - = - = - = - = - = - = -

settings.load()

loop.set_alarm_in(0, render_tasks)
loop.set_alarm_in(0, logprinter)
loop.set_alarm_in(0, errorprinter)
loop.set_alarm_in(0, tick_handler)

# for testing purposes?
# threading.Thread(target=downloadd, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

loop.run()
