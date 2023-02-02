import click


class Stage(object):
    def __init__(self, callback, plugin, priority=100, description=None):
        self.priority = priority
        self.callback = callback
        self.description = description or callback.__doc__
        self.plugin = plugin

    def __gt__(self, other):
        return self.priority > other.priority

    def __lt__(self, other):
        return self.priority < other.priority

    def __repr__(self):
        return f"{self.priority} :: {self.description}"

    def __str__(self):
        return self.description

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs)


class StageList(list):
    def __init__(self, plugin) -> None:
        super().__init__()
        self.plugin = plugin

    def add(self, callback, priority=100):
        self.append(Stage(callback=callback, plugin=self.plugin, priority=priority))


class Plugin(click.Group):
    def __init__(self, name=None, **kwargs) -> None:
        super().__init__(name=name or str(type(self).__name__.lower().replace("plugin", "")), **kwargs)
        self.project_stages = StageList(self)

    def load(self, **kwargs):
        return {}
