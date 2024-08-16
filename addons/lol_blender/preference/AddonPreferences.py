import os

import bpy
from bpy.types import AddonPreferences

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.operators.DownloadDeps import LOL_OT_download_dependencies
from addons.lol_blender.operators.InstallDeps import LOL_OT_install_dependencies
from addons.lol_blender.dependencies import default_dep_path


def factory_update_addon_category(cls, prop):
    def func(self, context):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        cls.bl_category = self[prop]
        bpy.utils.register_class(cls)

    return func


class LOLPrefs(AddonPreferences):
    # this must match the add-on name (the folder name of the unzipped file)
    bl_idname = __addon_name__

    # https://docs.blender.org/api/current/bpy.props.html
    # The name can't be dynamically translated during blender programming running as they are defined
    # when the class is registered, i.e. we need to restart blender for the property name to be correctly translated.
    wheel_path: bpy.props.StringProperty(
        name="Wheel Path",
        subtype='FILE_PATH',
        default=os.environ.get("__LOL_WHEEL_PATH", ''),
    ) # type: ignore

    wheel_download_path: bpy.props.StringProperty(
        name="Dependency Download Path",
        subtype='DIR_PATH',
        default=default_dep_path
    ) # type: ignore

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.label(text="Add-on Preferences View")
        layout.operator(LOL_OT_download_dependencies.bl_idname, icon="IMPORT")
        layout.prop(self, "wheel_download_path")
        layout.prop(self, "wheel_path")
        layout.operator(LOL_OT_install_dependencies.bl_idname, icon="CONSOLE")

