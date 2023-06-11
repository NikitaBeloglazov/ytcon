import os
import sys
import time
import logging
import threading
import traceback
import pprint
import curses
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
		ControlClass.error_countdown = 15
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
		if len(msg) > ControlClass.screen_width:
			temp1 = ControlClass.screen_width - 3
			ControlClass.log.append(msg[0:temp1]+"...")
		else:
			ControlClass.log.append(msg)
		logger.debug(ControlClass.log)

journal = JournalClass()

class ControlClass_base:
	def __init__(self):
		self.last_error = "No errors:)"
		self.error_countdown = 0
		self.log = ["", "", "", "", "", "Logs will appear there.."]
		self.exit = False
		self.exception = ""

def hook(d):
	logger.debug(pprint.pformat(d))
	if d["info_dict"]["extractor"] == "youtube":
		indexx = d["info_dict"]["original_url"] + ":" + d["info_dict"]["format_id"]
	else:
		indexx = d["info_dict"]["original_url"]

	ControlClass.queue_list[indexx]["file"] = d["info_dict"]['_filename']
	if ControlClass.queue_list[indexx]["status"] == "exists" and d["status"] == "finished":
		return None
	ControlClass.queue_list[indexx]["status"] = d['status']
	ControlClass.queue_list[indexx]["progress"] = d["_percent_str"].strip()
	ControlClass.queue_list[indexx]["speed"] = d["_speed_str"].strip()

	#try:
	#	ControlClass.queue_list[indexx]["eta"] = d["_eta_str"].strip()
	#except KeyError:
	#	if d["status"] == "finished":
	#		ControlClass.queue_list[indexx]["eta"] = "00:00"

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
	return None

ydl_opts = {
	'logger': journal,
	'progress_hooks': [hook],
	'no_color': True,
	'outtmpl': '%(title)s [%(id)s].%(ext)s',
	'socket_timeout': 7,
	# 'cookiesfrombrowser': ('chromium', ) # needed for some sites with login only access. you may need to replace it with the correct one
	}

