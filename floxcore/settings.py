from os.path import join, expanduser


class ConfigDirs:
    def __init__(self, dirs):
        self.dirs = dirs

    def get(self, scope, default=None):
        return self.dirs.get(scope, default)

    def get_in(self, scope, subpath):
        return join(self.dirs.get(scope), subpath)

    @property
    def SYSTEM(self):
        return self.get("system")

    @property
    def USER(self):
        return self.get("user")


CONFIG_DIRS = ConfigDirs(dict(
    system="/etc/flox/",
    user=join(expanduser("~"), ".flox")
))
