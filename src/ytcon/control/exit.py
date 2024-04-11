import traceback

from log import journal
from control.variables import variables

def exit_with_exception(text):
	""" Terminates the pseudo-graphics API and prints an error message, then exits the program """
	journal.error(text)
	variables.exit = True
	variables.exception = text + "\nPrinted by exit_with_exception()"
