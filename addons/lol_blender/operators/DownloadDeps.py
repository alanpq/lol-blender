import bpy
import requests
import platform

from addons.lol_blender.dependencies import *

class LOL_OT_download_dependencies(bpy.types.Operator):
    bl_idname = "lolblender.download_dependencies"
    bl_label = "Automatically download & install dependencies"
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
            resp = requests.get("https://api.github.com/repos/alanpq/lol-blender/releases/latest").json()

            system = platform.system().lower()
            if len(system) == 0:
                raise ValueError("Could not determine operating system.")
            machine = platform.machine().lower()
            if len(machine) == 0:
                raise ValueError("Could not determine machine architecture.")

            matches = []
            for asset in resp["assets"]:
                name: str = asset["name"].lower()
                if not name.startswith("league_toolkit"):
                    continue
                if not (system in name and machine in name):
                    continue
                matches.append((name, asset["browser_download_url"]))
            
            if len(matches) <= 0:
                raise ValueError(f"Could not find toolkit wheel for {system}/{machine}.")
            elif len(matches) > 1:
                self.report({"WARN"}, ">1 matching wheel found!")
                # TODO: what should we do when >1 wheel matches our os/arch
            
            asset = matches[0]
            wheel = requests.get(asset[1])
            download_path = bpy.context.preferences.addons["lol_blender"].preferences.wheel_download_path
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            wheel_path = os.path.join(download_path, asset[0])
            with open(wheel_path, mode="wb") as f:
                f.write(wheel.content)
            bpy.context.preferences.addons["lol_blender"].preferences.wheel_path = wheel_path

            install_dependencies(wheel_path)
        except (subprocess.CalledProcessError, ImportError, ValueError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # Register the panels, operators, etc. since dependencies are installed
        # for cls in classes:
        #     bpy.utils.register_class(cls)

        return {"FINISHED"}
