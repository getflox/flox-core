from dataclasses import dataclass, field
from typing import Callable, List

from floxcore.console import tqdm, info, warning
from floxcore.context import Flox
from floxcore.exceptions import StopExecutionException


@dataclass
class Stage:
    callback: Callable
    priority: int = 100
    require: list = field(default_factory=list)

    def __str__(self):
        return self.callback.__doc__ or self.callback.__name__

    def __repr__(self):
        return self.callback.__doc__ or self.callback.__name__

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs) or {}


def get_command_stages(flox: Flox, command: str, features: dict = None) -> List[Stage]:
    """
    Load all command entrypoints and filter by passed options. In result return list of the stages
    Returned list of the stages will be in reverse order triggering stages with higher priority to run first
    """
    stages = []

    for name, plugin in {k: v for k, v in flox.plugins.handlers(command).items() if k in (features or [])}.items():

        for stage in plugin.handle(command, flox=flox):
            if stage.require and not all(map(lambda x: bool(flox.settings[x]), stage.require)):
                continue

            stage.plugin = plugin
            stages.append(stage)

    return sorted(stages, key=lambda x: x.priority, reverse=True)


def execute_stages(flox: Flox, event: str, features=None, wrapper=tqdm, **kwargs):
    execution_stages = get_command_stages(flox, event, features)

    if not execution_stages:
        warning(f"No stages to be executed for '{event}'.")
        return {}

    output = wrapper(execution_stages)
    outputs = {}
    try:
        for stage in output:
            output.set_context(stage.plugin.name)
            output.set_description(str(stage))

            if not stage.plugin.configured(flox):
                output.warning(f"Skipping step '{str(stage)}' as '{stage.plugin.name}' plugin isn't configured")
                continue

            outputs.update(
                stage(
                    flox=flox,
                    out=output,
                    features=features,
                    **kwargs,
                    **outputs
                )
            )
    except StopExecutionException as e:
        output.close()
        info(f"Terminated command execution with message: {e}")

    return outputs
