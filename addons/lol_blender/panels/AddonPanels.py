import bpy

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import dependencies, get_modules
from addons.lol_blender.operators.AddonOperators import ExportSkinned
from addons.lol_blender.operators.DownloadDeps import LOL_OT_download_dependencies
from common.i18n.i18n import i18n


class ToolkitPanel(bpy.types.Panel):
    bl_label = "League Toolkit"
    bl_idname = "SCENE_PT_league_toolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "LoL"

    def check(self, context: bpy.types.Context):
        return True

    def draw(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        layout = self.layout

        modules = get_modules(addon_prefs.wheel_path)
        league_toolkit = modules.get("league_toolkit", None)

        if league_toolkit is None:
            layout.operator(LOL_OT_download_dependencies.bl_idname, icon="CONSOLE")
            layout.label(text=f"Dependencies not installed!")
            return
            
        layout.label(text=f"Toolkit version: {league_toolkit.version()}")
        layout.separator()

        row = layout.row()

        layout.operator(ExportSkinned.bl_idname)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None
