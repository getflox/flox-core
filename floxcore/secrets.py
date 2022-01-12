import platform
from functools import wraps
from os.path import isfile

from keyring import get_password, set_password
from keyring.errors import KeyringLocked

from floxcore import KEYCHAIN_PATH
from floxcore.console import info
from floxcore.exceptions import MissingConfigurationValue, KeyringException


def ensure_keychain():
    try:
        if isfile(KEYCHAIN_PATH):
            return

        info("Looks like flox is trying to access keychain for the first time. \n"
             "Please select keychain password.")

        from plumbum.cmd import security
        security["create-keychain", "-P", KEYCHAIN_PATH]()
    except Exception as e:
        raise KeyringException(f"Unable to initialise keychain.")


def with_keychain(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if platform.system() == 'Darwin':
            ensure_keychain()

        return f(*args, **kwargs)

    return wrapper


class Manager:
    def __init__(self, flox):
        """
        :param flox: floxcore.context.Flox
        """
        self.flox = flox
        self.defaults = {}
        for name, plugin in self.flox.plugins.all().items():
            for param in plugin.configuration().secrets():
                self.defaults[f"{name}_{param.name}"] = param.default

    @with_keychain
    def getone(self, name, profile=None, required=False, ):
        if self.flox.initiated:
            profile = profile or self.flox.profile

        for location in reversed(self._param_locations(name, profile)):
            try:
                val = get_password(location, name)
                if val:
                    return val

            except KeyringLocked:
                raise KeyringException("Unable to unlock keyring.")

        if name in self.defaults:
            return self.defaults.get(name)

        if required:
            raise MissingConfigurationValue(name)

    @with_keychain
    def get(self, *args, required=False):
        values = {}
        for name in args:
            values[name] = self.getone(name, required)

        return values

    @with_keychain
    def put(self, name, value, scope=None, profile=None):
        key = name
        if scope == "project":
            key = f"{name}@{self.flox.id}"

        if profile:
            key += f":{profile}"

        set_password(key, name, value)

    @with_keychain
    def __getitem__(self, item):
        return self.get(item)

    @with_keychain
    def __setitem__(self, key, value):
        self.put(key, value)

    def _param_locations(self, name, profile):
        return (
            name,
            f"{name}:{profile}",
            f"{name}@{self.flox.id}",
            f"{name}@{self.flox.id}:{profile}",
        )
