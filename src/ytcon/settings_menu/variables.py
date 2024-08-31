""" A container with some shared variables for settings menu """

class SettingsMenuVariables:
	""" A container with some shared variables for settings menu """
	def __init__(self):
		self.settings_show = False
		self.settings_showed = False

		self.settings_soft_update_scheduled = False

settings_menu_variables = SettingsMenuVariables()
