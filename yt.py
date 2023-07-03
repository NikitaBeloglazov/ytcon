import os
import sys
import re
import time
import logging
import threading
import traceback
import pprint
import curses
import pyperclip
import ffmpeg # https://kkroening.github.io/ffmpeg-python/ # python310-ffmpeg-python
# import notify2
from colorama import init, Fore
init()
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

def printraw(printraw_msg):
	""" Outputs pretty-print json """
	print(Fore.CYAN)
	pprint.pprint(printraw_msg)
	print(Fore.RESET)

def name_shortener(name, symbols):
	""" Shortens filenames so they fit in the console """
	if len(name) < symbols:
		return name
	return name[0:symbols-3] + "..."

def divide_without_remainder(num):
	"""
	Division without remainder. Used for centering in the whitespace_stabilization function
		print(divide(22))  # Out: [11, 11]
		print(divide(23))  # Out: [11, 12]
	"""
	quotient = num // 2
	remainder = num % 2
	return [quotient, quotient + remainder]

def whitespace_stabilization(text, needed_space):
	if len(text) == needed_space:
		return text
	if len(text) > needed_space:
		return text[0:needed_space-2] + ".."
	white_space = needed_space - len(text)
	white_space = divide_without_remainder(white_space)
	return ' '*white_space[0] + text + ' '*white_space[1]

def bettersize(text):
	""" Rounds up file sizes """
	if text == "NaN":
		return "NaN"
	if len(text.split(".")) == 1:
		return text
	return text.split(".")[0] + text[-3:-1] + text[-1]

def progressbar_generator(percent):
	""" Generates progress bar """
	if percent == "Wait":
		return f"|{' '*25}|"
	if percent == "Exist":
		return f"|{'█'*25}|"
	percent = int(percent.split(".")[0])
	progress = round(percent / 4)
	white_space = 25 - progress
	return f"|{'█'*progress}{' '*white_space}|"

class JournalClass:
	def debug(self, msg):
		""" For yt-dlp """
		if msg.startswith('[debug] '):
			logger.debug(msg)
		else:
			self.info(msg)

	# show: show in logs field
	def info(self, msg, show=True):
		logger.info(msg)
		if show:
			self.add_to_logs_field(msg)
	def warning(self, msg, show=True):
		logger.warning(msg)
		if show:
			self.add_to_logs_field(msg)
	def error(self, msg, show=True):
		logger.error(msg)
		ControlClass.last_error = msg
		ControlClass.error_countdown = 99
		if show:
			self.add_to_logs_field(msg)

	def clear_errors(self):
		ControlClass.last_error = "No errors:)"
		ControlClass.error_countdown = 0

	def add_to_logs_field(self, msg):
		if "[download]" in msg and "%" in msg and "at" in msg:
			# awoid logging such as "[download] 100.0% of   52.05MiB at    3.07MiB/s ETA 00:00"
			return None

		del ControlClass.log[0]
		msg = msg.replace("\n", "")
		if len(msg) > ControlClass.screen_width:
			temp1 = ControlClass.screen_width - 3
			ControlClass.log.append(msg[0:temp1]+"...")
		else:
			ControlClass.log.append(msg)
		# logger.debug(ControlClass.log)
		return None

journal = JournalClass()

class ControlClass_base:
	def __init__(self):
		self.last_error = "No errors:)"
		self.error_countdown = 0
		self.log = ["", "", "", "", "", "Logs will appear there.."]
		self.exit = False
		self.exception = ""
		self.special_mode = False
		self.clipboard_checker_state = True
		self.clipboard_checker_state_launched = False

def hook(d):
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
			logger.debug("DOWNBYTES: " + str(d["downloaded_bytes"]))
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
			return None
		ControlClass.queue_list[indexx]["status"] = d["status"]
		ControlClass.queue_list[indexx]["progress"] = d["_percent_str"].strip()
		ControlClass.queue_list[indexx]["speed"] = d["_speed_str"].strip()

		try:
			ControlClass.queue_list[indexx]["eta"] = d["_eta_str"].strip()
		except KeyError:
			if d["status"] == "finished":
				ControlClass.queue_list[indexx]["eta"] = "00:00"

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

		# DEBUG
		# os.system("clear")
		# print(f"\b{ControlClass.progress} {progressbar_generator(ControlClass.progress)} {ControlClass.speed} {ControlClass.site} | {ControlClass.name}")
		# printraw(d)
		# time.sleep(20)

		logger.debug(pprint.pformat(ControlClass.queue_list))
		return None
	except:
		exit_with_exception(traceback.format_exc())

