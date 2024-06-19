import bpy

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import dependencies, modules
from addons.lol_blender.operators.AddonOperators import ExportSkinned
from addons.lol_blender.operators.InstallDeps import LOL_OT_install_dependencies
from common.i18n.i18n import i18n

from addons.lol_blender.toolkit import get_toolkit


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

        layout.operator(LOL_OT_install_dependencies.bl_idname, icon="CONSOLE")
        for dependency in dependencies:
            if not dependency.module in modules:
                layout.label(text=f"Dependencies not installed!")
                return

        layout.label(text=i18n("Toolkit Library") + ": ")
        layout.prop(addon_prefs, "toolkit_path")
        toolkit = get_toolkit()
        if len(addon_prefs.toolkit_version) <= 1:
            layout.label(text="Invalid toolkit library")
        else:
            layout.label(text=f"Toolkit version: {toolkit.version}")
        league_toolkit = modules["league_toolkit"]
        layout.label(text=f"Real toolkit version: {league_toolkit.version()}")
        layout.separator()

        row = layout.row()

        layout.operator(ExportSkinned.bl_idname)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None
