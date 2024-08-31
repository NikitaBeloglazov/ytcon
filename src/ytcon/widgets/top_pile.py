""" Contains top_pile with widgets, which used by loops.render_tasks, for indicating current downloads """
import urwid

class Widgets_TopPile_Basic:
	""" Contains top_pile with widgets, which used by loops.render_tasks, for indicating current downloads """
	def __init__(self):
		self.top_pile = urwid.Pile([])

widgets_tp = Widgets_TopPile_Basic()
