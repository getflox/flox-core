import abc
import warnings
from dataclasses import dataclass
from os.path import join
from typing import Any, Tuple

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import anyconfig

from box import Box
from loguru import logger

from floxcore.settings import CONFIG_DIRS
from floxcore.state import StateManager


@dataclass
class ParamDefinition:
    name: str  # name of the parameter (internal)
    description: str  # description which should be presented to the user
    boolean: bool = False  # is it boolean value? (will use confirm instead of prompt)
    multi: bool = False  # allow multiple values, comma separated - will be converted into list
    secret: bool = False  # is it a secret - currently not in use
    default: Any = None  # default value, will be overwritten by current value
    filter_empty: bool = True  # filter empty values
    depends_on: str = None  # use this configuration  value only if dependant one is already configured
    value_of: str = None  # Use value of other parameter as default value

    def __post_init__(self):
        if self.multi and not self.default:
            self.default = []


def load_settings(pluginManager, initiated=True, project_directory=None, profile=None, remotes: StateManager = None):
    settings = {}
    for name, plugin in pluginManager.all().items():
        settings[name] = {i.name: i.default for i in plugin.configuration().parameters()}

    locations = [
        join(CONFIG_DIRS.get("system"), "settings.toml"),
    ]

    if remotes:
        for remote in remotes.all().values():
            locations.append(join(CONFIG_DIRS.get("user"), "externals", remote.get("hash"), "settings.toml"))
            locations.append(join(CONFIG_DIRS.get("user"), "externals", remote.get("hash"), f"settings.{profile}.toml"))

    locations.append(join(CONFIG_DIRS.get("user"), "settings.toml"), )

    if initiated:
        locations.insert(1, join(CONFIG_DIRS.get("system"), f"/etc/flox/settings.{profile}.toml"))
        locations.append(join(CONFIG_DIRS.get("user"), f"settings.{profile}.toml"))
        locations.append(join(project_directory, ".flox", "settings.toml"))
        locations.append(join(project_directory, ".flox", f"settings.{profile}.toml"))

    logger.debug(f"Loading config from: {locations}")

    config = anyconfig.load(
        locations,
        ignore_missing=True,
        ac_template=False,
        ac_parser="toml",
    )

    settings.update(config)

    return Box(settings, default_box=True, box_dots=True)


class Configuration(abc.ABC):
    @abc.abstractmethod
    def parameters(self) -> Tuple[ParamDefinition, ...]:
        pass

    def secrets(self) -> Tuple[ParamDefinition, ...]:
        return tuple()

    @abc.abstractmethod
    def schema(self):
        pass
