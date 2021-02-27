from os.path import join, isfile

import toml
from box import Box


class StateManager:
    def __init__(self, flox, state="state"):
        """
        :type flox: floxcore.context.Flox
        """
        data = {}
        self.state_file = join(flox.local_config_dir, state)

        if isfile(self.state_file):
            data = toml.load(open(self.state_file))

        self._state = Box(data)

    def set(self, name, val):
        self.__setattr__(name, val)

    def remove(self, name):
        if name in self._state:
            del self._state[name]
            self._save()

    def has(self, name):
        return name in self._state

    def get(self, item):
        return self._state.get(item)

    def all(self):
        return self._state

    def __getattr__(self, item):
        return self._state.get(item)

    def __setattr__(self, key, value):
        if key not in ["_state", "state_file"]:
            self._state[key] = value
            self._save()
        else:
            super().__setattr__(key, value)

    def _save(self):
        with open(self.state_file, "w+") as f:
            toml.dump(self._state, f)
