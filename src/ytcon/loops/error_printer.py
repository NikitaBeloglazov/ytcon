"""
	Draws errors in widgets.error_widget in red
	After some time (specified in the timer) removes error messages
"""

from log import journal

from control.variables import variables
from control.exit import exit_with_exception, traceback

from render.colors import colors
from render.progressbar_defs import progressbar_defs

from widgets.main_widgets import widgets

# - = - = - = - = - = - = - = - = - =
class ErrorPrinterVariables:
	""" Placeholder """
	def __init__(self):
		""" Placeholder """
		self.animation = 3

error_printer_variables = ErrorPrinterVariables()
# - = - = - = - = - = - = - = - = - =

def error_printer(loop, _):
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
		if error_printer_variables.animation == 0:
			widgets.error_widget.set_text(to_render)
		elif error_printer_variables.animation == 1:
			widgets.error_widget.set_text(to_render[:-1])
		elif error_printer_variables.animation == 2:
			if to_render[:-2] == ["- - -\n"]:
				widgets.error_widget.set_text("- - -")
			else:
				widgets.error_widget.set_text(to_render[:-2])
		elif error_printer_variables.animation == 3:
			if not to_render[:-3]:
				widgets.error_widget.set_text("")
			else:
				widgets.error_widget.set_text(to_render[:-3])

		if variables.last_error == "":
			if error_printer_variables.animation < 3 and error_printer_variables.animation >= 0:
				error_printer_variables.animation += 1
		else:
			if error_printer_variables.animation <= 3 and error_printer_variables.animation > 0:
				error_printer_variables.animation = error_printer_variables.animation - 1
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

		variables.prev_last_error = variables.last_error
		variables.prev_error_countdown = variables.error_countdown

		if variables.error_countdown != 0: # TODO: variables.error_countdown might be moved to separate container
			variables.error_countdown = variables.error_countdown - 1
			if variables.error_countdown == 0:
				journal.clear_errors()

		#widgets.error_widget.set_text(to_render)
		loop.set_alarm_in(0.3, error_printer)
	except:
		exit_with_exception(str(traceback.format_exc()))
