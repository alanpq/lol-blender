import bpy

from addons.lol_blender.dependencies import *


class LOL_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "lolblender.install_dependencies"
    bl_label = "Manually install dependencies"
    bl_description = ("Installs the league-toolkit dependency for this add-on. "
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
            install_dependencies(bpy.context.preferences.addons["lol_blender"].preferences.wheel_path)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        dependencies_installed[0] = True

        # Register the panels, operators, etc. since dependencies are installed
        # for cls in classes:
        #     bpy.utils.register_class(cls)

        return {"FINISHED"}
