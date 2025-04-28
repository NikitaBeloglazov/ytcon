"""
	Class for processing user input.
	Contains a modified Urwid.edit widget and functions for processing commands and URLs
"""
import pprint
import traceback
import threading

import urwid

from log import journal, logger
#from render.render import render
from settings_menu.variables import settings_menu_variables
from render.loop import loop_container
from control.variables import variables
from control.control import ControlClass
from control.exit import exit_with_exception, traceback
from settings.settings_processor import settings

from downloader.main import downloader

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
		def is_skipable(self, inp):
			"""
				Determines whether this character can be skipped.
				Used in ALT key handlers to determine whether a character is part of a word
			"""
			if inp.isalpha() or inp.isdigit():# or inp == "%":
				return True
			return False

		def get_cords(self, size):
			"""
				Takes the cursor coordinates from the InputBox to determine which character the cursor is currently on.
				Doesn't work well if the text is muiti-line
			"""
			tmp1 = self.get_cursor_coords(size)[0]
			if len(self.get_cursor_coords(size)) > 1 and self.get_cursor_coords(size)[1] > 0:
				if variables.alt_plus_arrow_multiline_message_sended is False:
					journal.error("[YTCON] Navigation using Alt+Arrow in a multi-line input field does not work as expected, this is a known problem, and we cannot solve it due to the peculiarities of the engine.\n\nNavigation will be inaccurate and skip some characters for no reason.\nWe apologize for the inconvenience caused.")
					variables.alt_plus_arrow_multiline_message_sended = True
				tmp1 = tmp1 * self.get_cursor_coords(size)[1]
				return tmp1
			return tmp1 - 12

		def get_safe_text(self):
			""" Limits the end of the text to avoid infinite recursion """
			return self.get_edit_text() + "??"

		def keypress(self, size, key):
			""" Overrides a regular class. """
			#journal.info(key)

			if key in ('meta left', 'ctrl left'):
				# Alt + Left and Ctrl + Left key handler. Moves left one word
				super().keypress(size, "left")
				temp1 = ""
				# Moves one letter at a time until it finds a special symbol that cannot an part of word
				while self.is_skipable(self.get_safe_text()[self.get_cords(size)-1]):# and self.get_cords(size) > 0:
					endless_loop_detector_first = self.get_cords(size)
					temp1 = temp1 + self.get_safe_text()[self.get_cords(size)-1]
					super().keypress(size, "left")

					# If the coordinates have not changed since the last cursor movement, then the border has been reached
					endless_loop_detector_two = self.get_cords(size)
					if endless_loop_detector_first == endless_loop_detector_two:
						logger.debug("meta left: loop detected")
						break
				return None

			if key in ('meta right', 'ctrl right'):
				# Alt + Right and Ctrl + Right key handler. Moves right one word
				super().keypress(size, "right")
				temp1 = ""
				# Moves one letter at a time until it finds a special symbol that cannot an part of word
				while self.is_skipable(self.get_safe_text()[self.get_cords(size)]):# and self.get_cords(size) > 0:
					endless_loop_detector_first = self.get_cords(size)
					temp1 = temp1 + self.get_safe_text()[self.get_cords(size)]
					super().keypress(size, "right")

					# If the coordinates have not changed since the last cursor movement, then the border has been reached
					endless_loop_detector_two = self.get_cords(size)
					if endless_loop_detector_first == endless_loop_detector_two:
						logger.debug("meta right: loop detected")
						break
				return None

			if key == 'meta backspace':
				# Alt + Backspace key handler. Removes last word in inputbox
				if len(self.get_edit_text()) < 3:
					super().keypress(size, "backspace")
					return None

				temp1 = list(self.get_edit_text())
				temp2 = False
				if self.is_skipable(temp1[-1]):
					temp2 = True
				else:
					if self.is_skipable(temp1[-2]):
						temp2 = True
					del temp1[-1]

				while self.is_skipable(temp1[-1]) and temp2 is True:
					del temp1[-1]
					if len(temp1) == 0:
						break

				self.set_edit_text("".join(temp1))
				return None

			if key == 'enter':
				# If enter pressed, send URL to input_handler and clear inputbox
				InputHandler.input_handler(self.get_edit_text())
				self.set_edit_text("")
				return None

			# If the conditions do not work and the key is not assigned
			return super().keypress(size, key)

	class InputProcessed(Exception):
		""" Dummy exception, when called means that the processing of this request is completed. """

	def input_handler(self, text):
		""" Main input handler logic """
		try:
			original_text = text
			text = text.lower()

			if text == "":
				# Force refreshing screen...
				loop_container.loop.draw_screen()
				raise self.InputProcessed

			journal.info("")
			journal.info("[YTCON] [INPUT] " + original_text)

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

			elif text == "crash":
				try:
					0/0
				except:
					exit_with_exception(traceback.format_exc())

			elif text == "s":
				settings_menu_variables.settings_show = True

			elif text == "flags":
				journal.info(pprint.pformat(variables.ydl_opts))

			elif text == "s ls":
				journal.info(settings.settings)

			elif text == "fake update":
				# For debug purposes, lol
				from app_update.variables import app_updates # pylint: disable=import-outside-toplevel
				app_updates.pypi_version = "9.9.9"
				app_updates.pypi_version_split = (9, 9, 9)
				app_updates.new_version_available = app_updates.check_new_version_available()
				journal.info("PyPI version set to 9.9.9. I wish you good testing:)")

			elif text == "save":
				settings.save()
				#journal.info(settings.settings)
			elif text == "load":
				settings.load()
				#journal.info(settings.settings)

			else:
				threading.Thread(target=downloader, args=(original_text,), daemon=True).start()

		except self.InputProcessed:
			pass
		except:
			exit_with_exception(traceback.format_exc())

InputHandler = InputHandlerClass()
