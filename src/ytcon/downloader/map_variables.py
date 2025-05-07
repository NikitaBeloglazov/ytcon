"""
Created to simplify the distribution of parameters,
work is organized here with playlists and requesting several formats on youtube
"""

from control.variables import variables
from log import journal, logger

class MapVariablesClass:
	""" Created to simplify the distribution of parameters, work is organized here with playlists and requesting several formats on youtube """

	def main(self, multiple_formats, infolist, filename):
		""" Finding some specific parameters and using a loop assign if there are several files """
		if multiple_formats:
			variables.queue_list[infolist["original_url"]] = {}
			variables.queue_list[infolist["original_url"]]["meta_index"] = True
			variables.queue_list[infolist["original_url"]]["multiple_formats"] = True
			variables.queue_list[infolist["original_url"]]["formats"] = []
			variables.queue_list[infolist["original_url"]]["status"] = "waiting"
			for i in infolist["requested_formats"]:
				temp1_index = infolist["original_url"] + ":" + i["format_id"]
				variables.queue_list[infolist["original_url"]]["formats"].append(i["format_id"])
				self.map_variables(temp1_index, infolist, i, filename)
			return temp1_index
		# else:
		temp1_index = infolist["original_url"]
		self.map_variables(temp1_index, infolist, infolist, filename)
		return temp1_index

	def map_variables(self, temp1_index, infolist, i, filename):
		""" Main parameter assigner. In some cases, it can be used in a loop """
		variables.queue_list[temp1_index] = {}
		variables.queue_list[temp1_index]["status"] = "waiting"
		variables.queue_list[temp1_index]["status_short_display"] = "Wait"
		variables.queue_list[temp1_index]["percent"] = "0.0%"
		variables.queue_list[temp1_index]["speed"] = "0KiB/s"
		try:
			variables.queue_list[temp1_index]["size"] = str(round(i["filesize"]/1e+6)) + "MiB"
		except KeyError:
			variables.queue_list[temp1_index]["size"] = "???MiB"
		variables.queue_list[temp1_index]["downloaded"] = "0MiB"
		variables.queue_list[temp1_index]["eta"] = "ETA ??:??"
		variables.queue_list[temp1_index]["name"] = infolist["fulltitle"]
		if i["resolution"] == "audio only":
			variables.queue_list[temp1_index]["resolution"] = "audio"
		else:
			if i.get("width", None) is None and i.get("height", None) is None:
				variables.queue_list[temp1_index]["resolution"] = "???х???"
			else:
				variables.queue_list[temp1_index]["resolution"] = (str(i.get("width", None)) + "x" + str(i.get("height", None))).replace("None", "???")
		variables.queue_list[temp1_index]["site"] = infolist["extractor"].lower()
		variables.queue_list[temp1_index]["file"] = filename

	def mark_as_error(self, url):
		""" Change the status of the downloaded link to Error if such link exists """
		if url in variables.queue_list:
			variables.queue_list[url]["status"] = "error"
			if "multiple_formats" in variables.queue_list[url]:
				for i in variables.queue_list[url]["formats"]:
					temp1_index = url + ":" + i
					variables.queue_list[temp1_index]["status"] = "error"
					variables.queue_list[temp1_index]["status_short_display"] = "Error"
			else:
				variables.queue_list[url]["status_short_display"] = "Error"

map_variables = MapVariablesClass()
