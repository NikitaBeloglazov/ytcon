# - = Standart modules = -
import os
import re
import sys
import time
import pprint
import threading
import traceback
# - = - = - = - = - = - = -
import urwid

import clipman
#import notify2

debug_that_will_be_saved_later = []
logs_that_will_be_printed_later = []

# - = CHECK SYSTEM PATHS - = - = - = - = - = - = - = - =
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
	logs_that_will_be_printed_later.append("[YTCON] /tmp folder is unavalible (windows, android?). setting current dir for logs..")
	log_folder = ""
# - = - = - = - = - = - = - = - = - = - = - = - = - = - =

from log import journal, logger

from control.variables import variables
from control.exit import exit_with_exception, traceback

from render.colors import colors
from render.progressbar_defs import progressbar_defs
from render.render import render
from render.loop import loop_container
RenderClass = render

from widgets.main_widgets import widgets

from settings.settings_processor import settings

#from settings_menu.variables import settings_menu_variables
from settings_menu.render import sett #, settings_sections

from app_update import app_updates

from misc.ffmpeg import get_resolution_ffprobe

from downloader.main import downloader

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
		if "multiple_formats" in variables.queue_list[d["info_dict"]["original_url"]]:
			indexx = d["info_dict"]["original_url"] + ":" + d["info_dict"]["format_id"]
		else:
			indexx = d["info_dict"]["original_url"]

		# - = - resolution detector - = - = - = - = - = - = - = - = - = -
		if variables.queue_list[indexx]["resolution"].find("???") > -1 and (variables.queue_list[indexx].get("resolution_detection_tried_on_byte", 0) + 4000000) < int(d.get("downloaded_bytes", 0)) and variables.queue_list[indexx].get("resolution_detection_tries", 0) < 5:
			# int(d["downloaded_bytes"]) > 4000000 # if the file size is too smol, it does not have the needed metadata and ffprobe gives an error
			logger.debug("DOWNBYTES: %s", str(d["downloaded_bytes"]))
			temp1 = get_resolution_ffprobe(d["tmpfilename"])
			temp2 = str(variables.queue_list[indexx].get("resolution_detection_tries", 0)+1)

			if temp1 is not None:
				variables.queue_list[indexx]["resolution"] = temp1
				journal.info(f"[YTCON] Detected resolution: {temp1} (on try {temp2})" )
			else:
				journal.warning(f'[YTCON] Resolution detection failed: ffprobe gave an error (try {temp2})')
			variables.queue_list[indexx]["resolution_detection_tried_on_byte"] = int(d["downloaded_bytes"])
			variables.queue_list[indexx]["resolution_detection_tries"] = variables.queue_list[indexx].get("resolution_detection_tries", 0) + 1
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

		variables.queue_list[indexx]["file"] = d["info_dict"]['_filename']
		if variables.queue_list[indexx]["status"] == "exists" and d["status"] == "finished":
			return None # i'll guess it's made to avoid bugs that overwriting some data
		variables.queue_list[indexx]["status"] = d["status"]

		if int(d["_percent_str"].strip().split(".")[0]) > 100:
			journal.warning("[YTCON] yt-dlp returned percent more than 100%: \"" + d["_percent_str"].strip() + "\". Values remain unchanged...")
		else:
			variables.queue_list[indexx]["status_short_display"] = d["_percent_str"].strip()
			variables.queue_list[indexx]["percent"] = d["_percent_str"].strip()
		variables.queue_list[indexx]["speed"] = d["_speed_str"].strip()

		try:
			if variables.queue_list[indexx]["eta"].count(":") > 1:
				variables.queue_list[indexx]["eta"] = d["_eta_str"].strip()
			else:
				variables.queue_list[indexx]["eta"] = "ETA " + d["_eta_str"].strip()
		except KeyError:
			if d["status"] == "finished":
				variables.queue_list[indexx]["eta"] = "ETA 00:00"

		try:
			if d["_total_bytes_estimate_str"].strip() == "N/A":
				variables.queue_list[indexx]["size"] = d["_total_bytes_str"].strip()
			else:
				variables.queue_list[indexx]["size"] = d["_total_bytes_estimate_str"].strip()
		except KeyError:
			pass

		try:
			variables.queue_list[indexx]["downloaded"] = d["_downloaded_bytes_str"].strip()
		except:
			pass

		d["info_dict"]["formats"] = []
		d["info_dict"]["thumbnails"] = []
		d["info_dict"]["subtitles"] = []
		d["info_dict"]["fragments"] = []

		logger.debug(pprint.pformat(variables.queue_list))
	except:
		exit_with_exception(traceback.format_exc())

