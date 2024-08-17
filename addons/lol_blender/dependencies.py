import bpy
import os
import sys
import subprocess
import importlib
from collections import namedtuple

Dependency = namedtuple("Dependency", ["module", "package", "name"])

dependencies = (Dependency(module="league_toolkit", package=None, name=None),)
dependencies_installed = [False]

modules = {}

default_dep_path = os.path.join(os.path.dirname(__file__), "deps")

def get_modules(wheel_path: str):
    if len(modules.keys()) != len(dependencies):
        install_dependencies(wheel_path)
    return modules

def install_dependencies(wheel_path: str):
    try:
        install_pip()
    except:
        pass
    for dependency in dependencies:
        pkg = dependency.package
        if dependency.module == "league_toolkit":
            pkg = wheel_path
        install_and_import_module(module_name=dependency.module,
                                    package_name=pkg,
                                    global_name=dependency.name)

def import_module(module_name, global_name=None, reload=True):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    if global_name is None:
        global_name = module_name

    if global_name in modules:
        print(f"reloading {global_name}")
        importlib.invalidate_caches()
        importlib.reload(modules[global_name])
    else:
        import site
        sys.path.append(site.getusersitepackages())
        # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
        # the given name, just like the regular import would.
        modules[global_name] = importlib.import_module(module_name)


def install_pip():
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    :return:
    """
    sys.executable = os.environ.get("BLENDER_SYSTEM_PYTHON", sys.executable)
    try:
        # Check if pip is already installed
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)


def install_and_import_module(module_name, package_name=None, global_name=None):
    """
    Installs the package through pip and attempts to import the installed module.
    :param module_name: Module to import.
    :param package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """
    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    sys.executable = os.environ.get("BLENDER_SYSTEM_PYTHON", sys.executable)
    subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", package_name], check=True,
                   env=environ_copy)

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)
