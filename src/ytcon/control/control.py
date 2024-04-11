from log import journal, logger
from control.variables import variables
from control.exit import exit_with_exception, traceback

class ControlClass_base:
	""" It stores information about the download queue and some information that must be passed through several functions. """

	def delete_finished(self):
		""" Removes all completed operations from ControlClass.queue_list with a loop """
		try:
			temp1 = 0
			temp2_new = variables.queue_list.copy()
			for item, item_content in variables.queue_list.copy().items():
				if item_content["status"] == "exists" or item_content["status"] == "finished" or item_content["status"] == "error":
					del temp2_new[item]
					if "meta_index" not in item_content:
						temp1 = temp1 + 1
			variables.queue_list = temp2_new
			logger.debug(variables.queue_list)
			RenderClass.remove_all_widgets()
			return str(temp1)
		except:
			exit_with_exception(traceback.format_exc())
		return None

	def clear(self, _=None):
		""" Clears errors and finished downloads from memory """
		journal.clear_errors()
		journal.info(f"[YTCON] {self.delete_finished()} item(s) removed from list!")
		RenderClass.flash_button_text(main_clear_button, RenderClass.light_yellow, 2)

	def delete_after_download_switch(self, _=None, _1=None):
		""" Special mode switch function for urwid.Button's """
		journal.info("")
		if variables.delete_after_download: # true
			variables.delete_after_download = False
			journal.info("[YTCON] Delete after download disabled!")
		elif not variables.delete_after_download: # false
			variables.delete_after_download = True
			journal.error("[YTCON] Delete after download ENABLED! This means that the downloaded files WILL NOT BE SAVED!")

ControlClass = ControlClass_base()
