import os

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import AddonPreferences

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.operators.InstallDeps import LOL_OT_install_dependencies
from addons.lol_blender.toolkit import load_toolkit_lib, Toolkit, get_toolkit


def factory_update_addon_category(cls, prop):
    def func(self, context):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        cls.bl_category = self[prop]
        bpy.utils.register_class(cls)

    return func


def switch_toolkit_lib(self, context):
    load_toolkit_lib(self.toolkit_path)


def get_toolkit_lib(self):
    toolkit = get_toolkit()
    if toolkit is None:
        return ""
    return str(toolkit.version)


class LOLPrefs(AddonPreferences):
    # this must match the add-on name (the folder name of the unzipped file)
    bl_idname = __addon_name__

    # https://docs.blender.org/api/current/bpy.props.html
    # The name can't be dynamically translated during blender programming running as they are defined
    # when the class is registered, i.e. we need to restart blender for the property name to be correctly translated.
    toolkit_path: StringProperty(
        name="Library Path",
        subtype='FILE_PATH',
        default='X:\Documents\Projects\lol-blender\lib.dll',
        update=switch_toolkit_lib
    )

    wheel_path: StringProperty(
        name="Wheel Path",
        subtype='FILE_PATH',
        default='X:\\Documents\\Projects\\lol-blender\\bindings\\target\\wheels\\league_toolkit-0.1.0-cp311-none-win_amd64.whl',
    )

    toolkit_version: StringProperty(name="Toolkit Version", get=get_toolkit_lib)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.label(text="Add-on Preferences View")
        layout.prop(self, "toolkit_path")
        layout.prop(self, "wheel_path")
        layout.operator(LOL_OT_install_dependencies.bl_idname, icon="CONSOLE")
