""" Two pages in the settings, needed to obtain information and manage self-updates """
import urwid

from render.colors import colors

from settings.settings_processor import settings

from app_update.variables import app_updates
from app_update.updater import update_run_and_restart

class Update_Status_SECTION: # pylint: disable=attribute-defined-outside-init # because get() initializes a class
	"""
	Button section related to self-update feature
	P.S. Previously it was called auto-update, but now it has become self-update, because there was no automatic update in fact)
	"""
	name = "Update Status"
	def get(self):
		""" Get content of section """

		self.version_text = urwid.Text("")
		self.detected_by_text = urwid.Text("")

		self.installation_source_text = urwid.Text("")
		self.auto_update_avalible_text = urwid.Text("     Refresh required")
		self.auto_update_command_text = urwid.Text("")

		self.pypi_version_text = urwid.Text("")
		self.new_version_available_text = urwid.Text("")

		# - = - = Controls
		self.refresh_title = urwid.Text( (colors.cyan, "- Manual refresh") )
		self.refresh_description = urwid.Text("Determine the installed version and the newest on the server.\nIt takes some time to check versions. One request to pypi.org API will be made")
		self.refresh_button = urwid.Button((colors.light_blue, "Refresh now"), on_press=self.refresh_button_pressed)

		self.update_title = urwid.Text( (colors.cyan, "- Self-update") )
		self.update_description = urwid.Text("Temporary unavalible due to: Refresh required")
		self.update_button = urwid.Button((colors.light_red, "Unavalible"))
		# - = - = - = - =

		if app_updates.initialize_called is True:
			self.update()

		settings_pile = urwid.Pile([
			# - = - = - = - =
			urwid.Divider(),
			urwid.Text((colors.bold, "Information")),
			urwid.Divider(),
			self.version_text,
			self.detected_by_text,
			urwid.Divider(),
			self.installation_source_text,
			self.auto_update_avalible_text,
			self.auto_update_command_text,
			urwid.Divider(),
			self.pypi_version_text,
			self.new_version_available_text,
			# - = - = - = - =
			urwid.Divider(),
			urwid.Text((colors.bold, "Controls")),
			urwid.Divider(),
			self.refresh_title,
			self.refresh_description,
			urwid.GridFlow([self.refresh_button], cell_width=15, h_sep=2, v_sep=1, align="left"), # shit but i can't make this in other way
			urwid.Divider(),
			self.update_title,
			self.update_description,
			urwid.GridFlow([self.update_button], cell_width=15, h_sep=2, v_sep=1, align="left"),
			])

		return settings_pile

	def refresh_button_pressed(self, _):
		""" On press, checks for updates including on pypi and updates the page """
		app_updates.initialize()
		self.update()

	def update(self):
		""" Update checkbox states for they don't lie """
		if app_updates.version == "0.0.0":
			self.version_text.set_text("Running version: Unknown")
		else:
			self.version_text.set_text("Running version: " + str(app_updates.version))

		if app_updates.detected_by is None:
			self.detected_by_text.set_text("Detected by algorithm: -")
		else:
			self.detected_by_text.set_text("Detected by algorithm: " + str(app_updates.detected_by))

		if app_updates.pypi_version == "0.0.0" or app_updates.pypi_version is None:
			self.pypi_version_text.set_text("Newest version on PyPI: Unknown")
		else:
			self.pypi_version_text.set_text("Newest version on PyPI: " + str(app_updates.pypi_version))

		if app_updates.install_source is None:
			self.installation_source_text.set_text("Installation source: -")
		else:
			self.installation_source_text.set_text("Installation source: " + str(app_updates.install_source))

		if app_updates.auto_update_avalible is True:
			self.auto_update_avalible_text.set_text( (colors.green, "Self-update availability: " + str(app_updates.auto_update_avalible)) )
		else:
			self.auto_update_avalible_text.set_text( (colors.light_red, "Self-update availability: " + str(app_updates.auto_update_avalible)) )

		if app_updates.auto_update_avalible is not True or app_updates.auto_update_command is None:
			self.auto_update_command_text.set_text("Self-update command: -")
		else:
			self.auto_update_command_text.set_text("Self-update command: " + str(app_updates.auto_update_command))

		if app_updates.new_version_available is True:
			self.new_version_available_text.set_text( (colors.green, "New version available: " + str(app_updates.new_version_available)) )
		else:
			self.new_version_available_text.set_text( (colors.light_red, "New version available: " + str(app_updates.new_version_available)) )

		# - = - = Controls
		if app_updates.auto_update_avalible is True and app_updates.new_version_available is True:
			self.update_description.set_text("[!] Please check the update command above. Detection algorithms can make mistakes.\nAll downloads will be interrupted.")
			self.update_button.set_label((colors.green, "Update now"))
			urwid.connect_signal(self.update_button, 'click', update_run_and_restart)
		elif app_updates.pypi_version is None or app_updates.pypi_version == "0.0.0":
			self.update_description.set_text("Temporary unavalible due to: Unable to check update - PyPI version is None - PyPI is unreachable?")
		elif app_updates.auto_update_avalible is False:
			self.update_description.set_text("Temporary unavalible due to: " + app_updates.auto_update_comment)
		elif app_updates.new_version_available is False:
			self.update_description.set_text("Temporary unavalible due to: Update is not needed - higher versions not found")
		elif app_updates.version == "0.0.0" or app_updates.install_source is None:
			self.update_description.set_text("Temporary unavalible due to: Running version number is invalid or install source is not defined")
		else:
			self.update_description.set_text("Temporary unavalible due to: Unknown reasons. Look at information above for some useful info")

class Update_Settings_SECTION: # pylint: disable=attribute-defined-outside-init # because get() initializes a class
	""" Self-update behavior settings """
	name = "Update Settings"
	def get(self):
		""" Get content of section """

		# - = - = Settings
		self.setting_checkbox_check_updates_on_boot = urwid.CheckBox([(colors.cyan, "Check updates on startup"), "\nDetermine in background the installed version, and check the newest version on the server (one API request to pypi.org)"], on_state_change=settings.setting_switch, user_data="check_updates_on_boot")
		self.setting_checkbox_show_update_bottom_sign = urwid.CheckBox([(colors.cyan, "Notify about new update"), "\nDisplay an message under the input field when new update is found. Requires some time to take effect (10-60 secs)"], on_state_change=settings.setting_switch, user_data="show_updates_bottom_sign")
		# - = - = - = - =

		# UPDATE CHECKBOXES
		self.update()

		settings_pile = urwid.Pile([
			urwid.Divider(),
			urwid.Text((colors.bold, "Settings")),
			urwid.Divider(),
			self.setting_checkbox_check_updates_on_boot,
			urwid.Divider(),
			self.setting_checkbox_show_update_bottom_sign,
			])

		return settings_pile

	def update(self):
		""" Update checkbox states for they don't lie """
		self.setting_checkbox_check_updates_on_boot.set_state(settings.get_setting("check_updates_on_boot"), do_callback=False)
		self.setting_checkbox_show_update_bottom_sign.set_state(settings.get_setting("show_updates_bottom_sign"), do_callback=False)
