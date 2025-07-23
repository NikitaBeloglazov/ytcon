import sys
sys.path.append("..")
from settings_plugins import dynamic_modules
# - = - = -

class MainClass():
	title = "Lorem ipsum dolor sit amet"
	description = "Integer tristique lectus quis luctus dapibus.\nVestibulum sit amet egestas sem. Sed lobortis semper enim et varius"
	section = "Cookies"

	savename = "yt-dlp.loresipisum"

	widget_type = "input_field"

	if_enabled = "cock"
	# if_disabled = None

	verify_input = "ignore"
	verify_input_data = None

# - = - = -
dynamic_modules.register(MainClass)

