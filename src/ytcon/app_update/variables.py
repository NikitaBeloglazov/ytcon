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

from shutil import which # for binary detection

import urwid
import requests

#from log import journal, logger
#from control.variables import variables
#from render.colors import colors

class UpdateAndVersionsClass:
	""" The class stores everything related to determining the version number and auto-updates """
	def __init__(self):
		self.version, self.version_tuple, self.detected_by = self.get_version()
		self.install_source = self.get_source()
		self.pypi_version = self.get_pypi_version()

		self.auto_update_avalible = False
		self.auto_update_command = None

		# Widget from settings that shows versions

		# Variables that cannot have initial values but need to be declared
		self.update_thread = None

	def get_version(self):
		"""
		Get installed version number
		outputs: version, version_tuple, detected method
		"""
		# - = - = - = - = - = - = -
		try:
			from __version__ import version, version_tuple # pylint: disable=import-outside-toplevel
			if version != "0.0.0":
				return version, version_tuple, "direct_import"
		except:
			pass
		# - = - = - = - = - = - = -

		# - = git - = - = - = - = - = -
		if which('git') is not None: # if git is installed
			try:
				# Use GIT to check tags, makes sense if git clone was used to install
				ytcon_files_path = os.path.dirname(os.path.realpath(__file__)) # get currently running script path
				tag = subprocess.check_output(('git', '-C', ytcon_files_path, 'describe', '--tags'), encoding="UTF-8")

				# Formating it a little
				# v0.0.11-3-g0ada3b4 -> 0.0.11
				tag = tag.replace("\n", "").replace("v", "")
				if tag.find("-") > 1:
					tag = tag[0:tag.find("-")]

				return tag, tuple(map(int, tag.split('.'))), "git"
				# - - - - - ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ convert to typle like (0, 5, 3)
			except:
				pass
		# - = - = - = - = - = - = -
		return None, None, None # if none is detected


	def get_source(self):
		""" Tries to determine the installation method """

		# - = git - = - = - = - = - = -
		if self.detected_by == "git":
			return "git" # logica :)

		# - = rpm - = - = - = - = - = -
		# if self-writing is not avalible (mostly system installations)
		if os.access(os.path.abspath(__file__), os.W_OK) is False:
			try:
				import rpm # pylint: disable=import-outside-toplevel

				transaction = rpm.TransactionSet() # Init a connection
				results = transaction.dbMatch() # Get all packages
				results.pattern('name', rpm.RPMMIRE_GLOB, '*ytcon*') # pylint: disable=no-member
				# Module 'rpm' has no 'RPMMIRE_GLOB' member -- pylint is actually lying

				if len(list(results)) > 0: # search results and if results more than one
					return "rpm"
			except (ImportError, ModuleNotFoundError):
				print("rpm module not found on this system.")
			except:
				print(traceback.format_exc())

		# - = pipx - = - = - = - = -
		if os.path.abspath(__file__).find("/pipx/venvs") > 0:
			if os.path.isfile(sys.prefix + "/pipx_metadata.json"):
				if which('pipx') is not None: # if pipx is installed
					return "pipx"
				# Manual check by calling pipx, just leave it just in case.
				# import json # for pipx json response parsing
				# try:
				# 	json_output = subprocess.check_output(('pipx', 'list', '--json'), encoding="UTF-8")
				# 	json_output = json.loads(json_output)
				# 	if "ytcon" in json_output["venvs"]:
				# 		return "pipx"
				# except:
				# 	pass

		# - = pip - = - = - = - = -
		if os.path.abspath(__file__).find("/site-packages/ytcon") > 0: # Most likely installed via pip
			if os.path.isfile(sys.prefix + "/pyvenv.cfg"):
				if "VIRTUAL_ENV" in os.environ: # is it not set in pipx
					return "pip_in_venv"

			return "pip" # Far from a guarantee, so we simply won't service pip installations.
		# - = - = - = - = - = - = -
		return None


	def get_pypi_version(self):
		""" Get newest version number via PyPI public API """
		try:
			json_response = requests.get("https://pypi.org/pypi/ytcon/json", timeout=20).json()
			#logger.debug(pprint.pformat(json_response))
			return json_response["info"]["version"]
		except:
			print(traceback.format_exc())
		return None

	def auto_update_determine(self):
		"""
		A function that stores commands for updating
		"""
		if self.install_source == "pipx":
			return True, "pipx upgrade ytcon"

		if self.install_source == "git":
			ytcon_files_path = os.path.dirname(os.path.realpath(__file__))
			return True, f"git -C {ytcon_files_path} pull"

		if self.install_source == "pip_in_venv":
			python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
			if which('pip'+python_version) is not None:
				return True, f"pip{python_version} install -U ytcon --require-virtualenv"
			elif which('pip3') is not None:
				return True, "pip3 install -U ytcon --require-virtualenv"
			elif which('pip') is not None:
				return True, "pip install -U ytcon --require-virtualenv"
			else:
				return False, None

		if self.install_source == "pip":
			return False, None

		return False, None


	# def get_pypi_version_new_thread(self):
	# 	""" Just starts a new thread self.get_pypi_version. Made for not to slow down GUI or utility launch """
	# 	threading.Thread(target=self.get_pypi_version, daemon=True).start()

app_updates = UpdateAndVersionsClass()
