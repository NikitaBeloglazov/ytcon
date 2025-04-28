"""
	The module that is responsible for outputting the string undew input line
	New update {app_updates.version} > {app_updates.pypi_version} is avalible! Go to "Update Status" for information
"""
from widgets.main_widgets import widgets
from render.colors import colors

from settings.settings_processor import settings

from app_update.variables import app_updates

def update(loop, _):
	""" A loop for display a sign about new available updates. """
	if settings.get_setting("show_updates_bottom_sign") is False:
		widgets.bottom_separator.set_text("- - -")
		loop.set_alarm_in(60, update) # For optimization lol
	else:
		if app_updates.new_version_available is True:
			widgets.bottom_separator.set_text(["- - -\n", (colors.cyan, f"New update ({app_updates.version} > {app_updates.pypi_version}) is avalible! Go to \"Update Status\" for information")])
		elif app_updates.new_version_available is False:
			widgets.bottom_separator.set_text("- - -") # This can create some issues if some other code rewrites this widget
		loop.set_alarm_in(10, update)
