from typing import Any

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import axis_conversion, ExportHelper

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import get_modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs
from common.types.framework import ExpandableUi

import os
from mathutils import Vector, Matrix

import itertools

class MenuImportSkinned(ExpandableUi):
    target_id = "TOPBAR_MT_file_import"

    def draw(self, context):
        self.layout.operator(ImportSkinned.bl_idname, text="LoL Skinned Mesh (.skn/.skl)")


class ImportSkinned(bpy.types.Operator, ExportHelper):
    """Import skinned mesh w/ optional rig"""
    bl_idname = "lol_skn_import.operator"
    bl_label = "Import LoL Skinned Mesh"
    bl_description = "Import the selected object's mesh (+ skeleton, if available)"

    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".skn"
    filter_glob: StringProperty( # type: ignore
        default="*.skn;*.skl",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    import_skl: BoolProperty(
        name="Import Skeleton",
        description="Whether to import the .skl, along with the .skn. This will not fail if the .skl cannot be found",
        default=True
    ) # type: ignore

    def __init__(self):
        self.armature_obj = None

    def invoke(self, context, event):
        if context.object is not None:
            self.recall_mode = context.object.mode
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self.properties, "import_skl")

    def recall(self):
        if self.recall_mode is not None:
            bpy.ops.object.mode_set(mode=self.recall_mode)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, LOLPrefs)

        l = get_modules(addon_prefs.wheel_path)["league_toolkit"]

        mat = axis_conversion(
            from_forward='-Y',
            from_up='Z',
            to_forward='Z',
            to_up='Y',
        ).to_4x4()

        try:
            skn = l.import_skn(
                bpy.path.ensure_ext(self.filepath, ".skn"),
            )

            mesh = bpy.data.meshes.new("mesh")
            mesh.from_pydata(
                    list(map(lambda v: v.pos, skn.vertices)),
                    [],
                    list(map(lambda t: (t[0], t[1], t[2]), skn.triangles))
            )
            mesh.normals_split_custom_set_from_vertices(list(map(lambda v: v.normal, skn.vertices)))
            mesh.update()        
            obj = bpy.data.objects.new("obj", mesh)

            vert_groups = {}

            for vert_id, vertex in enumerate(skn.vertices):
                for i in range(4):
                    blend_idx = vertex.blend_indices[i]
                    blend_weight = vertex.blend_weights[i]
                    if blend_weight <= 0.0:
                        continue
                    if blend_idx not in vert_groups:
                        vert_groups[blend_idx] = obj.vertex_groups.new(name = f'{blend_idx}')
                    vert_groups[blend_idx].add((vert_id, ), blend_weight, 'ADD')

            mesh.vertices.add(len(skn.vertices))

            # new_collection = bpy.data.collections.new('new_collection')
            # bpy.context.scene.collection.children.link(new_collection)
            # new_collection.objects.link(obj)
            bpy.context.collection.objects.link(obj)

            # print(skn.vertices)
            # print(skn.triangles)
            # print(skn.influences)
        finally:
            pass

        return {'FINISHED'}


