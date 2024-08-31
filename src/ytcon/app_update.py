""" DEPRECATED: WILL BE DELETED AND REWORKED IN THE FUTURE """
# TODO: delete auto-update, rework detection func

import os
import sys
import time
import pprint
import importlib
import traceback
import threading
import subprocess

import urwid
import requests

from log import journal, logger
from control.variables import variables
from render.colors import colors

class UpdateAndVersionsClass:
	""" The class stores everything related to determining the version number and auto-updates """
	def __init__(self):
		self.version = "?.?.?"
		self.install_source = "???"
		self.pypi_version = "?.?.?"

		self.auto_update_avalible = False

		self.get_pypi_version_new_thread()
		self.version, self.install_source = self.check_version()

		# Widget from settings that shows versions
		self.settings_version_text = urwid.Text((colors.yellow, f"Your YTCON version: {self.version} / Newest YTCON version: *Working..*"))

		# Variables that cannot have initial values but need to be declared
		self.update_thread = None

	def check_version(self):
		""" Tries to determine the installation method. Sometimes using some external tools """
		version = "?.?.?"
		install_source = "???"
		try:
			# Trying to use relative paths to look at __version__
			from .__version__ import __version__ # pylint: disable=import-outside-toplevel
			version = __version__

			# Understand by which tool is it installed
			if os.path.abspath(__file__).find("pipx") > 0:
				install_source = "pipx"
			else:
				# TODO ADD VENV DETECTION
				install_source = "pip"
		except:
			pass

		if version in ("!!{PLACEHOLDER}!!", "?.?.?"):
			try:
				# Find the directory in which the ytcon startup file is located
				ytcon_files_path = os.path.abspath(__file__).replace("app_update.py", "")

				# Try to load __version__.py from the directory where ytcon is located
				spec = importlib.util.spec_from_file_location("version", ytcon_files_path + "__version__.py")
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				version = module.__version__
			except:
				pass

		if version in ("!!{PLACEHOLDER}!!", "?.?.?"):
			try:
				# Use GIT to check tags, makes sense if git clone was used to install
				tag = subprocess.check_output(f'git -C "{ytcon_files_path}" describe --tags', shell=True, encoding="UTF-8")

				# Formating it a little
				# v0.0.11-3-g0ada3b4 -->> 0.0.11
				tag = tag.replace("\n", "").replace("v", "")
				if tag.find("-") > 1:
					tag = tag[0:tag.find("-")]

				version = tag
				install_source = "git"
			except:
				pass

		if version == "!!{PLACEHOLDER}!!":
			version = "?.?.?"
		return version, install_source

	def get_pypi_version(self):
		""" Get newest version number via PyPI public API """
		try:
			temp1 = requests.get("https://pypi.org/pypi/ytcon/json", timeout=20).json()
			logger.debug(pprint.pformat(temp1))
			self.pypi_version = temp1["info"]["version"]
			#self.pypi_version = "0.0.14"
		except:
			logger.debug(traceback.format_exc())

	def get_pypi_version_new_thread(self):
		""" Just starts a new thread self.get_pypi_version. Made for not to slow down GUI or utility launch """
		threading.Thread(target=self.get_pypi_version, daemon=True).start()

	def update_settings_version_text(self):
		""" Class that generates text for the widget settings_version_text """
		textt = f"Your YTCON version: {self.version} (from {self.install_source}) / Actual YTCON version: {self.pypi_version}"

		if self.version == "?.?.?" or self.pypi_version == "?.?.?":
			self.settings_version_text.set_text((colors.yellow, textt))
		elif self.version == self.pypi_version:
			self.settings_version_text.set_text((colors.green, textt))
		elif self.version != self.pypi_version:
			if self.install_source == "pipx":
				#textt = textt + "\n\nUpdate using pipx:\n - pipx upgrade ytcon\n"
				self.auto_update_avalible = True
			if self.install_source == "pip":
				textt = textt + "\n\nUpdate using pip:\n - pip3 install -U ytcon\n"
			if self.install_source == "git":
				#textt = textt + "\n\nUpdate using git:\n - `git pull` in folder with ytcon\n"
				self.auto_update_avalible = True

			if self.auto_update_avalible is True:
				textt = textt + "\n[!!] Auto update is avalible! Write \"update\" in input field to easy update right now!\n"
			self.settings_version_text.set_text((colors.light_red, textt))

	def get_update_command(self):
		""" A function that stores commands for updating """
		if self.install_source == "pipx":
			return "pipx upgrade ytcon"
		if self.install_source == "git":
			ytcon_files_path = os.path.abspath(__file__).replace("app_update.py", "")
			return f"git -C {ytcon_files_path} pull"
		if self.install_source == "pip":
			journal.error("[YTCON] Auto update is not avalible for pip installation type")
			return None
		if self.install_source == "???":
			journal.error("[YTCON] Auto update is not avalible - Unable to determine your installation type")
			return None
		#else:
		journal.error("[YTCON] Auto update is not avalible - No update instructions found for your installation type")
		return None

	def update_run_and_restart(self):
		""" Starts auto-update """
		update_command = self.get_update_command()
		if update_command is None:
			return None
		variables.auto_update_safe_gui_stop = True
		time.sleep(1)
		print("\n- = - =\nThe following command will run in 10 seconds:")
		print(" - " + update_command)
		print("\nCtrl+C to cancel update.")
		time.sleep(10)
		print("- = - =\n>> " + update_command + "\n")
		status_code = os.system(update_command)
		if status_code == 0:
			print("\n- = - =\nUpdate was completed successfully! YTCON will restart itself..")
			restart_command = sys.executable + " " + " ".join(sys.argv)
			print(" - " + restart_command)
			print("\nCtrl+C to cancel restart.")
			time.sleep(5)
			print("- = - =\n>> " + restart_command + "\n")
			os.system(restart_command)
		else:
			print("\n- = - =\nIt looks like the update failed. See the output above for details.\nYTCON has not been updated.")
		return None

app_updates = UpdateAndVersionsClass()
