"""
	A hook that is called every time by yt-dlp when the state of the task changes (example percent changed),
	and the hook writes the necessary information to the class in order to draw it later
"""
#import pprint
from log import journal, logger

from control.variables import variables
from control.exit import exit_with_exception, traceback

from misc.ffmpeg import get_resolution_ffprobe

def hook(d):
	""" A hook that is called every time by yt-dlp when the state of the task changes (example percent changed),
	and the hook writes the necessary information to the class in order to draw it later """
	try:
		# - = - = - log spam filter - = - = - = - =
		if "automatic_captions" in d["info_dict"]:
			del d["info_dict"]["automatic_captions"]
		if "formats" in d["info_dict"]:
			del d["info_dict"]["formats"]
		if "thumbnails" in d["info_dict"]:
			del d["info_dict"]["thumbnails"]
		if "heatmap" in d["info_dict"]:
			del d["info_dict"]["heatmap"]

		# ↓ ???
		d["info_dict"]["formats"] = []
		d["info_dict"]["thumbnails"] = []
		d["info_dict"]["subtitles"] = []
		d["info_dict"]["fragments"] = []
		# - = - = - = - = - = - = - = - = - = - = -

		#logger.debug(pprint.pformat(d))
		if "multiple_formats" in variables.queue_list[d["info_dict"]["original_url"]]:
			indexx = d["info_dict"]["original_url"] + ":" + d["info_dict"]["format_id"]
		else:
			indexx = d["info_dict"]["original_url"]

		# - = - resolution detector - = - = - = - = - = - = - = - = - = -
		if variables.queue_list[indexx]["resolution"].find("???") > -1: # if resolution is unknown
			if (variables.queue_list[indexx].get("resolution_detection_tried_on_byte", 0) + 4000000) < int(d.get("downloaded_bytes", 0)) and variables.queue_list[indexx].get("resolution_detection_tries", 0) < 5:
				# int(d["downloaded_bytes"]) > 4000000 # if the file size is too smol, it does not have the needed metadata and ffprobe gives an error
				logger.debug("DOWNBYTES: %s", str(d["downloaded_bytes"]))
				temp1 = get_resolution_ffprobe(d["tmpfilename"])
				temp2 = str(variables.queue_list[indexx].get("resolution_detection_tries", 0)+1)

				if temp1 is not None:
					variables.queue_list[indexx]["resolution"] = temp1
					journal.info(f"[YTCON] Detected resolution: {temp1} (on try {temp2})" )
				else:
					journal.warning(f'[YTCON] Resolution detection failed: ffprobe gave an error (try {temp2})')
				variables.queue_list[indexx]["resolution_detection_tried_on_byte"] = int(d["downloaded_bytes"])
				variables.queue_list[indexx]["resolution_detection_tries"] = variables.queue_list[indexx].get("resolution_detection_tries", 0) + 1
			# - = - = - = -
			# Detects resolution on finished file if is it undetected
			if d["status"] == "finished":
				temp1 = get_resolution_ffprobe(variables.queue_list[indexx]["file"])

				if temp1 is not None:
					variables.queue_list[indexx]["resolution"] = temp1
					journal.info(f"[YTCON] Detected resolution: {temp1} (after full download)" )
				else:
					journal.warning('[YTCON] Resolution detection failed: ffprobe gave an error even after full download')
		# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

		variables.queue_list[indexx]["file"] = d["info_dict"]['_filename']
		if variables.queue_list[indexx]["status"] == "exists" and d["status"] == "finished":
			return None # i'll guess it's made to avoid bugs that overwriting some data
		variables.queue_list[indexx]["status"] = d["status"]

		if int(d["_percent_str"].strip().split(".")[0]) > 100:
			journal.warning("[YTCON] yt-dlp returned percent more than 100%: \"" + d["_percent_str"].strip() + "\". Values remain unchanged...")
		else:
			variables.queue_list[indexx]["status_short_display"] = d["_percent_str"].strip()
			variables.queue_list[indexx]["percent"] = d["_percent_str"].strip()
		variables.queue_list[indexx]["speed"] = d["_speed_str"].strip()

		try:
			if variables.queue_list[indexx]["eta"].count(":") > 1:
				variables.queue_list[indexx]["eta"] = d["_eta_str"].strip()
			else:
				variables.queue_list[indexx]["eta"] = "ETA " + d["_eta_str"].strip()
		except KeyError:
			if d["status"] == "finished":
				variables.queue_list[indexx]["eta"] = "ETA 00:00"

		try:
			if d["_total_bytes_estimate_str"].strip() == "N/A":
				variables.queue_list[indexx]["size"] = d["_total_bytes_str"].strip()
			else:
				variables.queue_list[indexx]["size"] = d["_total_bytes_estimate_str"].strip()
		except KeyError:
			pass

		try:
			variables.queue_list[indexx]["downloaded"] = d["_downloaded_bytes_str"].strip()
		except:
			pass

		#logger.debug(pprint.pformat(variables.queue_list))
	except:
		exit_with_exception(traceback.format_exc())
	return None
