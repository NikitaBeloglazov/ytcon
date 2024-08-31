"""
	This module stores some information about rendering, screen,
	some functions for working with widgets
	and some functions that are related to rendering.
"""
import os
import urwid

#from widgets.main_widgets import widgets
from widgets.top_pile import widgets_tp

class RenderClass:
	""" It stores some information about rendering, screen, some functions for working with widgets and some functions that are related to rendering. """
	def __init__(self):
		# We need to have some numbers for initializing,
		# but loop_container.loop.screen.get_cols_rows() is not ready.
		# so i use os.get_terminal_size(0) for some numbers to init.
		self.width, self.height = os.get_terminal_size(0)

	def add_row(self, text):
		""" Add an additional widget to top_pile for drawing a new task """
		widgets_tp.top_pile.contents = widgets_tp.top_pile.contents + [[urwid.Text(text), widgets_tp.top_pile.options()],]

	def edit_or_add_row(self, text, pos):
		""" Edit a widget with a specific serial number, and if there is none, then create a new one """
		if pos > self.calculate_widget_height(widgets_tp.top_pile) - 1:
			self.add_row(text)
		else:
			widgets_tp.top_pile.contents[pos][0].set_text(text)

	#def remove_all_widgets(self):
	#	- = + DEPRECATED + = -
	#	USE widgets_tp.top_pile.contents = [] UNSTEAD
	#
	#	"""
	#	If there are obsolete widgets in top_pile that will not be changed, they are considered garbage,
	#	for this you need to call remove_all_widgets, all widgets, including unnecessary old ones,
	#	will be removed, but will be recreated if needed
	#	"""
	#	widgets_tp.top_pile.contents = []

	def calculate_widget_height(self, widget):
		""" (recursively) Counts how many rows the widget occupies in height """
		if isinstance(widget, urwid.Text):
			# Returns the number of lines of text in the widget
			return len(widget.text.split('\n'))
		if isinstance(widget, urwid.Pile):
			# Recursively sums the heights of widgets inside a urwid.Pile container
			return sum(self.calculate_widget_height(item[0]) for item in widget.contents)
		return 0 # Return 0 for unsupported widget types (?)

render = RenderClass()
