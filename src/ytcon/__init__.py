"""
Just placeholder for pylint. Please ignore this file
For running ytcon start yt.py file.
But when trying to call, it will try to run ytcon
"""
try:
	from . import yt # pylint: disable=import-self
except (ImportError, ModuleNotFoundError) as e:
	try:
		import yt
	except (ImportError, ModuleNotFoundError) as e:
		m = "[!] [YTCON] For running YTCON, please start yt.py file, not __init__.py."
		raise RuntimeError(m) from e
