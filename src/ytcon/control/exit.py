""" Stops the urwid and prints an error message, then exits the program """

import traceback
# TODO: catch traceback by self, like
"""
>>> def lol(): print(traceback.format_exc()); print("yes")
...
>>> try:
...     0/0
... except:
...     lol()
...
Traceback (most recent call last):
File "<stdin>", line 2, in <module>
ZeroDivisionError: division by zero
yes
"""

from log import journal
from control.variables import variables

# TODO: Consider stop by self, using loop_container
def exit_with_exception(text):
	""" Stops the urwid and prints an error message, then exits the program """
	journal.error(text)
	variables.exit = True
	variables.exception = text + "\nPrinted by exit_with_exception()"
