import atexit
import logging
import logging.handlers
import os
import os.path
import inspect
import tuned.consts as consts

__all__ = ["get"]

root_logger = None

def get():
	global root_logger
	if root_logger is None:
		root_logger = logging.getLogger("tuned")

	calling_module = inspect.currentframe().f_back
	name = calling_module.f_locals["__name__"]
	if name == "__main__":
		name = "tuned"
		return root_logger
	elif name.startswith("tuned."):
		(root, child) = name.split(".", 1)
		child_logger = root_logger.getChild(child)
		child_logger.remove_all_handlers()
		child_logger.setLevel("NOTSET")
		return child_logger
	else:
		assert False

class TunedLogger(logging.getLoggerClass()):
	"""Custom tuned daemon logger class."""
	_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
	_console_handler = None
	_file_handler = None

	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		self.setLevel(logging.INFO)
		self.switch_to_console()

	def set_level(self, level, default = logging.NOTSET):
		"""Set logging level. The 'level' parameter can be str or logging module constant."""
		if type(level) is str:
			level = logging._levelNames.get(level.upper(), logging.NOTSET)
		self.level = level

	def switch_to_console(self):
		self._setup_console_handler()
		self.remove_all_handlers()
		self.addHandler(self._console_handler)

	def switch_to_file(self, filename = consts.LOG_FILE):
		self._setup_file_handler(filename)
		self.remove_all_handlers()
		self.addHandler(self._file_handler)

	def remove_all_handlers(self):
		for handler in self.handlers:
			self.removeHandler(handler)

	@classmethod
	def _setup_console_handler(cls):
		if cls._console_handler is not None:
			return

		cls._console_handler = logging.StreamHandler()
		cls._console_handler.setFormatter(cls._formatter)

	@classmethod
	def _setup_file_handler(cls, filename):
		if cls._file_handler is not None:
			return

		log_directory = os.path.dirname(filename)
		if not os.path.exists(log_directory):
			os.makedirs(log_directory)

		cls._file_handler = logging.handlers.RotatingFileHandler(
			filename, maxBytes = consts.LOG_FILE_MAXBYTES, backupCount = consts.LOG_FILE_COUNT)
		cls._file_handler.setFormatter(cls._formatter)

logging.setLoggerClass(TunedLogger)
atexit.register(logging.shutdown)
