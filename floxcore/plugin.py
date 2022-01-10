import abc
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Dict

from click import Group
from lazy_load import lazy
from loguru import logger
from pkg_resources import iter_entry_points


@dataclass
class PluginDefinition:
    name: str = None
    description: str = None
    url: str = None
    version: str = None


class Plugin(abc.ABC, PluginDefinition):
    """
    Plugin definition class. Only mandatory method is configuration.
    If you would like to inject to action you should implement handle_{action} method which will return list
    of the stages
    """

    @abc.abstractmethod
    def configuration(self):
        """
        Return Plugin Configuration definition
        :return: floxcore.config.Configuration
        """

    def add_commands(self, cli: Group):
        """
        Add commands to given cli instance
        """

    def configured(self, flox) -> bool:
        return True

    def handle_configuration_change(self, flox):
        return tuple()

    def support(self, even_name: str):
        return hasattr(self, f"handle_{even_name}")

    def handle(self, even_name: str, *args, **kwargs):
        return getattr(self, f"handle_{even_name}")(*args, **kwargs)

    def __repr__(self):
        return self.description


class PluginManager:
    def __init__(self):
        self.plugins = lazy(self._load)

    def get(self, name: str) -> Plugin:
        return self.plugins.get(name)

    def has(self, name: str) -> bool:
        return name in self.plugins

    def all(self):
        return self.plugins

    def handlers(self, name: str) -> Dict[str, Plugin]:
        """
        Return plugins which are able to handle given event
        :param name:
        :return:
        """
        return {k: v for k, v in self.plugins.items() if v.support(name)}

    def execute(self, name: str, scope=None, *args, **kwargs):
        result = {}
        for plugin in self.handlers(name).values():
            if scope and plugin.name not in scope:
                continue
            result.update(plugin.handle(name, *args, **kwargs))

        return result

    def add_commands(self, cli: Group):
        for plugin in filter(lambda x: hasattr(x, "add_commands"), self.plugins.values()):
            plugin.add_commands(cli)

    def _load(self):
        plugins = {}
        for entry in iter_entry_points("flox.plugin"):
            logger.debug(f"Loading plugin info: {entry}")
            plugin = entry.resolve()()
            pkg = None

            for meta in ("PKG-INFO", "METADATA"):
                try:
                    pkg = self._get_pkg_info(entry.dist.get_metadata(meta))
                    break
                except FileNotFoundError as e:
                    pass

            if not pkg:
                continue

            plugin.name = entry.name
            plugin.version = pkg.get("version")
            plugin.description = pkg.get("summary")
            plugin.url = pkg.get("home-page")
            plugins[entry.name] = plugin

        return plugins

    def _get_pkg_info(self, pkg_info: str):
        config_parser = ConfigParser(strict=False)
        config_parser.read_string("[package]\n" + pkg_info)

        return dict(config_parser["package"])
