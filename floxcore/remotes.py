import hashlib
from distutils.dir_util import copy_tree
from os.path import join, isdir

from loguru import logger
from plumbum import local

from floxcore.context import Flox
from floxcore.exceptions import ConfigurationException


def fetch_remote_git(flox: Flox, storage, source):
    logger.debug(f"Adding {source} as external storage with git clone")
    try:
        from plumbum.cmd import git
    except ImportError:
        raise ConfigurationException("Missing git", extra="You must have git installed in your system if you "
                                                          "like to use git remote configuration provider")

    if isdir(join(storage, ".git")):
        with local.cwd(storage):
            git["pull"]()
        logger.debug(f"Updated {source} into {storage}")
    else:
        git["clone", source, storage]()
        logger.debug(f"Cloned {source} into {storage}")


def copy_local_config(flox: Flox, storage, source):
    logger.debug(f"Adding {source} as external storage with copy")
    if not isdir(source):
        raise ConfigurationException(f"Invalid source location, {source} isn't a directory")

    logger.debug(f"Copying '{source}' to '{storage}'")
    copy_tree(source, storage)


def generate_cache_hash(source):
    return hashlib.sha256(str(source).encode("UTF-8")).hexdigest()


def universal_copy(flox: Flox, base: str, source):
    source_hash = generate_cache_hash(source)
    storage = join(base, source_hash)

    if source.startswith("git") or source.endswith(".git"):
        fetch_remote_git(flox, storage, source)
    else:
        copy_local_config(flox, storage, source)
