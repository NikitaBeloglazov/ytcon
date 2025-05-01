"""
	Graphic part of ytcon - draws a colored video queue from variables.queue_list
	Shows names, extractors, ETAs, generates progress bars, etc.
"""
from control.variables import variables
from control.exit import exit_with_exception, traceback

from render.colors import colors
from render.progressbar_defs import progressbar_defs
from render.render import render

def render_tasks(loop, _):
	"""
	Graphic part of ytcon - draws a colored video queue from variables.queue_list
	Shows names, extractors, ETAs, generates progress bars, etc.
	"""
	try:
		if not variables.queue_list: # if variables.queue_list == {}
			render.edit_or_add_row((colors.cyan, "No tasks"), 0)
		else:
			r = 0
			for _, i in variables.queue_list.items():
				if "meta_index" in i:
					continue # just ignore meta-downloads

				rcm = progressbar_defs
				ws = rcm.whitespace_stabilization

				errorr = i["status"] == "error"

				temp1 = f'{ws(i["status_short_display"], 7)}{rcm.progressbar_generator(i["percent"], errorr)}{ws(i["speed"], 13)}|{ws(rcm.bettersize(i["downloaded"])+"/"+rcm.bettersize(i["size"]), 15)}| {ws(i["eta"], 9)} | {ws(i["site"], 7)} | {ws(i["resolution"], 9)} | '
				fileshortname = rcm.name_shortener(i["name"], render.width - len(temp1))
				temp1 = temp1 + fileshortname

				if i["status"] == "waiting":
					render.edit_or_add_row((colors.cyan, temp1), r)
				elif i["status"] == "error":
					render.edit_or_add_row((colors.red, temp1), r)
				elif i["status"] == "exists":
					render.edit_or_add_row((colors.dark_yellow, temp1), r)
				elif i["status"] == "finished":
					render.edit_or_add_row((colors.green, temp1), r)
				else:
					render.edit_or_add_row(temp1, r)

				r = r+1
		loop.set_alarm_in(0.3, render_tasks)
	except:
		exit_with_exception(traceback.format_exc())
