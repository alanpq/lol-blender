import bpy

from addons.lol_blender.dependencies import *


class LOL_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "example.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        # Deactivate when dependencies have been installed
        # return not dependencies_installed[0]
        return True

    def execute(self, context):
        try:
            install_pip()
            for dependency in dependencies:
                pkg = dependency.package
                if dependency.module == "league_toolkit":
                    pkg = bpy.context.preferences.addons["lol_blender"].preferences.wheel_path
                install_and_import_module(module_name=dependency.module,
                                          package_name=pkg,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        dependencies_installed[0] = True

        # Register the panels, operators, etc. since dependencies are installed
        # for cls in classes:
        #     bpy.utils.register_class(cls)

        return {"FINISHED"}
