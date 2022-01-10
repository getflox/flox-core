from functools import wraps
from os import getcwd
from os.path import realpath, join, abspath, isdir, pardir

import click
from click import Context

from floxcore.exceptions import ProjectException
from floxcore.plugin import PluginManager
from floxcore.secrets import Manager
from floxcore.settings import CONFIG_DIRS
from floxcore.state import StateManager


def locate_project_root(test, dirs=(".flox",), default=None):
    prev, test = None, abspath(test)
    user_dir = CONFIG_DIRS.get("user")
    while prev != test:
        if any(isdir(join(test, d)) and join(test, d) != user_dir for d in dirs):
            return test
        prev, test = test, abspath(join(test, pardir))

    return default


def with_active_project(f):
    @wraps(f)
    def wrapper(flox, *args, **kwargs):
        if not flox.initiated:
            ProjectException("Calling project related method without project context")

        return f(flox, *args, **kwargs)

    return wrapper


class Flox:
    CONFIG_FILE_NAME = "config.yml"
    plugins = PluginManager()

    def __init__(self, project_dir=None):
        self.cwd = getcwd()
        if not project_dir:
            project_dir = locate_project_root(self.cwd)
            self.working_dir = realpath(project_dir or self.cwd)
        else:
            self.working_dir = project_dir
        self.initiated = isdir(str(join(str(project_dir), ".flox")))
        self.meta = StateManager(self, "metadata")
        self.local = StateManager(self, "local")
        self.remotes = StateManager(self, join(CONFIG_DIRS.get("user"), "remotes"))

        from floxcore.config import load_settings

        self.settings = load_settings(Flox.plugins, self.initiated, self.working_dir, self.profile, self.remotes)

        self.secrets = Manager(self)

    @property
    @with_active_project
    def environment_file(self):
        return join(self.local_config_dir, "environment")

    @property
    @with_active_project
    def local_config_dir(self):
        return join(self.working_dir, ".flox")

    @property
    @with_active_project
    def config_file(self):
        return self.get_module_config_path(Flox.CONFIG_FILE_NAME)

    @with_active_project
    def get_module_config_path(self, module):
        return join(self.local_config_dir, module)

    @property
    def prompt(self):
        return Prompt(self)

    @property
    @with_active_project
    def name(self):
        return self.meta.name

    @property
    @with_active_project
    def id(self):
        return self.meta.id

    @property
    @with_active_project
    def profile(self):
        return self.local.profile or 'dev'

    def security_context(self, scope=None):
        return self.plugins.execute("execution_context", flox=self, scope=scope)


class Prompt:
    def __init__(self, flox: Flox) -> None:
        self.flox = flox

    @staticmethod
    def colourize(name):
        if name in ["prod", "production", "live"]:
            return click.style(name, fg="red")
        elif name in ["uat", "preprod", "test"]:
            return click.style(name, fg="yellow")
        elif name in ["staging", "integration"]:
            return click.style(name, fg="green")
        else:
            return name

    def __repr__(self):
        return "{name}@{profile}> ".format(name=self.flox.id, profile=Prompt.colourize(self.flox.profile))


class EmptyContext:
    def __init__(self, flox, command, args, **kwargs):
        self.args = args
        self.flox = flox
        self.command = command
        self.kwargs = kwargs

        if "max_content_width" not in self.kwargs:
            terminal_width, _ = click.get_terminal_size()
            self.kwargs["max_content_width"] = terminal_width

    def __enter__(self):
        ctx = Context(self.command, info_name=self.command.name, obj=self.flox, **self.kwargs)
        with ctx.scope(cleanup=False):
            self.command.parse_args(ctx, self.args)

        return ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
