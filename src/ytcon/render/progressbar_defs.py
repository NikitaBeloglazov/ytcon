""" This module contains methods for drawing progress bars """
import time
from tqdm import tqdm

from settings.settings_processor import settings

class ProgressBarDefs:
	""" Minor methods mostly needed by render_tasks """
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
			return f"|{'#'*progress}{' '*white_space}|"

		style = settings.get_setting("progressbar_appearance")

		if style == "detailed":
			return tqdm.format_meter(percent, 100, 0, ascii=False, bar_format="|{bar}|", ncols=27, mininterval=0, maxinterval=0)

		if style == "simple":
			return f"|{'█'*progress}{' '*white_space}|"

		if style == "arrow":
			temp1 = '='*progress
			if temp1 != "":
				temp1 = temp1[:-1] + ">" # replace last symbol to >
			return f"|{temp1}{' '*white_space}|"

		if style == "pacman":
			# [---------Co o o o o o o ]
			#            ^ background ^

			mseconds = time.time() - round(time.time())
			if mseconds > 0: # pylint: disable=simplifiable-if-statement # no, because bool(-1) is True
				mystery_bool = True
			else:
				mystery_bool = False

			progressline = '-'*progress
			if progress not in (0, 25):
				if mystery_bool:
					progressline = progressline[:-1] + "C" # replace last symbol to c
				else:
					progressline = progressline[:-1] + "c" # replace last symbol to C

			# Skip background generation if this not needed
			if progress == 25:
				return f"[{progressline}]"

			# - = Background generation = -
			if progress % 2:
				background = "o"
			else:
				background = " "

			while len(background) != white_space:
				if background[-1] == " ":
					background = background + "o"
				else:
					background = background + " "
			# - = - = - = - = - = - = - = -
			return f"[{progressline}{background[:white_space]}]"
		return None

progressbar_defs = ProgressBarDefs()
