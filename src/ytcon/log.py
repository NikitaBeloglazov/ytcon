"""
	A log wrapper for yt-dlp and a logging class for the whole application.
	info, warning and error will be added to the logs field. (logprinter())
	For debug messages it is highly recommended to use logger.debug instead of journal
"""

import logging
from control.variables import variables

from render.render import render

logger = logging.getLogger('main_logger')
def init_logger(log_folder):
	"""
	Logger initialization. Made because imports cannot have argument funcionality,
	Because we can't check log folder in log.py, and it must be detected in yt.py
	"""
	# - = logging init - = - = - = - = - = - = - = - = - = - = - = - =
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
		variables.last_error = msg
		variables.error_countdown = 99
		if show:
			self.add_to_logs_field(msg)
		return None

	def clear_errors(self, _=None):
		""" Clear the errorprinter() field """
		variables.last_error = ""
		variables.error_countdown = 0

	def add_to_logs_field(self, msg):
		""" there logs will be added to the logprinter() field. """
		msg = str(msg).replace("\n", "")
		if "[download]" in msg and "%" in msg and "at" in msg:
			# awoid logging such as "[download] 100.0% of   52.05MiB at    3.07MiB/s ETA 00:00"
			return None

		del variables.log[0]

		# TODO: loops.log_printer must cut log messages, not logger. current version is cruel shit
		if len(msg) > render.width:
			temp1 = render.width - 3
			variables.log.append(msg[0:temp1]+"...")
		else:
			variables.log.append(msg)
		# logger.debug(variables.log)
		return None

journal = JournalClass()
