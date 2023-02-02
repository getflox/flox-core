import itertools
from collections import ChainMap
from os.path import isfile, join
from typing import List

import yaml
from box import Box
from loguru import logger

from floxcore import Plugin


class Project(object):
    def __init__(self, context):
        self.context = context
        self.id = None
        self.description = None
        self.variables = {}

    @property
    def stages(self):
        stages = list(itertools.chain(*[plugin.project_stages for plugin in self.context.plugins]))
        stages.sort()

        return stages


class FloxContext(object):
    def __init__(self, plugins):
        self.plugins: List[Plugin] = list(map(lambda x: x.resolve(), list(plugins or [])))
        self.project: Project = Project(self)
        self.work_dir = None
        self.profile = Box(default_box=True)
        self.profile_file = None

    @property
    def profile_file_local(self):
        return self.profile_file.replace(self.work_dir, "")

    def load(self):
        self.profile_file = join(self.work_dir, ".flox")

        if isfile(self.profile_file):
            with open(self.profile_file, "r") as stream:
                try:
                    profile: dict = yaml.safe_load(stream)
                    for k, v in profile.pop("project", {}).items():
                        setattr(self.project, k, v)

                    self.profile = Box(profile)
                except yaml.YAMLError as e:
                    logger.exception(e)

        self.project.variables = ChainMap(
            *list(map(lambda x: {x.name: x.load(**self.profile.get(x.name, {}))}, self.plugins))
        )
