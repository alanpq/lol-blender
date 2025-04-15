from typing import Any
import typing

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import axis_conversion, ExportHelper

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import get_modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs
from common.types.framework import ExpandableUi

import os
from mathutils import Vector, Matrix, Color
from math import sin

import itertools
import statistics
import re
import random
import numpy as np

class MenuImportAnimation(ExpandableUi):
    target_id = "TOPBAR_MT_file_import"

    def draw(self, context):
        self.layout.operator(ImportAnimation.bl_idname, text="LoL Animation (.anm)")


def util_obj_select(context, obj, action = 'SELECT'):
    return obj.select_set(action == 'SELECT')

def util_obj_set_active(context, obj):
    context.view_layer.objects.active = obj


def utils_set_mode(mode):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode = mode, toggle = False)
    # else:
        # bpy.ops.object.mode_set(mode = mode, toggle = False)
        #dev

class ImportAnimation(bpy.types.Operator, ExportHelper):
    """Import a League of Legends animation"""
    bl_idname = "lol_anm_import.operator"
    bl_label = "Import LoL Animation"
    bl_description = "Import a League of Legends animation"

    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".anm"
    filter_glob: StringProperty( # type: ignore
        default="*.anm",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def __init__(self):
        self.armature_obj = None

    def invoke(self, context, event):
        if context.object is not None:
            self.recall_mode = context.object.mode

        # Make sure the selected object is an obj.
        active_object = context.view_layer.objects.active
        if active_object is None or active_object.type != 'ARMATURE':
            self.report({'ERROR_INVALID_CONTEXT'}, 'The active object must be an armature')
            return {'CANCELLED'}

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}



    def draw(self, context):
        layout = self.layout

    def recall(self):
        if self.recall_mode is not None:
            bpy.ops.object.mode_set(mode=self.recall_mode)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, LOLPrefs)

        self.mat = axis_conversion(
            from_forward='-Y',
            from_up='Z',
            to_forward='Z',
            to_up='Y',
        ).to_4x4().inverted()

        l = get_modules(addon_prefs.wheel_path)["league_toolkit"]
        anm = l.import_anm(self.filepath)

        armature_obj = context.view_layer.objects.active
        # safety: we check the active object's type to be 'ARMATURE' in invoke()
        armature_data = typing.cast(bpy.types.Armature, armature_obj.data)

        action_name = "COCK"

        # TODO: make this operator setting
        should_overwrite = True
        if should_overwrite and action_name in bpy.data.actions:
            action = bpy.data.actions[action_name]
        else:
            action = bpy.data.actions.new(name=action_name)

        # Remove existing f-curves.
        action.fcurves.clear()

        fcurves = {}

        # Create f-curves for the rotation and location of each bone.
        for (name, pose_bone) in armature_obj.pose.bones.items():
            rotation_data_path = pose_bone.path_from_id('rotation_quaternion')
            location_data_path = pose_bone.path_from_id('location')
            scale_data_path = pose_bone.path_from_id('scale')
            fcurves[name] = [
                action.fcurves.new(location_data_path, index=0, action_group=pose_bone.name),  # Lx
                action.fcurves.new(location_data_path, index=1, action_group=pose_bone.name),  # Ly
                action.fcurves.new(location_data_path, index=2, action_group=pose_bone.name),  # Lz
                # note: blender does wxyz, we do xyzw
                action.fcurves.new(rotation_data_path, index=1, action_group=pose_bone.name),  # Qx
                action.fcurves.new(rotation_data_path, index=2, action_group=pose_bone.name),  # Qy
                action.fcurves.new(rotation_data_path, index=3, action_group=pose_bone.name),  # Qz
                action.fcurves.new(rotation_data_path, index=0, action_group=pose_bone.name),  # Qw
                action.fcurves.new(scale_data_path, index=0, action_group=pose_bone.name),  # Sx
                action.fcurves.new(scale_data_path, index=1, action_group=pose_bone.name),  # Sy
                action.fcurves.new(scale_data_path, index=2, action_group=pose_bone.name),  # Sz
            ]

        effective_fps = context.scene.render.fps / context.scene.render.fps_base
        fps_ratio = effective_fps / anm.fps
        print(f"effective_fps: {effective_fps}")
        print(f"real_fps: {anm.fps}")
        print(f"ratio: {fps_ratio}")

        for bone_name, bone in armature_obj.pose.bones.items():
            print(bone.lol_name_hash)
            if bone.lol_name_hash is None:
                continue
            if bone.lol_name_hash not in anm.joint_anms:
                continue
            joint = anm.joint_anms[bone.lol_name_hash]
            # print(bone_name, ":")
            for i, fcurve in enumerate(fcurves[bone_name]):
                fcurve.keyframe_points.add(len(joint[i])//2)
                fcurve.keyframe_points.foreach_set("co", joint[i])


        print(anm.fps)



        return {'FINISHED'}
