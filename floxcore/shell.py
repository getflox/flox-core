from plumbum import FG
from plumbum import local, ProcessExecutionError

from floxcore.exceptions import ShellException


def execute_command(command, args, variables=None):
    variables = variables or {}

    with local.env(**variables):
        cmd = local[command]
        try:
            (cmd.__getitem__(args) & FG)
        except ProcessExecutionError as e:
            message = e.stderr or f"Failed to execute {' '.join(e.argv)}"

            for value in [v for v in variables.values() if v]:
                message = message.replace(value, "**********")

            raise ShellException(message, exit_code=e.retcode)
