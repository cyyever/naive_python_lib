import atexit
import contextlib
import logging
import logging.handlers
import os
import threading
from multiprocessing import Manager, Process, Queue
from typing import Any

from colorlog import ColoredFormatter


def __worker(qu: Queue, main_pid) -> None:
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
                        add_file_handler_impl(filename=filename, formatter=formatter)
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


__logger_lock = threading.RLock()
__message_queue: Any = None

__proxy_logger: logging.Logger | None = None


def __initialize_proxy_logger() -> None:
    global __proxy_logger
    __proxy_logger = logging.getLogger("proxy_logger")
    assert not __proxy_logger.handlers
    __proxy_logger.setLevel(logging.INFO)
    __proxy_logger.addHandler(logging.handlers.QueueHandler(__message_queue))
    __proxy_logger.propagate = False


__filenames = set()


def __initialize_logger() -> None:
    global __message_queue
    if __message_queue is not None:
        return
    __message_queue = Manager().Queue()
    __initialize_proxy_logger()

    __background_thd = Process(
        target=__worker, args=(__message_queue, os.getpid()), daemon=True
    )
    __background_thd.start()

    @atexit.register
    def shutdown() -> None:
        with contextlib.suppress(BaseException):
            __message_queue.put({"cyy_logger_exit": os.getpid()})


def add_file_handler(filename: str) -> None:
    with __logger_lock:
        filename = os.path.normpath(os.path.abspath(filename))
        __filenames.add(filename)
        __message_queue.put({"filename": filename})


def set_level(level: Any) -> None:
    __message_queue.put({"logger_level": level})


__formatter = None


def set_formatter(formatter: logging.Formatter) -> None:
    global __formatter
    __formatter = formatter
    __message_queue.put({"logger_formatter": __formatter})


def get_logger_setting() -> dict:
    if __message_queue is None:
        return {}
    setting = {
        "message_queue": __message_queue,
        "filenames": __filenames,
        "pid": os.getpid(),
    }
    if __formatter is not None:
        setting["logger_formatter"] = __formatter
    return setting


def apply_logger_setting(setting: dict) -> None:
    global __message_queue
    if not setting:
        return
    if os.getpid() == setting["pid"]:
        return
    __message_queue = setting["message_queue"]
    __initialize_proxy_logger()
    __formatter = setting.pop("logger_formatter", None)
    if __formatter is not None:
        set_formatter(formatter=__formatter)
    for filename in setting["filenames"]:
        add_file_handler(filename=filename)


def __get_logger() -> logging.Logger:
    __initialize_logger()
    assert __proxy_logger is not None
    return __proxy_logger


def log_info(*args, **kwargs) -> None:
    __get_logger().info(*args, **kwargs, stacklevel=2)


def log_debug(*args, **kwargs) -> None:
    __get_logger().debug(*args, **kwargs, stacklevel=2)


def log_warning(*args, **kwargs) -> None:
    __get_logger().warning(*args, **kwargs, stacklevel=2)


def log_error(*args, **kwargs) -> None:
    __get_logger().error(*args, **kwargs, stacklevel=2)