def render_tasks(loop, _):
	"""
	Graphic part of ytcon - draws a colored video queue from variables.queue_list
	Shows names, extractors, ETAs, generates progress bars, etc.
	"""
	try:
		if not variables.queue_list: # if variables.queue_list == {}
			RenderClass.edit_or_add_row((colors.cyan, "No tasks"), 0)
		else:
			r = 0
			for _, i in variables.queue_list.items():
				if "meta_index" in i:
					continue # just ignore meta-downloads

				rcm = progressbar_defs
				ws = rcm.whitespace_stabilization

				errorr = i["status"] == "error"

				temp1 = f'{ws(i["status_short_display"], 7)}{rcm.progressbar_generator(i["percent"], errorr)}{ws(i["speed"], 13)}|{ws(rcm.bettersize(i["downloaded"])+"/"+rcm.bettersize(i["size"]), 15)}| {ws(i["eta"], 9)} | {ws(i["site"], 7)} | {ws(i["resolution"], 9)} | '
				fileshortname = rcm.name_shortener(i["name"], RenderClass.width - len(temp1))
				temp1 = temp1 + fileshortname

				if i["status"] == "waiting":
					RenderClass.edit_or_add_row((colors.cyan, temp1), r)
				elif i["status"] == "error":
					RenderClass.edit_or_add_row((colors.red, temp1), r)
				elif i["status"] == "exists":
					RenderClass.edit_or_add_row((colors.yellow, temp1), r)
				elif i["status"] == "finished":
					RenderClass.edit_or_add_row((colors.green, temp1), r)
				else:
					RenderClass.edit_or_add_row(temp1, r)

				r = r+1
		loop.set_alarm_in(0.3, render_tasks)
	except:
		exit_with_exception(traceback.format_exc())

def errorprinter(loop, _):
	""" Draws errors in widgets.error_widget in red, after some time (specified in the timer) removes error messages """
	try:
		# - = skip, do not re-render if there is no errors - = - = - = - = -
		# if variables.prev_last_error == variables.last_error and variables.prev_error_countdown == variables.error_countdown:
		#	time.sleep(0.6)
		#	continue
		# - = - = - = - = - = - = - = - = - = - = - = - = - - = - = - = -
		to_render = []
		to_render.append("- - -\n")

		if variables.error_countdown != 0:
			error_text_generator = "[" + progressbar_defs.whitespace_stabilization(str(variables.error_countdown), 2) + "] " + str(variables.last_error)
		else:
			error_text_generator = str(variables.last_error)

		error_text_generator = error_text_generator.replace("; please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U", "")

		if variables.last_error == "":
			to_render.append((colors.cyan, error_text_generator))
		else:
			to_render.append((colors.red, error_text_generator))

		to_render.append("\n")

		# - = - = - = - = - = - unfold animation - = - = - = - = - = -
		if RenderClass.errorprinter_animation == 0:
			widgets.error_widget.set_text(to_render)
		elif RenderClass.errorprinter_animation == 1:
			widgets.error_widget.set_text(to_render[:-1])
		elif RenderClass.errorprinter_animation == 2:
			if to_render[:-2] == ["- - -\n"]:
				widgets.error_widget.set_text("- - -")
			else:
				widgets.error_widget.set_text(to_render[:-2])
		elif RenderClass.errorprinter_animation == 3:
			if not to_render[:-3]:
				widgets.error_widget.set_text("")
			else:
				widgets.error_widget.set_text(to_render[:-3])

		if variables.last_error == "":
			if RenderClass.errorprinter_animation < 3 and RenderClass.errorprinter_animation >= 0:
				RenderClass.errorprinter_animation += 1
		else:
			if RenderClass.errorprinter_animation <= 3 and RenderClass.errorprinter_animation > 0:
				RenderClass.errorprinter_animation = RenderClass.errorprinter_animation - 1
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

		variables.prev_last_error = variables.last_error
		variables.prev_error_countdown = variables.error_countdown

		if variables.error_countdown != 0:
			variables.error_countdown = variables.error_countdown - 1
			if variables.error_countdown == 0:
				journal.clear_errors()

		#widgets.error_widget.set_text(to_render)
		loop.set_alarm_in(0.3, errorprinter)
	except:
		exit_with_exception(str(traceback.format_exc()))

