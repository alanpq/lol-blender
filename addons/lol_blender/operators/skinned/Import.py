from typing import Any

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import axis_conversion, ExportHelper

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import get_modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs
from common.types.framework import ExpandableUi

import os
from mathutils import Vector, Matrix, Color

import itertools
import statistics
import re
import random
import numpy as np

class MenuImportSkinned(ExpandableUi):
    target_id = "TOPBAR_MT_file_import"

    def draw(self, context):
        self.layout.operator(ImportSkinned.bl_idname, text="LoL Skinned Mesh (.skn/.skl)")



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

    scale_factor: FloatProperty(
        name = "Scale Factor",
        description="How much to scale everything by when importing (0.01 = 1/100 scale = 100x smaller). Make sure to use the same scale factor when exporting!",
        default=0.01
    )
    

    import_skl: BoolProperty(
        name="Import Skeleton",
        description="Whether to import the .skl, along with the .skn. This will not fail if the .skl cannot be found",
        default=True
    ) # type: ignore
    leaf_bone_scale: FloatProperty(
        name = "Leaf Bone Scale",
        description="How long to make leaf bones, as a % of their parent bone's length",
        default=0.5,
        min=0.0,
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
        layout.prop(self.properties, "scale_factor")

        skl_box = layout.box()
        skl_box.prop(self.properties, "import_skl")
        col = skl_box.column()
        col.enabled = self.import_skl
        col.prop(self.properties, "leaf_bone_scale")

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

        self.mat = axis_conversion(
            from_forward='-Y',
            from_up='Z',
            to_forward='Z',
            to_up='Y',
        ).to_4x4().inverted()

        # the general transform from LoL space -> Blender space
        self.global_mat = self.mat @ Matrix.Scale(self.scale_factor, 4)

        try:
            utils_set_mode('OBJECT')

            (file_head, file_base) = os.path.split(self.filepath)
            file_stem = os.path.splitext(file_base)[0]

            skn = l.import_skn(
                os.path.join(file_head, file_stem + ".skn"),
            )
            
            # import mesh verts/faces
            mesh = bpy.data.meshes.new(file_stem)
            mesh.from_pydata(
                    list(map(lambda v: self.global_mat @ Vector(v.pos), skn.vertices)),
                    [],
                    list(map(lambda t: t, skn.triangles))
            )

            # we don't use global_mat, since normals shouldn't be scaled
            mesh.normals_split_custom_set_from_vertices(list(map(lambda v: self.mat @ Vector(v.normal), skn.vertices)))

            mesh.validate()
            mesh.update()

            mesh_obj = bpy.data.objects.new(f"GEO_{file_stem}", mesh)

            # import uvs
            vert_uvs = list(map(lambda v: v.uvs, skn.vertices))

            uv = mesh.uv_layers.new(name="UV_0")
            uv.uv.foreach_set("vector", [uv for pair in [vert_uvs[l.vertex_index] for l in mesh.loops] for uv in pair])

            # import armature
            armature = self.do_skl_import(
                l, context, skn, mesh_obj, file_stem,
                os.path.join(file_head, file_stem + ".skl")
            ) if self.import_skl else None
            
            # import materials
            mats = {}
            for r in skn.material_ranges:
                if r.material not in mats:
                    matdata = bpy.data.materials.get(r.material)
                    if matdata is None:
                        matdata = bpy.data.materials.new(r.material)
                        matdata.diffuse_color = (random.random(), random.random(), random.random(), 1.0)
                    mats[r.material] = len(mesh.materials) 
                    mesh.materials.append(matdata)
                for p_idx in range(r.start_index, r.index_count // 3):
                    p = mesh.polygons[p_idx]
                    p.material_index = mats[r.material]

            # new_collection = bpy.data.collections.new('new_collection')
            # context.scene.collection.children.link(new_collection)
            # new_collection.objects.link(obj)
            context.collection.objects.link(mesh_obj)
            
            if armature is not None:
                # parenting mesh to armature object
                mesh_obj.parent = armature
                mesh_obj.parent_type = 'OBJECT'

                # add armature modifier
                arm_modifier = mesh_obj.modifiers.new( armature.data.name, type = 'ARMATURE')
                arm_modifier.show_expanded = False
                arm_modifier.use_vertex_groups = True
                arm_modifier.use_bone_envelopes = False
                arm_modifier.object = armature
        finally:
            pass

        return {'FINISHED'}

    def do_skl_import(self, l, context: bpy.types.Context, skn, mesh_obj, file_stem, path: str):
        try:
            skl = l.import_skl(path)
            armature_data = bpy.data.armatures.new(file_stem)
            armature_obj = bpy.data.objects.new(f"RIG_{file_stem}", armature_data)
            armature_data.show_axes = False
            armature_obj.show_in_front = True

            context.collection.objects.link(armature_obj)

            # set up vertex groups/blend weights
            vert_groups = {}
            for vert_id, vertex in enumerate(skn.vertices):
                for i in range(4):
                    blend_idx = vertex.blend_indices[i]
                    blend_weight = vertex.blend_weights[i]
                    if blend_weight <= 0.0:
                        continue
                    if blend_idx not in vert_groups:
                        # blend_idx is an index into the .skl's joint influence list,
                        # so we need to get the actual joint index (via influence_lookup).
                        # since we only need the name, the influence_lookup directly gives you the joint name
                        vert_groups[blend_idx] = mesh_obj.vertex_groups.new(name = skl.influence_lookup[blend_idx])
                    vert_groups[blend_idx].add((vert_id, ), blend_weight, 'ADD')

            # set armature as active and go to edit mode
            # this way we can work with the edit bones
            util_obj_select(context, armature_obj)
            util_obj_set_active(context, armature_obj)
            utils_set_mode('EDIT')
        
            # joint pass 1 - create all bones, give them names + head matrix
            for joint in skl.joints:
                bone = armature_obj.data.edit_bones.new(joint.name)
                # set a default tail so blender doesn't delete our bone later
                bone.tail = Vector((0.0,0.0,1.0))
                bone.matrix = self.global_mat @ Matrix(joint.ibm).inverted() 

            # joint pass 2 - establish parent-child hierarchy
            for joint in skl.joints:
                bone = armature_obj.data.edit_bones[joint.name]
                parent = None if joint.parent is None else armature_obj.data.edit_bones[joint.parent]

                if parent is not None:
                    bone.parent = parent

            # final bone pass - set tail to average of children, or extrapolate tail from parent if we are leaf bones
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
            return armature_obj
        except e:
            utils_set_mode('OBJECT')
            raise e



