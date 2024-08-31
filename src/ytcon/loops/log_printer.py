""" Prints the last 6 lines of logs in widgets.log_widget """
from control.variables import variables
from control.exit import exit_with_exception, traceback

from widgets.main_widgets import widgets

def log_printer(loop, _): # TODO: POSSIBLE, NEEDS REWRITE/BUGFIX. SEE log.py, line 93
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

		loop.set_alarm_in(0.3, log_printer)
	except:
		exit_with_exception(traceback.format_exc())
