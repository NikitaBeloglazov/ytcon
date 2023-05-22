import os
import time
import logging
import threading
import pprint
import curses
from colorama import init, Fore
init()
import yt_dlp

# - = logging init - = - = - = - = - = - = - = - = - = - = - = - =
logger = logging.getLogger('main_logger')
logger.setLevel(logging.DEBUG)

# Create handler for the INFO level
info_file_handler = logging.FileHandler('info.log', mode='w')
info_file_handler.setLevel(logging.INFO)

# Create handler for the DEBUG level
debug_file_handler = logging.FileHandler('debug.log', mode='w')
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

def name_shortener(name):
	""" Shortens filenames so they fit in the console. rewrite required """
	splitted = name.split()
	temp1 = []
	for i in splitted:
		if len(" ".join(temp1) + " " + i) > 10:
			return " ".join(temp1)[0:-1].strip() + "...   "
		temp1.append(i)
	return "Unknown name"

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

class ErrorLogger:
	def debug(self, msg):
		if msg.startswith('[debug] '):
			logger.debug(msg)
		else:
			self.info(msg)
	def info(self, msg):
		logger.info(msg)
	def warning(self, msg):
		logger.warning(msg)
	def error(self, msg):
		logger.error(msg)

class ControlClass:
	def __init__(self):
		pass

def hook(d):
	if d["info_dict"]["extractor"] == "youtube":
		indexx = d["info_dict"]["original_url"] + ":" + d["info_dict"]["format_id"]
	else:
		indexx = d["info_dict"]["original_url"]

	ControlClass.queue_list[indexx]["file"] = d["info_dict"]['_filename']
	if ControlClass.queue_list[indexx]["status"] == "exists" and d['status'] == "finished":
		return None
	ControlClass.queue_list[indexx]["status"] = d['status']
	ControlClass.queue_list[indexx]["progress"] = d["_percent_str"].strip()
	ControlClass.queue_list[indexx]["speed"] = d["_speed_str"].strip()

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

	#if d['status'] == 'downloading':
	#	print(d['eta']) # TODO

	# DEBUG
	# os.system("clear")
	# print(f"\b{ControlClass.progress} {progressbar_generator(ControlClass.progress)} {ControlClass.speed} {ControlClass.site} | {ControlClass.name}")
	# printraw(d)
	# time.sleep(20)
	logger.debug(pprint.pformat(d))
	return None

ydl_opts = {
	'logger': ErrorLogger(),
	'progress_hooks': [hook],
	'no_color': True,
	'outtmpl': '%(title)s [%(id)s].%(ext)s'
	}

def downloadd(url):
	try:
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
					ControlClass.queue_list[temp1_index]["filename"] = infolist["fulltitle"]
					ControlClass.queue_list[temp1_index]["quality"] = i["resolution"]
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
				ControlClass.queue_list[temp1_index]["filename"] = infolist["fulltitle"]
				ControlClass.queue_list[temp1_index]["quality"] = "None"
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
		ControlClass.screen.addstr(ControlClass.screen_height-2, 0, str(e))
		ControlClass.screen.refresh()
		return None

	# - = - = - = [Post-processing] = - = - = - #
	if ControlClass.queue_list[temp1_index]["progress"] == "Exist":
		return None # skip post-process if file already exists
	# Removes Last-modified header. Repeats --no-mtime functionality which is not present in yt-dlp embeded version
	os.utime(ControlClass.queue_list[temp1_index]["file"])

	# Remove file after downloading for testing purposes
	# os.remove(ControlClass.queue_list[temp1_index]["file"])
	return None

#threading.Thread(target=downloadd, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

def main(stdscr):
	ControlClass.screen = stdscr
	curses.echo()
	curses.curs_set(1)
	threading.Thread(target=input_url, args=(stdscr,), daemon=True).start()
	while True:
		if not ControlClass.queue_list: # if ControlClass.queue_list == {}
			stdscr.addstr(0, 0, "No tasks")
		else:
			r = 0
			for _, i in ControlClass.queue_list.items():
				temp1 = f'{whitespace_stabilization(i["progress"], 7)}{progressbar_generator(i["progress"])} {i["speed"]} {bettersize(i["downloaded"])}/{bettersize(i["size"])} {i["site"]} | {name_shortener(i["filename"])}'
				if i["status"] == "waiting":
					stdscr.addstr(r, 0, temp1, curses.color_pair(3))
				elif i["status"] == "exists":
					stdscr.addstr(r, 0, temp1, curses.color_pair(4))
				elif i["status"] == "finished":
					stdscr.addstr(r, 0, temp1, curses.color_pair(2))
				else:
					stdscr.addstr(r, 0, temp1)
				r = r+1
			stdscr.addstr(7, 0, str(ControlClass.queue_list))
		stdscr.refresh()
		time.sleep(0.1)

def input_url(stdscr):
	# Получение размеров окна
	height, width = stdscr.getmaxyx()
	ControlClass.screen_height, ControlClass.screen_width = height, width

	while True:
		# Создание и настройка окна для текстового поля
		textwin = curses.newwin(1, width, height-1, 0)
		textwin.addstr(0, 0, "Введите текст: ")

		# Получение ввода от пользователя
		text = textwin.getstr(0, len("Введите текст: "))

		stdscr.addstr(height-2, 0, "Вы ввели: " + text.decode('utf-8'))
		stdscr.refresh()
		if text.decode('utf-8') == "":
			stdscr.refresh()
		else:
			threading.Thread(target=downloadd, args=(text.decode('utf-8'),), daemon=True).start()

ControlClass.queue_list = {}
# Инициализация curses и вызов основной функции
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