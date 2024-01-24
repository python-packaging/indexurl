import logging
import os
from configparser import RawConfigParser
from pathlib import Path
from typing import Optional

import appdirs

LOG = logging.getLogger(__name__)

DEFAULT_INDEX_URL = "https://pypi.org/simple"


def get_index_url() -> str:
    """
    Returns the configured (or default) value of global.index-url

    For most intents this matches the value of `pip config get global.index-url`
    except it works with older versions of pip, has the default in a common
    place, normalizes the trailing slash away, and doesn't require another
    process or pip to be installed.
    """
    # There are a lot of places this can live.
    # See https://pip.pypa.io/en/stable/topics/configuration/#location
    #
    # Note that we look at them in _reverse_ order so we can stop as soon as the
    # key is found.

    virtual_env = os.getenv("VIRTUAL_ENV")
    pip_config_file = os.getenv("PIP_CONFIG_FILE")
    xdg_config_dirs = os.getenv("XDG_CONFIG_DIRS", "").split(",")
    if pip_config_file == "os.devnull":
        return DEFAULT_INDEX_URL

    for option in [
        # Site
        Path(virtual_env, "pip.conf") if virtual_env else None,
        # User
        (
            # These look the same at first glance but they're not on Mac.  See
            # the doc for this complex logic involving whether the _dir_ exists.
            Path(appdirs.user_config_dir("pip"), "pip.conf")
            if Path(appdirs.user_config_dir("pip")).exists()
            else Path("~/.config/pip/pip.conf").expanduser()
        ),
        # Global
        Path("/etc/pip.conf"),
        *(Path(d, "pip", "pip.conf") for d in xdg_config_dirs),
        # Env
        Path(pip_config_file) if pip_config_file else None,
    ]:
        if option is not None:
            index_url = _get_global_index_url_from_file(option)
            if index_url:
                return index_url.rstrip("/")

    return DEFAULT_INDEX_URL


def _get_global_index_url_from_file(path: Path) -> Optional[str]:
    """
    Returns the global.index-url, or None.  Logs an error message if file exists
    but is invalid or unreadable.
    """
    if not path.exists():
        return None
    config = RawConfigParser()
    try:
        config.read(path)
    except Exception as e:
        LOG.warning("Config %s could not be read: %s", path, repr(e))
    return config.get("global", "index-url", fallback=None)


if __name__ == "__main__":  # pragma: no cover
    print(get_index_url())
