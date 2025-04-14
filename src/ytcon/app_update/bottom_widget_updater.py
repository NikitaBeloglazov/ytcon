from widgets.main_widgets import widgets
from render.colors import colors

from settings.settings_processor import settings

from app_update.variables import app_updates

def update(loop, _):
	if settings.get_setting("show_updates_bottom_sign") is False:
		widgets.bottom_separator.set_text("- - -")
		loop.set_alarm_in(60, update)
	else:
		if app_updates.new_version_available is True:
			widgets.bottom_separator.set_text(["- - -\n", (colors.cyan, f"New update ({app_updates.version} > {app_updates.pypi_version}) is avalible! Go to \"Update Status\" for information")])
		loop.set_alarm_in(10, update)