def logprinter(loop, _):
	""" Prints the last 6 lines of logs in widgets.log_widget """
	try:
		# - = skip, do not re-render if it doesn't change - = - = - =
		# if ControlClass.oldlog == variables.log:
		#	time.sleep(0.5)
		#	continue
		# else:
		#	ControlClass.oldlog = variables.log.copy()
		#
		# controlclass snippet:
		# self.oldlog = ["", "", "", "", "", ""]
		# - = - = - = - = - = - = - = - = - = - = - = - = - - = - = - =

		to_render = variables.log[0] + "\n"
		to_render += variables.log[1] + "\n"
		to_render += variables.log[2] + "\n"
		to_render += variables.log[3] + "\n"
		to_render += variables.log[4] + "\n"
		to_render += variables.log[5]
		widgets.log_widget.set_text(to_render)

		loop.set_alarm_in(0.3, logprinter)
	except:
		exit_with_exception(traceback.format_exc())

def tick_handler(loop, _):
	""" It just checks some conditions every few seconds and executes them. Directly not responsible for rendering, but changes some buttons color """

	# - = - = - = - = - = - = - = - = -
	# Autopaste button color changer
	if (settings.get_setting("clipboard_autopaste") is True and variables.clipboard_checker_state_launched is not True) or (settings.get_setting("clipboard_autopaste") is False and variables.clipboard_checker_state_launched is not False):
		widgets.main_footer_buttons.contents[2] = (urwid.AttrMap(widgets.main_footer_clipboard_autopaste_button, "yellow"), widgets.main_footer_buttons.contents[2][1])
		variables.temp["autopaste_button_color"] = "yellow" # some kind of cache
	elif variables.clipboard_checker_state_launched is not True and variables.temp["autopaste_button_color"] != "light_red":
		widgets.main_footer_buttons.contents[2] = (urwid.AttrMap(widgets.main_footer_clipboard_autopaste_button, "light_red"), widgets.main_footer_buttons.contents[2][1])
		variables.temp["autopaste_button_color"] = "light_red" # some kind of cache
	elif variables.clipboard_checker_state_launched is True and variables.temp["autopaste_button_color"] != "buttons_footer":
		widgets.main_footer_buttons.contents[2] = (urwid.AttrMap(widgets.main_footer_clipboard_autopaste_button, "buttons_footer"), widgets.main_footer_buttons.contents[2][1])
		variables.temp["autopaste_button_color"] = "buttons_footer" # some kind of cache
	# - = - = - = - = - = - = - = - = -

	# - = Clipboard thread activator = -
	if settings.get_setting("clipboard_autopaste") and variables.clipboard_checker_state_launched is False:
		threading.Thread(target=clipboard_checker, daemon=True).start()
	# - = - = - = - = - = - = - = - = -

	# - = - = - = - = - = - = - = - = -
	# The error handler, if it sees variables.exit = True,
	# then exits the program commenting this with the text from variables.exception.
	# The parent function of such actions: exit_with_exception()
	if variables.exit is True:
		loop.stop()
		print("An unknown error has occurred!\n")
		time.sleep(0.5)
		print(variables.exception)
		sys.exit(1)

	if variables.auto_update_safe_gui_stop is True:
		try:
			loop.stop()
		except:
			journal.debug(traceback.format_exc())

		try:
			app_updates.update_thread.join()
		except KeyboardInterrupt:
			print(" - Okay, canceled")
		sys.exit()
	# - = - = - = - = - = - = - = - = -

	# Prevent focus from remaining on footer buttons after pressing them
	widgets.main_footer.set_focus(widgets.input_widget)

	# - =
	loop.set_alarm_in(0.3, tick_handler)

def tick_handler_big_delay(loop, _):
	""" Same as tick_handler, but with bigger delay. Made for optimization purposes. """

	# - = - = - = - = - = - = - = - = -
	# Draw version in settings
	app_updates.update_settings_version_text()

	# New-update-avalible notificator
	if app_updates.auto_update_avalible is True:
		widgets.auto_update_avalible_text_indicator.set_text((colors.cyan, f"- - -\nAuto update {app_updates.version} -> {app_updates.pypi_version} is avalible! Write \"update\" to easy update right now!"))
	# - = - = - = - = - = - = - = - = -

	# - =
	loop.set_alarm_in(4, tick_handler_big_delay)