def downloadd(url):
	try:
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			journal.debug(str(ydl.params))
			# needed for some sites. you may need to replace it with the correct one
			# ydl.params["http_headers"]["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
			# - = - = - = Get downloading resolutions (yt) = -
			infolist = ydl.extract_info(url, download=False)
			logger.debug(pprint.pformat(infolist))

			# Check if file exists
			exists = os.path.exists(f'{infolist["title"]} [{infolist["id"]}].{infolist["ext"]}'.replace("|", "｜")) # yt-dlp, wtf?
			if exists:
				logger.warning(f'FILE "{infolist["title"]} [{infolist["id"]}].{infolist["ext"]}" EXISTS'.replace("|", "｜"))

			if infolist["extractor"] == "youtube":
				for i in infolist["requested_formats"]:
					temp1_index = infolist["original_url"] + ":" + i["format_id"]
					ControlClass.queue_list[temp1_index] = {}
					ControlClass.queue_list[temp1_index]["progress"] = "Wait"
					ControlClass.queue_list[temp1_index]["speed"] = "0KiB/s"
					try:
						ControlClass.queue_list[temp1_index]["size"] = str(round(i["filesize"]/1e+6)) + "MiB"
					except KeyError:
						ControlClass.queue_list[temp1_index]["size"] = "???MiB"
					ControlClass.queue_list[temp1_index]["downloaded"] = "0MiB"
					#ControlClass.queue_list[temp1_index]["eta"] = "??:??"
					ControlClass.queue_list[temp1_index]["filename"] = infolist["fulltitle"]
					ControlClass.queue_list[temp1_index]["quality"] = i["resolution"] # TODO
					ControlClass.queue_list[temp1_index]["site"] = infolist["extractor_key"]
					ControlClass.queue_list[temp1_index]["status"] = "waiting"
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
				#ControlClass.queue_list[temp1_index]["eta"] = "??:??"
				ControlClass.queue_list[temp1_index]["filename"] = infolist["fulltitle"]
				ControlClass.queue_list[temp1_index]["quality"] = "None" # TODO
				ControlClass.queue_list[temp1_index]["site"] = infolist["extractor_key"]
				ControlClass.queue_list[temp1_index]["status"] = "waiting"

			if exists:
				if infolist["extractor"] == "youtube":
					for i in infolist["requested_formats"]:
						temp1_index = infolist["original_url"] + ":" + i["format_id"]
						ControlClass.queue_list[temp1_index]["status"] = "exists"
						ControlClass.queue_list[temp1_index]["downloaded"] = ControlClass.queue_list[temp1_index]["size"]
						ControlClass.queue_list[temp1_index]["progress"] = "Exist"
				else:
					ControlClass.queue_list[temp1_index]["status"] = "exists"
					ControlClass.queue_list[temp1_index]["downloaded"] = ControlClass.queue_list[temp1_index]["size"]
					ControlClass.queue_list[temp1_index]["progress"] = "Exist"
			# - = - = - = - = - = - = - = - = - = - = - = - =
			logger.debug(pprint.pformat(ControlClass.queue_list))
			logger.debug(ydl.download(url))
	except yt_dlp.utils.DownloadError as e:
		journal.error(str(e), show=False)
		return None

	# - = - = - = [Post-processing] = - = - = - #
	if ControlClass.queue_list[temp1_index]["progress"] == "Exist":
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
		# removes old text with help of spaces, as curses doesn't do that..
		clear_old_text = " " * ((ControlClass.screen_height - 12) * ControlClass.screen_width)
		stdscr.addstr(0, 0, clear_old_text)
		# # #

		if not ControlClass.queue_list: # if ControlClass.queue_list == {}
			stdscr.addstr(0, 0, "No tasks")
		else:
			r = 0
			for _, i in ControlClass.queue_list.items():
				# Not included flags:
				# - ETA: {i["eta"]}
				temp1 = f'{whitespace_stabilization(i["progress"], 7)}{progressbar_generator(i["progress"])}{whitespace_stabilization(i["speed"], 13)}|{whitespace_stabilization(bettersize(i["downloaded"])+"/"+bettersize(i["size"]), 15)}| {i["site"]} | '
				fileshortname = name_shortener(i["filename"], ControlClass.screen_width - len(temp1))
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
				journal.info("[input] Force refreshing screen...")
				stdscr.refresh()
				raise InputProcessed

			journal.info("")
			journal.info("[input] " + text)

			if text == "clear" or text == "cls":
				journal.clear_errors()
				temp1 = delete_finished()
				journal.info(f"[clear]: {temp1} item(s) removed from list!")
			elif text == "logtest":
				time.sleep(1)
				journal.debug("[TEST] 1")
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

def errorprinter():
	max_error_space = ControlClass.screen_width * 3
	while True:
		ControlClass.screen.addstr(ControlClass.screen_height-5, 0, "- - -")
		ControlClass.screen.refresh()

		if ControlClass.error_countdown != 0:
			error_text_generator = "[" + whitespace_stabilization(str(ControlClass.error_countdown), 2) + "] " + str(ControlClass.last_error)
		else:
			error_text_generator = str(ControlClass.last_error)

		error_text_generator = error_text_generator.replace("; please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U", "")
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

def logprinter():
	ControlClass.screen.addstr(ControlClass.screen_height-12, 0, "- - -")
	ControlClass.screen.refresh()
	temp1 = " "*ControlClass.screen_width
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

def delete_finished():
	""" Removes all completed operations from ControlClass.queue_list with a loop """
	#try:
	temp1 = 0
	temp2_new = ControlClass.queue_list.copy()
	for item, item_content in ControlClass.queue_list.copy().items():
		if item_content["status"] == "exists" or item_content["status"] == "finished":
			del temp2_new[item]
			temp1 = temp1 + 1
	ControlClass.queue_list = temp2_new
	return str(temp1)
	#except:
	#	exit_with_exception(traceback.format_exc())

def exit_with_exception(text): # TODO connect to all functions
	journal.error(text)
	ControlClass.exit = True
	ControlClass.exception = text

ControlClass = ControlClass_base()
ControlClass.queue_list = {}

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

# Start
curses.wrapper(main)
