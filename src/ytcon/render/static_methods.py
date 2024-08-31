""" Contains some static methods for rendering """
import time

from render.loop import loop_container

class RenderStatic:
	""" Contains some static methods for rendering """
	def __init__(self):
		pass

	def flash_button_text(self, button, color, times=4):
		""" Makes the button to blink in the specified color """
		if button is None:
			return None
		temp1 = button.get_label()
		for _ in range(1, times+1):
			button.set_label((color, temp1))
			loop_container.loop.draw_screen()
			time.sleep(0.1)
			button.set_label(temp1)
			loop_container.loop.draw_screen()
			time.sleep(0.1)
		return None

render_static = RenderStatic()
