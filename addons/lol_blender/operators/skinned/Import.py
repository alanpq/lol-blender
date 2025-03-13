from typing import Any

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import axis_conversion, ExportHelper

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import get_modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs
from common.types.framework import ExpandableUi

import os
from mathutils import Vector, Matrix

import itertools
import statistics
import re

class MenuImportSkinned(ExpandableUi):
    target_id = "TOPBAR_MT_file_import"

    def draw(self, context):
        self.layout.operator(ImportSkinned.bl_idname, text="LoL Skinned Mesh (.skn/.skl)")



def util_obj_select(context, obj, action = 'SELECT'):
    # if obj.name in bpy.data.scenes[0].view_layers[0].objects:
    # print(obj.name)
    # print(list(context.view_layer.objects))
    # if obj.name in context.view_layer.objects:
    return obj.select_set(action == 'SELECT')
    # else:
    #     print('Warning: util_obj_select: Object not in "context.view_layer.objects"')

def util_obj_set_active(context, obj):
    context.view_layer.objects.active = obj


def utils_set_mode(mode):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode = mode, toggle = False)
    # else:
        # bpy.ops.object.mode_set(mode = mode, toggle = False)
        #dev

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

    leaf_bone_scale: FloatProperty(
        name = "Leaf Bone Scale",
        description="How long to make leaf joint bones, as a % of their parent bone's length",
        default=0.5
    )

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
        layout.prop(self.properties, "leaf_bone_scale")

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
        ).to_4x4().inverted()

        try:
            utils_set_mode('OBJECT')
            print(self.filepath)
            # TODO: make skl import optional
            skl = l.import_skl(
                bpy.path.ensure_ext(re.sub('skn$', 'skl', self.filepath), ".skl")
            )
            
            armature_data = bpy.data.armatures.new("armature_data")
            armature_obj = bpy.data.objects.new("armature_obj", armature_data)
            # TODO: options for axes and x_ray?
            armature_data.show_axes = False

            armature_data.display_type = 'STICK'
            armature_obj.show_in_front = True

            context.collection.objects.link(armature_obj)


            skn = l.import_skn(
                bpy.path.ensure_ext(re.sub('skl$', 'skn', self.filepath), ".skn"),
            )

            mesh = bpy.data.meshes.new("mesh")
            mesh.from_pydata(
                    list(map(lambda v: mat @ Vector(v.pos), skn.vertices)),
                    [],
                    list(map(lambda t: (t[0], t[1], t[2]), skn.triangles))
            )
            mesh.normals_split_custom_set_from_vertices(list(map(lambda v: mat @ Vector(v.normal), skn.vertices)))
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
                        vert_groups[blend_idx] = obj.vertex_groups.new(name = skl.influence_lookup[blend_idx])
                    vert_groups[blend_idx].add((vert_id, ), blend_weight, 'ADD')

            mesh.vertices.add(len(skn.vertices))

            util_obj_select(context, armature_obj)
            util_obj_set_active(context, armature_obj)
            utils_set_mode('EDIT')
            
            for b in skl.bones:
                edit_bone = armature_obj.data.edit_bones.new(b.name)
                edit_bone.tail = Vector((0.0, 1.0, 0.0))
                edit_bone.matrix = mat @ Matrix(b.ibm).inverted() 

            for b in skl.bones:
                bone = armature_obj.data.edit_bones[b.name]
                parent = None if b.parent is None else armature_obj.data.edit_bones[b.parent]

                if parent is not None:
                    bone.parent = parent

            for bone in armature_obj.data.edit_bones:
                mean = Vector()
                children = bone.children
                if len(children) == 0:
                    if bone.parent is not None:
                        bone.tail = bone.head + ((bone.head - bone.parent.head) * self.leaf_bone_scale)
                    continue
                for child in children:
                    mean += child.head
                bone.tail = mean / len(children)
            utils_set_mode('OBJECT')

            # new_collection = bpy.data.collections.new('new_collection')
            # context.scene.collection.children.link(new_collection)
            # new_collection.objects.link(obj)
            context.collection.objects.link(obj)

            # parenting mesh to armature object
            obj.parent = armature_obj
            obj.parent_type = 'OBJECT'
            
            # add armature modifier
            arm_modifier = obj.modifiers.new( armature_obj.data.name, type = 'ARMATURE')
            arm_modifier.show_expanded = False
            arm_modifier.use_vertex_groups = True
            arm_modifier.use_bone_envelopes = False
            arm_modifier.object = armature_obj

            # print(skn.vertices)
            # print(skn.triangles)
            # print(skn.influences)
        finally:
            pass

        return {'FINISHED'}


