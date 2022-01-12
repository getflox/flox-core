import textwrap
from functools import partial

import click
import tqdm
from wasabi import Printer, MESSAGES
from wasabi.util import ICONS

from floxcore.config import ParamDefinition
from floxcore.utils.functions import list_get

msg = Printer()

success = partial(msg.text, color=MESSAGES.GOOD, icon=MESSAGES.GOOD)
info = partial(msg.text, color=MESSAGES.INFO, icon=MESSAGES.INFO)
error = partial(msg.text, color=MESSAGES.FAIL, icon=MESSAGES.FAIL)
warning = partial(msg.text, color=MESSAGES.WARN, icon=MESSAGES.WARN)


def message_box(message, bg, icon, extra=None, file=None):
    width = min(120, click.get_terminal_size()[0])
    indent = " " * 2

    wrap = partial(textwrap.fill, width=width - len(indent), subsequent_indent=indent, break_long_words=False,
                   break_on_hyphens=False, )

    lines = [""]
    lines += wrap(message, initial_indent=f"{indent}{ICONS.get(icon)} ").splitlines()

    if extra:
        lines += wrap(extra, initial_indent=indent, ).splitlines()

    lines.append("")
    click.echo("")
    for i, line in enumerate(lines):
        click.echo("  ", nl=False)
        click.secho(f"{line}{indent}".ljust(width, " "), bg=bg, bold=i == 1, file=file)
    click.echo("")


error_box = partial(message_box, bg="red", icon=MESSAGES.FAIL)
info_box = partial(message_box, bg="blue", icon=MESSAGES.INFO)
warning_box = partial(message_box, bg="yellow", icon=MESSAGES.WARN)
success_box = partial(message_box, bg="green", icon=MESSAGES.GOOD)


class Output:
    def __init__(self, stages, *args, **kwargs):
        self.stages = stages
        self.context = None
        self.printer = Printer()

    def success(self, title="", text="", show=True, spaced=False, exits=None):
        self.write(
            self.printer.text(title=self.with_prefix(title), text=text, color=MESSAGES.GOOD, icon=MESSAGES.GOOD,
                              show=show, spaced=spaced, exits=exits, no_print=True)
        )

    def info(self, title="", text="", show=True, spaced=False, exits=None):
        self.write(
            self.printer.text(title=self.with_prefix(title), text=text, color=MESSAGES.INFO, icon=MESSAGES.INFO,
                              show=show, spaced=spaced, exits=exits, no_print=True)
        )

    def error(self, title="", text="", show=True, spaced=False, exits=None):
        self.write(
            self.printer.text(title=self.with_prefix(title), text=text, color=MESSAGES.FAIL, icon=MESSAGES.FAIL,
                              show=show, spaced=spaced, exits=exits, no_print=True)
        )

    def warning(self, title="", text="", show=True, spaced=False, exits=None):
        self.write(
            self.printer.text(title=self.with_prefix(title), text=text, color=MESSAGES.WARN, icon=MESSAGES.WARN,
                              show=show, spaced=spaced, exits=exits, no_print=True)
        )

    def set_description(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def write(self, text):
        click.echo(text)

    def set_context(self, context: str):
        self.context = context

    def line_prefix(self) -> str:
        return f"[{self.context}] " if self.context else ""

    def with_prefix(self, title) -> str:
        return f"{self.line_prefix()} {title}"

    def __iter__(self):
        return iter(self.stages)


class tqdm(tqdm.tqdm, Output):
    def __init__(self, iterable=None, desc=None, total=None, leave=True, file=None, ncols=None, mininterval=0.1,
                 maxinterval=10.0, miniters=None, ascii=None, disable=False, unit='it', unit_scale=False,
                 dynamic_ncols=False, smoothing=0.3, bar_format=None, initial=0, position=None, postfix=None,
                 unit_divisor=1000, write_bytes=None, lock_args=None, gui=False, **kwargs):
        super().__init__(iterable, desc, total, leave, file, ncols, mininterval, maxinterval, miniters, ascii,
                         disable, unit, unit_scale, dynamic_ncols, smoothing,
                         bar_format or "{l_bar}{bar} | {n_fmt}/{total_fmt}", initial, position, postfix,
                         unit_divisor, write_bytes, lock_args, gui, **kwargs)
        Output.__init__(self, [])


def prompt(param: ParamDefinition):
    func = click.confirm if param.boolean else click.prompt

    val = None
    if param.multi:
        val = []
        info(f"'{param.description}' configuration is accepting multiple values, "
             f"each in new line, enter empty value to end input, '-' to delete value")

    i = 0
    while True:
        current_value = list_get(param.default, i, "") if param.multi else param.default
        str_val = func(click.style(" \u2192 " + param.description, fg="green"), default=current_value)

        if param.multi and str_val and str_val != "-":
            val.append(str_val)
        elif not param.multi:
            val = str_val

        # hack to avoid prompt in same line
        if str_val == current_value:
            click.echo("")

        stdout = click.get_text_stream("stdout")
        stdout.write("\033[F")
        stdout.write("\033[K")

        if str_val:
            click.echo(f" \u2714 {param.description}: {str_val}")

        i += 1
        if not str_val or not param.multi:
            break

    if param.filter_empty and not param.boolean and not val:
        return None

    return val
