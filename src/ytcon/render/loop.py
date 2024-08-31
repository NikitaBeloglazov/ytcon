""" LoopContainer - container class that shares iniated loop variable (urwid.MainLoop) """

class LoopContainer:
	"""" LoopContainer - container class that shares iniated loop variable (urwid.MainLoop) """
	def __init__(self):
		self.loop = None

loop_container = LoopContainer()
