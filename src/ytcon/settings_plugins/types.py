from abc import ABC, abstractmethod
from enum import Enum
import inspect
from typing import Optional, Union, Tuple, List, Dict, Any, Callable
from pydantic import BaseModel, Field

class WidgetType(str, Enum):
	CHECKBOX = "CHECKBOX"
	INPUT_FIELD = "INPUT_FIELD"

class VerifyInput(str, Enum):
	IGNORE = "IGNORE"
	EXEC = "EXEC"
	COMPARE_WITH_LIST = "COMPARE_WITH_LIST"
	REGEX = "REGEX"

class IfEnabledType(str, Enum):
	JSON_INSERT = "JSON_INSERT"
	CONTENT = "CONTENT"
	CONTENT_TUPLE = "CONTENT_TUPLE"
	CONTENT_IN_NESTED_JSON = "CONTENT_IN_NESTED_JSON"
	NONE = "NONE"

class PluginBase(ABC):
	title: str
	description: str | Tuple | List
	section: str
	savename: str
	widget_type: WidgetType

	if_enabled: Optional[Dict] = None # TODO REWORK!!!
	if_enabled_type: IfEnabledType

	verify_input: Optional[VerifyInput] = VerifyInput.IGNORE
	verify_input_data: Optional[Callable] = None

	enabled_by_default: bool = False

	# widget: Any = None
	# original_widget: Any = None

	# Fields requiring strict type validation (must be exact Enum instances, not raw strings).
	# Add a field here if its type cannot be a plain value — e.g. "checkbox" instead of WidgetType.CHECKBOX.
	_type_checks = {
		"widget_type": WidgetType,
		"verify_input": VerifyInput,
		"if_enabled_type": IfEnabledType,
	}

	def __init_subclass__(cls, **kwargs):
		"""
		Automatically validates every subclass (plugin) at import time.

		Checks:
		- Required fields are present (any field annotated in PluginBase without a default value).
		- Enum fields contain proper Enum instances, not raw values like strings or ints (_type_checks).
		- If verify_input = VerifyInput.EXEC checks a @staticmethod 'verify_input_data'

		Raises TypeError with a descriptive message so broken plugins are caught immediately,
		before register() is ever called.
		"""
		super().__init_subclass__(**kwargs)
		plugin_name = getattr(cls, 'savename', cls.__name__)

		# - = Check: Required fields are present (any field annotated in PluginBase without a default value).
		required = [
			f for f in PluginBase.__annotations__
			if not hasattr(PluginBase, f)
		]

		missing = [f for f in required if not hasattr(cls, f)]
		if missing:
			raise TypeError(f"[Plugin '{plugin_name}'] Missing required fields: {missing}")
		# - = - = - = - = - = -

		# - = Check: Enum fields contain proper Enum instances, not raw values like strings or ints (_type_checks).
		for f, expected_type in PluginBase._type_checks.items():
			val = getattr(cls, f, None)
			if val is not None and type(val) is not expected_type:
				raise TypeError(f"[Plugin '{plugin_name}'] '{f}' must be {expected_type.__name__}, got {type(val).__name__}: {val!r}")
		# - = - = - = - = - = -

		# - = Check: If verify_input = VerifyInput.EXEC checks a @staticmethod 'verify_input_data'
		if getattr(cls, 'verify_input', None) is VerifyInput.EXEC:
			fn = getattr(cls, 'verify_input_data', None)
			if not (callable(fn) and isinstance(inspect.getattr_static(cls, 'verify_input_data', None), staticmethod)):
				raise TypeError(f"[Plugin '{plugin_name}'] 'verify_input = VerifyInput.EXEC' requires a @staticmethod 'verify_input_data'")
		# - = - = - = - = - = -
