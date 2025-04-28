""" The module that is responsible for updates, determining versions, sources, and storing variables about them """
import os
import sys
import traceback
import subprocess
from shutil import which # for binary detection

import requests

from log import logger
#from control.variables import variables
#from render.colors import colors

class UpdateAndVersionsClass:
	"""
	The class stores everything related to determining the version number and self-update feature
	P.S. Previously it was called auto-update, but now it has become self-update, because there was no automatic update in fact)
	"""
	def __init__(self):
		""" Just adds placeholders """
		self.version = "0.0.0"
		self.version_tuple = (0, 0, 0)
		self.detected_by = None

		self.install_source = None

		self.pypi_version = None
		self.pypi_version_split = None

		self.auto_update_avalible = False
		self.auto_update_command = None
		self.auto_update_comment = "Refresh required"

		self.new_version_available = False

		self.initialize_called = False

	def initialize(self):
		""" Checks for updates by calling various functions. Pushes useful information in variables """
		self.version, self.version_tuple, self.detected_by = self.get_version()
		self.install_source = self.get_source()
		self.pypi_version, self.pypi_version_split = self.get_pypi_version()

		self.auto_update_avalible, self.auto_update_command, self.auto_update_comment = self.auto_update_determine()

		self.new_version_available = self.check_new_version_available()

		self.initialize_called = True
		logger.debug("app_update init finished")

	def get_version(self):
		"""
		Get installed version number
		outputs: version, version_tuple, detected method
		"""
		# - = - = - = - = - = - = -
		try:
			# - = WARINING = -: If you install ytcon using `pip install git+https://github.com/NikitaBeloglazov/ytcon`
			# In version and version_tuple there will be sudden garbage
			# Like this: 0.6.0.dev8+g914b4b0 AND (0, 6, 0, "dev8", "g914b4b0")
			# This is absolute crap and it needs to be fixed somehow in the scm config.
			# I didn't notice any bugs, the comparison somehow continues to work fine
			# p.s. also notice that `(0, 6, 0, "dev8", "g914b4b0") > (0, 6, 0)` is true
			from __version__ import version, version_tuple # pylint: disable=import-outside-toplevel
			if version != "0.0.0":
				return version, version_tuple, "direct_import"
		except:
			logger.debug("version detect with direct_import failed:")
			logger.debug(traceback.format_exc())
		# - = - = - = - = - = - = -

		# - = git - = - = - = - = - = -
		if which('git') is not None: # if git is installed
			try:
				# Use GIT to check tags, makes sense if git clone was used to install
				ytcon_files_path = os.path.dirname(os.path.realpath(__file__)) # get currently running script path
				tag = subprocess.check_output(('git', '-C', ytcon_files_path, 'describe', '--tags'), stderr=subprocess.PIPE, encoding="UTF-8")

				# Formating it a little
				# v0.0.11-3-g0ada3b4 -> 0.0.11
				tag = tag.replace("\n", "").replace("v", "")
				if tag.find("-") > 1:
					tag = tag[0:tag.find("-")]

				tag_split = tag.split(".")
				if len(tag_split) == 3 and all(map(str.isdigit, tag_split)): # Check all fields in typle are digit
					tag_split = tuple(map(int, tag_split)) # Convert ("0", "0", "0") to (0, 0, 0)
				else: # if something is wrong
					logger.debug("git detection failed: something wrong with tags:")
					logger.debug(tag)
					logger.debug(tag_split)
					return "0.0.0", (0, 0, 0), None

				return tag, tag_split, "git"
				# - - - - - ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ convert to typle like (0, 5, 3)
			except subprocess.CalledProcessError as e:
				logger.debug("version detect with git failed:")
				logger.debug(traceback.format_exc())
				logger.debug("git stderr:")
				logger.debug(e.stderr)
			except:
				logger.debug("version detect with git failed:")
				logger.debug(traceback.format_exc())
		# - = - = - = - = - = - = -
		return "0.0.0", (0, 0, 0), None # if none is detected


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
				logger.debug("rpm module not found on this system.")
			except:
				logger.debug(traceback.format_exc())

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

	# def get_pypi_version_new_thread(self):
	# 	""" Just starts a new thread self.get_pypi_version. Made for not to slow down GUI or utility launch """
	# 	threading.Thread(target=self.get_pypi_version, daemon=True).start()

	def get_pypi_version(self):
		""" Get newest version number via PyPI public API """
		try:
			json_response = requests.get("https://pypi.org/pypi/ytcon/json", timeout=20).json()
			#logger.debug(pprint.pformat(json_response))
			version = json_response["info"]["version"]

			version_split = version.split(".")
			if len(version_split) == 3 and all(map(str.isdigit, version_split)): # Check all fields in typle are digit
				version_split = tuple(map(int, version_split)) # Convert ("0", "0", "0") to (0, 0, 0)
			else: # if something is wrong
				logger.debug("pypi request: something wrong with versions:")
				logger.debug(version)
				logger.debug(version_split)
				return None, None

			return version, version_split
		except:
			logger.debug(traceback.format_exc())
		return None, None

	def auto_update_determine(self):
		"""
		A function that stores commands for updating
		outputs: avalible(bool), command(string/None), comment(string/None)
		"""
		if self.install_source == "pipx":
			return True, "pipx upgrade ytcon", None

		if self.install_source == "git":
			ytcon_files_path = os.path.dirname(os.path.realpath(__file__))
			return True, f"git -C {ytcon_files_path} pull", None

		if self.install_source == "pip_in_venv":
			python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
			if which('pip'+python_version) is not None:
				return True, f"pip{python_version} install -U ytcon --require-virtualenv", None
			if which('pip3') is not None:
				return True, "pip3 install -U ytcon --require-virtualenv", None
			if which('pip') is not None:
				return True, "pip install -U ytcon --require-virtualenv", None
			return False, None, "pip binary not found"

		if self.install_source == "pip":
			return False, None, "pip without environment (env) is unsupported. Use pipx (recommended) or pip in venv"
		if self.install_source == "rpm":
			return False, None, "Restricted. To update the RPM version of YTCON, use the system package manager (zypper, dnf)"

		return False, None, "Install source is unknown"

	def check_new_version_available(self):
		""" Checks if the pypi version is higher than the installed one. """
		if self.pypi_version != "0.0.0" and self.pypi_version is not None and self.version != "0.0.0":
			if self.pypi_version_split > self.version_tuple:
				return True
		return False

app_updates = UpdateAndVersionsClass()