def downloadd(url):
	try:
		if url in ControlClass.queue_list:
			if ControlClass.queue_list[url]["status"] not in ("exists", "finished"):
				journal.error(f"[YTCON] Video link \"{name_shortener(url, 40)}\" is already downloading!")
				return None

		with yt_dlp.YoutubeDL(ControlClass.ydl_opts) as ydl:
			logger.debug(str(ydl.params))
			# needed for some sites. you may need to replace it with the correct one
			if ControlClass.special_mode:
				ydl.params["http_headers"]["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
			# - = - = - = Get downloading resolutions (yt) and generate filename (global) = -
			infolist = ydl.extract_info(url, download=False)

			# - = - = - log spam filter - = - = - = - =
			if "automatic_captions" in infolist:
				del infolist["automatic_captions"]
			if "formats" in infolist:
				del infolist["formats"]
			if "thumbnails" in infolist:
				del infolist["thumbnails"]
			logger.debug(pprint.pformat(infolist))
			# - = - = - = - = - = - = - = - = - = - = -

			if "_type" in infolist:
				if infolist["_type"] == "playlist":
					journal.error("[YTCON] SORRY, PLAYLISTS CURRENTLY UNSUPPORTED") # TODO
					return None

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
			if multiple_formats:
				ControlClass.queue_list[infolist["original_url"]] = {}
				ControlClass.queue_list[infolist["original_url"]]["meta_index"] = True
				ControlClass.queue_list[infolist["original_url"]]["multiple_formats"] = True
				ControlClass.queue_list[infolist["original_url"]]["formats"] = []
				ControlClass.queue_list[infolist["original_url"]]["status"] = "waiting"
				for i in infolist["requested_formats"]:
					temp1_index = infolist["original_url"] + ":" + i["format_id"]
					ControlClass.queue_list[infolist["original_url"]]["formats"].append(i["format_id"])
					ControlClass.queue_list[temp1_index] = {}
					ControlClass.queue_list[temp1_index]["progress"] = "Wait"
					ControlClass.queue_list[temp1_index]["speed"] = "0KiB/s"
					try:
						ControlClass.queue_list[temp1_index]["size"] = str(round(i["filesize"]/1e+6)) + "MiB"
					except KeyError:
						ControlClass.queue_list[temp1_index]["size"] = "???MiB"
					ControlClass.queue_list[temp1_index]["downloaded"] = "0MiB"
					ControlClass.queue_list[temp1_index]["eta"] = "??:??"
					ControlClass.queue_list[temp1_index]["name"] = infolist["fulltitle"]
					if i["resolution"] == "audio only":
						ControlClass.queue_list[temp1_index]["resolution"] = "audio"
					else:
						if i.get("width", None) is None and i["height"] is None:
							ControlClass.queue_list[temp1_index]["resolution"] = "???х???"
						else:
							ControlClass.queue_list[temp1_index]["resolution"] = (str(i.get("width", None)) + "x" + str(i["height"])).replace("None", "???")
					ControlClass.queue_list[temp1_index]["site"] = infolist["extractor"].lower()
					ControlClass.queue_list[temp1_index]["status"] = "waiting"
					ControlClass.queue_list[temp1_index]["file"] = filename
			else:
				temp1_index = infolist["original_url"]
				ControlClass.queue_list[temp1_index] = {}
				ControlClass.queue_list[temp1_index]["progress"] = "Wait"
				ControlClass.queue_list[temp1_index]["speed"] = "0KiB/s"
				try:
					ControlClass.queue_list[temp1_index]["size"] = str(round(infolist["filesize_approx"]/1e+6)) + "MiB"
				except KeyError:
					ControlClass.queue_list[temp1_index]["size"] = "???MiB"
				ControlClass.queue_list[temp1_index]["downloaded"] = "0MiB"
				ControlClass.queue_list[temp1_index]["eta"] = "??:??"
				ControlClass.queue_list[temp1_index]["name"] = infolist["fulltitle"]
				if infolist.get("width", None) is None and infolist["height"] is None:
					ControlClass.queue_list[temp1_index]["resolution"] = "???х???"
				else:
					ControlClass.queue_list[temp1_index]["resolution"] = (str(infolist.get("width", None)) + "x" + str(infolist["height"])).replace("None", "???")
				ControlClass.queue_list[temp1_index]["site"] = infolist["extractor"].lower()
				ControlClass.queue_list[temp1_index]["status"] = "waiting"
				ControlClass.queue_list[temp1_index]["file"] = filename

			if exists:
				ControlClass.queue_list[infolist["original_url"]]["status"] = "exists"
				if multiple_formats:
					for i in infolist["requested_formats"]:
						temp1_index = infolist["original_url"] + ":" + i["format_id"]
						ControlClass.queue_list[temp1_index]["status"] = "exists"
						ControlClass.queue_list[temp1_index]["downloaded"] = ControlClass.queue_list[temp1_index]["size"]
						ControlClass.queue_list[temp1_index]["progress"] = "Exist"
				else:
					ControlClass.queue_list[temp1_index]["downloaded"] = ControlClass.queue_list[temp1_index]["size"]
					ControlClass.queue_list[temp1_index]["progress"] = "Exist"
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

def main(stdscr):
	ControlClass.screen = stdscr
	curses.echo()
	curses.curs_set(1)

	threading.Thread(target=input_url, args=(stdscr,), daemon=True).start()
	threading.Thread(target=errorprinter, daemon=True).start()
	threading.Thread(target=logprinter, daemon=True).start()
	# for testing purposes
	# threading.Thread(target=downloadd, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

	while True:
		# Exit with exception
		if ControlClass.exit:
			curses.endwin()
			ControlClass.screen = None
			print(ControlClass.exception)
			sys.exit(1)
		# Clipboard auto-paste starter
		if ControlClass.clipboard_checker_state == True and ControlClass.clipboard_checker_state_launched is not True:
			threading.Thread(target=clipboard_checker, daemon=True).start()
		# removes old text with help of spaces, as curses doesn't do that..
		clear_old_text = " " * ((ControlClass.screen_height - 12) * ControlClass.screen_width)
		stdscr.addstr(0, 0, clear_old_text)
		# # #

		if not ControlClass.queue_list: # if ControlClass.queue_list == {}
			stdscr.addstr(0, 0, "No tasks")
		else:
			r = 0
			for _, i in ControlClass.queue_list.items():
				if "meta_index" in i:
					continue # just ignore meta-downloads
				temp1 = f'{whitespace_stabilization(i["progress"], 7)}{progressbar_generator(i["progress"])}{whitespace_stabilization(i["speed"], 13)}|{whitespace_stabilization(bettersize(i["downloaded"])+"/"+bettersize(i["size"]), 15)}| ETA {i["eta"]} | {whitespace_stabilization(i["site"], 7)} | {whitespace_stabilization(i["resolution"], 9)} | '
				fileshortname = name_shortener(i["name"], ControlClass.screen_width - len(temp1))
				temp1 = temp1 + fileshortname
				if i["status"] == "waiting":
					stdscr.addstr(r, 0, temp1, curses.color_pair(3))
				elif i["status"] == "exists":
					stdscr.addstr(r, 0, temp1, curses.color_pair(4))
				elif i["status"] == "finished":
					stdscr.addstr(r, 0, temp1, curses.color_pair(2))
				else:
					stdscr.addstr(r, 0, temp1)
				r = r+1
			# stdscr.addstr(7, 0, str(ControlClass.queue_list))
		stdscr.refresh()
		time.sleep(0.1)

class InputProcessed(Exception):
	""" Dummy exception, when called means that the processing of this request is completed and need to start a new one. """

def input_url(stdscr):
	# Get window sizes
	height, width = stdscr.getmaxyx()
	ControlClass.screen_height, ControlClass.screen_width = height, width

	while True:
		try:
			# Create and setting window for text field
			textwin = curses.newwin(1, width, height-1, 0)
			textwin.addstr(0, 0, "Enter URL > ")

			# Get user input
			text = textwin.getstr(0, len("Enter URL > "))
			text = text.decode('utf-8')

			# stdscr.addstr(height-2, 0, "You entered: " + text)
			# stdscr.refresh()

			if text == "":
				# Force refreshing screen...
				stdscr.refresh()
				raise InputProcessed

			journal.info("")
			journal.info("[input] " + text)

			# - = Special mode handler = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			if text in ("sp", "specialmode"):
				journal.info("[input] specialmode status: " + str(ControlClass.special_mode))
				raise InputProcessed

			if text == "sp1":
				text = "specialmode 1"
			elif text == "sp0":
				text = "specialmode 0"

			if text.split()[0] == "specialmode" or text.split()[0] == "sp":
				if text.split()[1] == "1" or text.split()[1].lower() == "true":
					ControlClass.special_mode = True
					ControlClass.ydl_opts["cookiesfrombrowser"] = ('chromium', ) # needed for some sites with login only access. you may need to replace it with the correct one
					journal.info("[YTCON] sp activated! now a different user agent will be used, and cookies will be retrieved from chromium")
				elif text.split()[1] == "0" or text.split()[1].lower() == "false":
					ControlClass.special_mode = False
					if "cookiesfrombrowser" in ControlClass.ydl_opts:
						del ControlClass.ydl_opts["cookiesfrombrowser"]
					journal.info("[YTCON] sp deactivated! now a default yt-dlp extractor settings will be used.")
				else:
					journal.error("[YTCON] I do not understand you")
				raise InputProcessed
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
			# - = Clipboard auto-paste status handler = - = - = - = - = - = - = - = - = - = - = - = - = - = - =
			if text in ("cb", "clipboard"):
				journal.info("[YTCON] Clipboard auto-paste status: " + str(ControlClass.clipboard_checker_state) + ", launched state: " + str(ControlClass.clipboard_checker_state_launched))
				raise InputProcessed

			if text == "cb1":
				text = "clipboard 1"
			elif text == "cb0":
				text = "clipboard 0"

			if text.split()[0] == "clipboard" or text.split()[0] == "cb":
				if text.split()[1] == "1" or text.split()[1].lower() == "true":
					if ControlClass.clipboard_checker_state == True:
						journal.info("[YTCON] Already enabled.")
					ControlClass.clipboard_checker_state = True
				elif text.split()[1] == "0" or text.split()[1].lower() == "false":
					if ControlClass.clipboard_checker_state == False:
						journal.info("[YTCON] Already disabled.")
					ControlClass.clipboard_checker_state = False
				else:
					journal.error("[input] I do not understand you")
				raise InputProcessed
			# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

			elif text in ("clear", "cls"):
				journal.clear_errors()
				temp1 = delete_finished()
				journal.info(f"[clear] {temp1} item(s) removed from list!")

			elif text == "logtest":
				time.sleep(1)
				logger.debug("[TEST] 1")
				time.sleep(1)
				journal.info("[TEST] 2")
				time.sleep(1)
				journal.warning("[TEST] 3")
				time.sleep(1)
				journal.error("[TEST] 4")
				time.sleep(1)
				journal.error("[TEST] 5", show=False)
				time.sleep(1)
				journal.info("😘😘😘😘 6") # can break something, emojis have problems calculating sizes
				time.sleep(1)

			elif text == "makecrash":
				try:
					0/0
				except:
					exit_with_exception(traceback.format_exc())

			else:
				threading.Thread(target=downloadd, args=(text,), daemon=True).start()
		except InputProcessed:
			pass
		except:
			exit_with_exception(traceback.format_exc())

def errorprinter():
	max_error_space = ControlClass.screen_width * 3
	try:
		while True:
			ControlClass.screen.addstr(ControlClass.screen_height-5, 0, "- - -")
			ControlClass.screen.refresh()

			if ControlClass.last_error == "ERROR: kwallet-query failed with return code 1. Please consult the kwallet-query man page for details":
				ControlClass.error_countdown = 0
				journal.clear_errors()

			if ControlClass.error_countdown != 0:
				error_text_generator = "[" + whitespace_stabilization(str(ControlClass.error_countdown), 2) + "] " + str(ControlClass.last_error)
			else:
				error_text_generator = str(ControlClass.last_error)

			error_text_generator = error_text_generator.replace("; please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U", "")

			# avoid situations when the text goes beyond the window due to too long url
			if len(error_text_generator) > ControlClass.screen_width*3 - 5:
				error_text_generator = error_text_generator[0:(ControlClass.screen_width*3 - 5)]
			# - = - = - = - = -

			error_text_generator = error_text_generator + (" " * (max_error_space - len(error_text_generator)))

			if ControlClass.last_error == "No errors:)":
				ControlClass.screen.addstr(ControlClass.screen_height-4, 0, error_text_generator, curses.color_pair(3))
				ControlClass.screen.refresh()
			else:
				ControlClass.screen.addstr(ControlClass.screen_height-4, 0, error_text_generator, curses.color_pair(1))
				ControlClass.screen.refresh()

			if ControlClass.error_countdown != 0:
				ControlClass.error_countdown = ControlClass.error_countdown - 1
				if ControlClass.error_countdown == 0:
					journal.clear_errors()
			time.sleep(1)
	except:
		exit_with_exception(traceback.format_exc())

def logprinter():
	ControlClass.screen.addstr(ControlClass.screen_height-12, 0, "- - -")
	ControlClass.screen.refresh()
	temp1 = " "*ControlClass.screen_width
	try:
		while True:
			# if old_logs == new_logs: skip, do not re-render # TODO
			# removes old text with help of spaces, as curses doesn't do that..
			ControlClass.screen.addstr(ControlClass.screen_height-11, 0, temp1)
			ControlClass.screen.addstr(ControlClass.screen_height-10, 0, temp1)
			ControlClass.screen.addstr(ControlClass.screen_height-9,  0, temp1)
			ControlClass.screen.addstr(ControlClass.screen_height-8,  0, temp1)
			ControlClass.screen.addstr(ControlClass.screen_height-7,  0, temp1)
			ControlClass.screen.addstr(ControlClass.screen_height-6,  0, temp1)
			# # #

			ControlClass.screen.addstr(ControlClass.screen_height-11, 0, ControlClass.log[0])
			ControlClass.screen.addstr(ControlClass.screen_height-10, 0, ControlClass.log[1])
			ControlClass.screen.addstr(ControlClass.screen_height-9,  0, ControlClass.log[2])
			ControlClass.screen.addstr(ControlClass.screen_height-8,  0, ControlClass.log[3])
			ControlClass.screen.addstr(ControlClass.screen_height-7,  0, ControlClass.log[4])
			ControlClass.screen.addstr(ControlClass.screen_height-6,  0, ControlClass.log[5])
			ControlClass.screen.refresh()
			time.sleep(0.2)
	except:
		exit_with_exception(traceback.format_exc())

def delete_finished():
	""" Removes all completed operations from ControlClass.queue_list with a loop """
	#try:
	temp1 = 0
	temp2_new = ControlClass.queue_list.copy()
	for item, item_content in ControlClass.queue_list.copy().items():
		if item_content["status"] == "exists" or item_content["status"] == "finished":
			del temp2_new[item]
			if "meta_index" not in item_content:
				temp1 = temp1 + 1
	ControlClass.queue_list = temp2_new
	logger.debug(ControlClass.queue_list)
	return str(temp1)
	#except:
	#	exit_with_exception(traceback.format_exc())

def clipboard_checker():
	ControlClass.clipboard_checker_state_launched = True
	journal.info("[YTCON] Clipboard auto-paste is ON.")

	new_clip = pyperclip.paste()
	if re.fullmatch(r"(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", new_clip):
		journal.info("[CLIP] URL detected: " + new_clip)
		threading.Thread(target=downloadd, args=(new_clip,), daemon=True).start()
	old_clip = new_clip

	while True:
		if ControlClass.clipboard_checker_state == False:
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
		time.sleep(0.5)

def exit_with_exception(text): # TODO connect to all functions
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
ControlClass.queue_list = {}

ControlClass.ydl_opts = {
	'logger': journal,
	'progress_hooks': [hook],
	'no_color': True,
	#'outtmpl': '%(title)s [%(id)s].%(ext)s', # REALIZED IN own file handler
	'socket_timeout': 15,
	#'restrictfilenames': True
	'trim_file_name': 150,
	'retries': 20,
	'fragment_retries': 40,
	'retry_sleep': 'http,fragment:exp'
	}

# Init screen
curses.update_lines_cols()
curses.initscr()

# Init colors
curses.start_color()
curses.use_default_colors()

curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

# curses.raw() # TODO: ??? can simplify some points in the program
# Start
curses.wrapper(main)
