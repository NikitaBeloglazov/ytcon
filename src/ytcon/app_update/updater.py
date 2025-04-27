""" A piece of code that runs a command to self-update ytcon. After completion, restarts app """
import time
import os
import sys

from app_update.variables import app_updates
from render.loop import loop_container

def update_run_and_restart(_=None):
	""" Starts self-update """
	if app_updates.auto_update_command is None:
		return None

	loop_container.loop.stop()

	try:
		print("\n- = - =\n")
		print("Updater started!")
		print(f"Install source: {app_updates.install_source} ({app_updates.detected_by})")
		print(f"\n{app_updates.version} -> {app_updates.pypi_version}")
		print("\n- = - =")
		print("\nThe following command will run in 10 seconds:")
		print(" - " + app_updates.auto_update_command)
		print("\nCtrl+C to cancel update.")
		time.sleep(10)
		print("- = - =\n>> " + app_updates.auto_update_command + "\n")
		status_code = os.system(app_updates.auto_update_command)
		#status_code = 0
		if status_code == 0:
			print("\n- = - =\nUpdate was completed successfully! YTCON will restart itself in 5 secs..")
			restart_command = sys.executable + " " + " ".join(sys.argv)
			print(" - " + restart_command)
			print("\nCtrl+C to cancel restart.")
			time.sleep(5)
			print("- = - =\n>> " + restart_command + "\n")
			os.system(restart_command)
			sys.exit(0)
		else:
			print("\n- = - =\nERROR: It looks like the update failed. See the output above for details.\nPossibly YTCON has not been updated.")
			sys.exit(1)
	except KeyboardInterrupt:
		print("\n\n[!!] Update was interrupted by user")
		sys.exit(1)
	return None
