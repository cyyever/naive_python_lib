import atexit
import contextlib
import logging
import logging.handlers
import multiprocessing
import os
import threading
from multiprocessing import Queue
from typing import Any

from colorlog import ColoredFormatter


class __LoggerEnv:
    __logger_lock = threading.RLock()
    __multiprocessing_ctx: Any = multiprocessing
    __message_queue: Any = None
    __proxy_logger: logging.Logger | None = None
    __filenames: set[str] = set()
    __formatter: None | Any = None
    __logger_level: Any | None = None

    @classmethod
    def set_multiprocessing_ctx(cls, ctx: Any) -> None:
        with cls.__logger_lock:
            cls.__multiprocessing_ctx = ctx

    @classmethod
    def initialize_proxy_logger(cls) -> logging.Logger:
        with cls.__logger_lock:
            if cls.__proxy_logger is not None:
                return cls.__proxy_logger
            cls.__initialize_logger()
            cls.__proxy_logger = logging.getLogger("proxy_logger")
            if cls.__proxy_logger.handlers:
                return cls.__proxy_logger
            cls.__proxy_logger.setLevel(logging.INFO)
            cls.__proxy_logger.addHandler(
                logging.handlers.QueueHandler(cls.__message_queue)
            )
            cls.__proxy_logger.propagate = False
            cls.__apply_logger_setting()
            return cls.__proxy_logger

    @classmethod
    def __apply_logger_setting(cls) -> None:
        if cls.__message_queue is None:
            return
        if cls.__logger_level is not None:
            cls.__message_queue.put({"logger_level": cls.__logger_level})

        if cls.__formatter is not None:
            cls.__message_queue.put({"logger_formatter": cls.__formatter})

        for filename in cls.__filenames:
            cls.__message_queue.put({"filename": filename})

    @classmethod
    def set_formatter(cls, formatter: logging.Formatter) -> None:
        with cls.__logger_lock:
            cls.__formatter = formatter
            cls.__apply_logger_setting()

    @classmethod
    def set_level(cls, level: Any) -> None:
        with cls.__logger_lock:
            cls.__logger_level = level
            cls.__apply_logger_setting()

    @classmethod
    def add_file_handler(cls, filename: str) -> None:
        filename = os.path.normpath(os.path.abspath(filename))
        with cls.__logger_lock:
            cls.__filenames.add(filename)
            cls.__apply_logger_setting()

    @classmethod
    def remove_file_handler(cls, filename: str) -> None:
        filename = os.path.normpath(os.path.abspath(filename))
        with cls.__logger_lock:
            cls.__filenames.remove(filename)
            cls.__message_queue.put({"removed_filename": filename})

    @classmethod
    def get_logger_setting(cls) -> dict:
        if cls.__message_queue is None:
            return {}
        setting = {
            "message_queue": cls.__message_queue,
            "filenames": cls.__filenames,
            "pid": os.getpid(),
        }
        if cls.__formatter is not None:
            setting["logger_formatter"] = cls.__formatter
        if cls.__logger_level is not None:
            setting["logger_level"] = cls.__logger_level
        return setting

    @classmethod
    def apply_logger_setting(cls, setting: dict | None = None) -> None:
        if setting is not None:
            if not setting:
                return
            if os.getpid() == setting["pid"]:
                return
            assert cls.__message_queue is None
            cls.__message_queue = setting["message_queue"]
            if "logger_formatter" in setting:
                cls.__formatter = setting["logger_formatter"]
            if "logger_level" in setting:
                cls.__logger_level = setting["logger_level"]
            cls.__filenames.update(setting["filenames"])
        cls.__apply_logger_setting()

    @classmethod
    def __initialize_logger(cls) -> None:
        with cls.__logger_lock:
            if cls.__message_queue is not None:
                return
            cls.__message_queue = cls.__multiprocessing_ctx.Manager().Queue()
            cls.initialize_proxy_logger()

            background_thd = cls.__multiprocessing_ctx.Process(
                target=cls._worker,
                args=(cls.__message_queue, os.getpid()),
                daemon=True,
            )
            background_thd.start()

            @atexit.register
            def shutdown() -> None:
                with contextlib.suppress(BaseException):
                    if cls.__message_queue is not None:
                        cls.__message_queue.put({"cyy_logger_exit": os.getpid()})

    @classmethod
    def _worker(cls, qu: Queue, main_pid: int) -> None:
        logger: logging.Logger = logging.getLogger("colored_logger")
        assert not logger.handlers
        logger.setLevel(logging.DEBUG)
        __handler = logging.StreamHandler()

        def set_default_formatter(
            handler: logging.Handler, with_color: bool = True
        ) -> None:
            if with_color and os.getenv("EINK_SCREEN") == "1":
                with_color = False
            format_str: str = "%(asctime)s %(levelname)s {%(processName)s} [%(filename)s => %(lineno)d] : %(message)s"
            if with_color:
                formatter: logging.Formatter = ColoredFormatter(
                    "%(log_color)s" + format_str,
                    log_colors={
                        "DEBUG": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "bold_red",
                    },
                    style="%",
                )
            else:
                formatter = logging.Formatter(
                    format_str,
                    style="%",
                )

            handler.setFormatter(formatter)

        set_default_formatter(__handler, with_color=True)
        logger.addHandler(__handler)
        logger.propagate = False

        def add_file_handler_impl(
            filename: str,
            formatter: None | logging.Formatter = None,
        ) -> logging.Handler:
            for handler in logger.handlers:
                if (
                    isinstance(handler, logging.FileHandler)
                    and handler.baseFilename == filename
                ):
                    return handler
            log_dir = os.path.dirname(filename)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            handler = logging.FileHandler(filename, mode="wt", encoding="utf8")
            logger.addHandler(handler)
            if formatter is not None:
                set_default_formatter(handler, with_color=False)
            return handler

        while True:
            try:
                record = qu.get()
                if record is None:
                    return
                match record:
                    case dict():
                        if record.get("cyy_logger_exit", None) == main_pid:
                            return
                        level = record.pop("logger_level", None)
                        if level is not None:
                            for handler in logger.handlers:
                                handler.setLevel(level)
                        formatter = record.pop("logger_formatter", None)
                        if formatter is not None:
                            for handler in logger.handlers:
                                handler.setFormatter(formatter)
                        filename = record.pop("filename", None)
                        if filename is not None:
                            formatter = None
                            if logger.handlers:
                                formatter = logger.handlers[0].formatter
                            add_file_handler_impl(
                                filename=filename, formatter=formatter
                            )
                        removed_filename = record.pop("removed_filename", None)
                        if removed_filename is not None:
                            for handler in logger.handlers:
                                if (
                                    isinstance(handler, logging.FileHandler)
                                    and handler.baseFilename == removed_filename
                                ):
                                    logger.removeHandler(handler)
                    case _:
                        logger.handle(record)
                        for hander in logger.handlers:
                            hander.flush()
            except ValueError:
                return
            except EOFError:
                return
            except OSError:
                return
            except TypeError:
                return


