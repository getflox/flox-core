import os
import textwrap
from os.path import join

import wasabi
from wasabi.util import to_string

from floxcore.settings import CONFIG_DIRS

KEYCHAIN_PATH = join(CONFIG_DIRS.get("user"), "flox-secrets")
os.environ["KEYRING_PROPERTY_KEYCHAIN"] = KEYCHAIN_PATH
os.environ["KEYCHAIN_PATH"] = KEYCHAIN_PATH


def wrap(text, wrap_max=200, indent=4):
    """Wrap text at given width using textwrap module.

    text (unicode): The text to wrap.
    wrap_max (int): Maximum line width, including indentation. Defaults to 80.
    indent (int): Number of spaces used for indentation. Defaults to 4.
    RETURNS (unicode): The wrapped text with line breaks.
    """
    indent = indent * " "
    wrap_width = wrap_max - len(indent)
    text = to_string(text)
    return textwrap.fill(
        text,
        width=wrap_width,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


# Overwrite wrap function to allow longer line length
wasabi.wrap = wrap
wasabi.printer.wrap = wrap
wasabi.util.wrap = wrap
