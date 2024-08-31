""" Module that responsible for contolling ffmpeg/ffprobe checks and calls. """
import sys
import subprocess
import pprint
import ffmpeg # | !!! pip install "ffmpeg-python", NOT "ffmpeg" !!! | # https://kkroening.github.io/ffmpeg-python/ # python310-ffmpeg-python

from log import logger

# - = - Check ffmpeg installed in system - = - = - = -
try:
	# Try to launch it
	subprocess.run("ffmpeg -version", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	subprocess.run("ffprobe -version", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except subprocess.CalledProcessError as e:
	# If there was a command execution error, ffmpeg is not installed
	print("\n[!!] FFMPEG and/or FFPROBE is not installed/broken in your system. Install it using system package manager:\n - sudo apt install ffmpeg\n - sudo dnf install ffmpeg\n - sudo zypper install ffmpeg\n - sudo pacman -S ffmpeg.\n\nYTCON execution cannot be continued.\n")
	sys.exit(1)
# - = - = - = - = - = - = - = - = - = - = - = - = - = -

def get_resolution_ffprobe(file):
	""" Uses ffprobe to get video (even not fully downloaded) resolution """
	try:
		probe = ffmpeg.probe(file)
	except ffmpeg.Error as e:
		logger.debug("ffprobe error:")
		logger.debug(e.stderr)
		return None
	logger.debug("ffprobe response:")
	logger.debug(pprint.pformat(probe))
	for i in probe["streams"]:
		if "width" in i and "height" in i:
			return str(i["width"]) + "x" + str(i["height"])
	return None