def set_multiprocessing_ctx(ctx: Any) -> None:
    __LoggerEnv.set_multiprocessing_ctx(ctx)


def add_file(filename: str) -> None:
    add_file_handler(filename)


def remove_file_handler(filename: str) -> None:
    add_file_handler(filename)


def add_file_handler(filename: str) -> None:
    __LoggerEnv.add_file_handler(filename)


def set_level(level: Any) -> None:
    __LoggerEnv.set_level(level)


def set_formatter(formatter: logging.Formatter) -> None:
    __LoggerEnv.set_formatter(formatter)


def get_logger_setting() -> dict:
    return __LoggerEnv.get_logger_setting()


def apply_logger_setting(setting: dict) -> None:
    __LoggerEnv.apply_logger_setting(setting)


def log_info(*args, **kwargs) -> None:
    __LoggerEnv.initialize_proxy_logger().info(*args, **kwargs, stacklevel=2)


def log_debug(*args, **kwargs) -> None:
    __LoggerEnv.initialize_proxy_logger().debug(*args, **kwargs, stacklevel=2)


def log_warning(*args, **kwargs) -> None:
    __LoggerEnv.initialize_proxy_logger().warning(*args, **kwargs, stacklevel=2)


def log_error(*args, **kwargs) -> None:
    __LoggerEnv.initialize_proxy_logger().error(*args, **kwargs, stacklevel=2)
