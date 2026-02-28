import contextlib
import logging
import os
from multiprocessing import Queue
from pathlib import Path

from colorlog import ColoredFormatter

from ._types import set_logger_level


def _set_default_formatter(
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
        formatter = logging.Formatter(format_str, style="%")
    handler.setFormatter(formatter)


def _add_file_handler(
    logger: logging.Logger,
    filename: str,
    formatter: logging.Formatter | None = None,
) -> None:
    file_path = Path(filename).resolve()
    for handler in logger.handlers:
        if (
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename).resolve() == file_path
        ):
            return
    if file_path.parent != Path():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(file_path, mode="wt", encoding="utf8")
    if formatter is not None:
        handler.setFormatter(formatter)
    else:
        _set_default_formatter(handler, with_color=False)
    logger.addHandler(handler)


def _handle_dict_record(
    record: dict, logger: logging.Logger, main_pid: int
) -> bool:
    """Handle a dict control record. Returns True if worker should exit."""
    if record.get("cyy_logger_exit") == main_pid:
        return True
    level = record.pop("logger_level", None)
    if level is not None:
        set_logger_level(logger, level)
    formatter = record.pop("logger_formatter", None)
    if formatter is not None:
        for handler in logger.handlers:
            handler.setFormatter(formatter)
    filename = record.pop("filename", None)
    if filename is not None:
        fmt = logger.handlers[0].formatter if logger.handlers else None
        _add_file_handler(logger, filename=filename, formatter=fmt)
    removed_filename = record.pop("removed_filename", None)
    done_event = record.pop("done_event", None)
    if removed_filename is not None:
        resolved = Path(removed_filename).resolve()
        for handler in logger.handlers[:]:
            if (
                isinstance(handler, logging.FileHandler)
                and Path(handler.baseFilename).resolve() == resolved
            ):
                handler.flush()
                logger.removeHandler(handler)
                handler.close()
    if done_event is not None:
        done_event.set()
    return False


def worker(qu: Queue, main_pid: int) -> None:
    # Avoid holding a handle on the inherited CWD (e.g. a temp directory)
    with contextlib.suppress(OSError):
        os.chdir(Path.home())

    logger: logging.Logger = logging.getLogger("colored_logger")
    assert not logger.handlers
    handler = logging.StreamHandler()
    _set_default_formatter(handler, with_color=True)
    logger.addHandler(handler)
    set_logger_level(logger, logging.DEBUG)
    logger.propagate = False

    try:
        while True:
            try:
                record = qu.get()
                if record is None:
                    break
                match record:
                    case dict():
                        if _handle_dict_record(record, logger, main_pid):
                            break
                    case _:
                        logger.handle(record)
                        for h in logger.handlers:
                            h.flush()
            except (ValueError, EOFError, OSError, TypeError):
                break
    finally:
        for handler in logger.handlers[:]:
            with contextlib.suppress(Exception):
                handler.flush()
            with contextlib.suppress(Exception):
                handler.close()
            logger.removeHandler(handler)
