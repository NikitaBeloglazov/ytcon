"""
 * Main init part of app

 * - = - = - =
 * Copyright (C) 2023-2024 Nikita Beloglazov <nnikita.beloglazov@gmail.com>
 *
 * This file is part of github.com/NikitaBeloglazov/ytcon.
 *
 * NikitaBeloglazov/ytcon is free software; you can redistribute it and/or
 * modify it under the terms of the Mozilla Public License 2.0
 * published by the Mozilla Foundation.
 *
 * NikitaBeloglazov/ytcon is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY.
 *
 * You should have received a copy of the Mozilla Public License 2.0
 * along with NikitaBeloglazov/ytcon
 * If not, see https://mozilla.org/en-US/MPL/2.0.
"""

import os
import sys

import urwid

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
	logs_that_will_be_printed_later.append("[YTCON] /tmp folder is unavalible (windows, android?). Set current dir for logs")
	log_folder = ""
# - = - = - = - = - = - = - = - = - = - = - = - = - = - =

from log import init_logger, journal, logger
init_logger(log_folder)

#from control.control import ControlClass
from control.variables import variables
#from control.exit import exit_with_exception, traceback

from render.colors import colors
#from render.progressbar_defs import progressbar_defs
from render.render import render
from render.loop import loop_container
RenderClass = render

from widgets.main_widgets import widgets

from settings.settings_processor import settings

#from settings_menu.variables import settings_menu_variables
from settings_menu.render import sett #, settings_sections

#from app_update import app_updates

#from misc.ffmpeg import get_resolution_ffprobe
from misc.clipboard import clipboard_init#, clipboard_checker

#from downloader.main import downloader
from downloader.hook import hook

# - = - = -

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

# TODO LIST:
# 'ratelimit': 207200
#
# Angry mode
# 'retries': float("inf"),
# 'fragment_retries': 999\
#
# Desktop notifications

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
	clipboard_init()
# - = - = - = - = - = - = - = - = - = - = - = -

from loops import render_tasks
from loops import log_printer
from loops import error_printer

from loops import tick_handlers

loop_container.loop.set_alarm_in(0, render_tasks.render_tasks)
loop_container.loop.set_alarm_in(0, log_printer.log_printer)
loop_container.loop.set_alarm_in(0, error_printer.error_printer)

loop_container.loop.set_alarm_in(0, tick_handlers.tick_handler)
loop_container.loop.set_alarm_in(1, tick_handlers.tick_handler_big_delay)
loop_container.loop.set_alarm_in(1, sett.tick_handler_settings)

# for testing purposes?
# threading.Thread(target=downloader, args=("https://www.youtube.com/watch?v=Kek5Inz-wjQ",), daemon=True).start()

loop_container.loop.run()
