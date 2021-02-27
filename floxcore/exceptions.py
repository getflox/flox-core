from click import ClickException

from floxcore.console import error_box


class FloxException(ClickException):
    """General flox exception, all exceptions should be based on it"""

    def __init__(self, message, extra="", exit_code=1):
        super().__init__(message)
        self.extra = extra
        self.exit_code = exit_code

    def show(self, file=None):
        error_box(message=self.message, extra=self.extra, file=file)


class ProfileException(FloxException):
    """Problems with profile"""


class ProjectException(FloxException):
    """Project related issues"""


class ConfigurationException(FloxException):
    """Missing or invalid configuration"""


class PluginException(FloxException):
    """Problems with plugin"""


class MissingPluginException(FloxException):
    """Problems with plugin"""

    def __init__(self, plugin):
        super().__init__(f"Unable to find plugin '{plugin}'",
                         extra="Check list of installed plugins with `flox plugin`")


class KeyringException(FloxException):
    """Keyring related issues"""


class InvalidFunctionCallException(FloxException):
    """Problems with plugin"""


class MissingConfigurationValue(FloxException):
    def __init__(self, name):
        super().__init__(f"Missing configuration parameter '{name}'. Use flox configure")


class ShellException(FloxException):
    """Shell command execution error"""


class StopExecutionException(Exception):
    """Stop execution of the tages"""