url_regex = r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$"
def clipboard_checker():
	"""
	Checks the clipboard for new entries against old ones.
	If it sees new content on the clipboard, it will check whether this is a site, if it detects site, download starts
	"""

	# Set the button yellow and DO NOT start daemon
	variables.clipboard_checker_state_launched = "Do not start"

	if clipman.dataclass.init_called is False:
		try:
			clipman.init()
		except:
			logger.info(traceback.format_exc())
			journal.error("[YTCON] An error occurred while initializing the clipboard. You can see the error in info.log. Or save the Auto-paste option enabled in the config file, restart ytcon, and after that you will see an error with detailed instructions.")

			# Keep setting ON for "save to config file" ability
			time.sleep(60)
			settings.write_setting("clipboard_autopaste", False)
			update_checkboxes()
			variables.clipboard_checker_state_launched = False
			return None

	try:
		variables.clipboard_checker_state_launched = True
		journal.info("[YTCON] Clipboard auto-paste is ON.")

		old_clip = ""

		while True:
			if settings.get_setting("clipboard_autopaste") is False:
				variables.clipboard_checker_state_launched = False
				journal.info("[YTCON] Clipboard auto-paste turned off.")
				return None

			new_clip = clipman.paste()
			if new_clip != old_clip:
				if re.fullmatch(url_regex, new_clip):
					journal.info("[CLIP] New URL detected: " + new_clip)
					threading.Thread(target=downloader, args=(new_clip,), daemon=True).start()
				else:
					logger.debug("clipboard content: %s", new_clip)
					journal.info("[CLIP] New clipboard content detected. But this is not URL. Ignoring..")
			old_clip = new_clip
			time.sleep(1)
	except:
		exit_with_exception(str(traceback.format_exc()))
		return None

# - = - = -
from control.control import ControlClass

variables.ydl_opts = {
	'logger': journal,
	'progress_hooks': [hook],
	'color': 'no_color',
	#'outtmpl': '%(title)s [%(id)s].%(ext)s', # REALIZED IN own file handler
	'socket_timeout': 15,
	'retries': 20,
	'fragment_retries': 40,
	'retry_sleep': 'http,fragment:exp',
	#'download_archive': 'downloaded_videos.txt', # !!! DANGEROUS OPTION !!! # TODO?
	}

loop_container.loop = urwid.MainLoop(widgets.main_widget, palette=colors.custom_palette)

RenderClass.width, RenderClass.height = loop_container.loop.screen.get_cols_rows()

# - = - = - = - = - = - = -
# Some debug info writer
logger.debug("width: %s", RenderClass.width)
logger.debug("height: %s", RenderClass.height)

# Output collected to-later-print logs
for i in logs_that_will_be_printed_later:
	journal.info(i)
for i in debug_that_will_be_saved_later:
	logger.debug(i)
# - = - = - = - = - = - = -

# - = - = - = - Late initialize - = - = - = - =
settings.load()

if settings.get_setting("clipboard_autopaste") is True:
	try:
		clipman.init()
	except Exception as e: # pylint: disable=broad-except
		logger.info(traceback.format_exc())
		print("[!!] An Clipboard error occurred!\n")
		print(f"- {type(e).__name__}: {e}")
		print("\nYou can follow instructions in this error message, or ignore it")
		print("BUT, if you ignore it, clipboard auto-paste will be unavalible.\n")
		print("Also, if this error message doesn't contain instructions,")
		print("and does not contain any understandable text for your human language, please make an issue")
		print("https://github.com/NikitaBeloglazov/clipman/issues/new")
		print("Full traceback can be found in info.log\n")

		try:
			user_answer = input("Ignore it? [yes/NO] > ")
		except KeyboardInterrupt:
			print("Exiting..")
			sys.exit(1)

		if user_answer.lower() in ("yes", "y"):
			journal.error("[YTCON] If you don't want answer \"yes\" every time, solve the problem, or disable auto-paste in settings and PRESS \"Save to config file\"")
			settings.write_setting("clipboard_autopaste", False)
		else:
			print("Exiting..")
			sys.exit(1)
# - = - = - = - = - = - = - = - = - = - = - = -

loop_container.loop.set_alarm_in(0, render_tasks)
loop_container.loop.set_alarm_in(0, logprinter)
loop_container.loop.set_alarm_in(0, errorprinter)
loop_container.loop.set_alarm_in(0, tick_handler)
loop_container.loop.set_alarm_in(1, tick_handler_big_delay)
loop_container.loop.set_alarm_in(1, sett.tick_handler_settings)

# for testing purposes?
# threading.Thread(target=downloader, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

loop_container.loop.run()
