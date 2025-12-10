from typing import Any, Container

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import axis_conversion, ExportHelper

import os
from mathutils import Vector, Matrix, Color

import itertools
import statistics
import re
import random
import numpy as np

import rust_wrap

from ...types import ObjectModeItems

def util_obj_select(context, obj, action = 'SELECT'):
    return obj.select_set(action == 'SELECT')

def util_obj_set_active(context, obj):
    context.view_layer.objects.active = obj


def utils_set_mode(mode):
    if bpy.ops.object.mode_set.poll(): # type: ignore
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
    filter_glob: StringProperty( # type: ignore[misc]
        default="*.skn;*.skl",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    scale_factor: FloatProperty( # type: ignore[misc]
        name = "Scale Factor",
        description="How much to scale everything by when importing (0.01 = 1/100 scale = 100x smaller). Make sure to use the same scale factor when exporting!",
        default=0.01
    )
    

    import_skl: BoolProperty( # type: ignore[misc]
        name="Import Skeleton",
        description="Whether to import the .skl, along with the .skn. This will not fail if the .skl cannot be found",
        default=True
    )
    
    leaf_bone_scale: FloatProperty( # type: ignore[misc]
        name = "Leaf Bone Scale",
        description="How long to make leaf bones, as a % of their parent bone's length",
        default=0.5,
        min=0.0,
    )

    recall_mode: ObjectModeItems
    armature_obj = None

    def invoke(self, context, event): # type: ignore[override]
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

    def execute(self, context: bpy.types.Context): # type: ignore[override]

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

            skn = rust_wrap.import_skn( # type: ignore
                os.path.join(file_head, file_stem + ".skn"),
            )
            
            # import mesh verts/faces
            mesh = bpy.data.meshes.new(file_stem)
            mesh.from_pydata(
                    list(map(lambda v: self.global_mat @ Vector(v), skn.vertex_positions)),
                    [],
                    list(map(lambda t: t, skn.triangles))
            )

            # we don't use global_mat, since normals shouldn't be scaled
            mesh.normals_split_custom_set_from_vertices(list(map(lambda v: self.mat @ Vector(v), skn.vertex_normals)))

            mesh.validate()
            mesh.update()

            mesh_obj = bpy.data.objects.new(f"GEO_{file_stem}", mesh)

            # import uvs
            vert_uvs = list(map(lambda uvs: (uvs[0], uvs[1] * -1.0), skn.vertex_uvs))

            uv = mesh.uv_layers.new(name="UV_0")
            # uv.uv.foreach_set("vector", [uv for pair in [vert_uvs[l.vertex_index] for l in mesh.loops] for uv in pair])

            # import armature
            armature = self.do_skl_import(
                context, skn, mesh_obj, file_stem,
                os.path.join(file_head, file_stem + ".skl")
            ) if self.import_skl else None
            
            # import materials
            mats = {}
            for r in skn.material_ranges:
                if r.material not in mats:
                    mat = bpy.data.materials.get(r.material)
                    if mat is None:
                        mat = bpy.data.materials.new(r.material)
                        mat.use_nodes = True

                    mats[r.material] = len(mesh.materials) 
                    mesh.materials.append(mat)
                # NOTE: why 6? this worked before as 3, which makes sense since 3 verts make a tri...
                for p_idx in range(r.start_index, r.index_count // 6):
                    if p_idx >= len(mesh.polygons):
                        print("[MAT IMPORT] p_idx >= len(mesh.polygons). p_idx =", p_idx)
                        # TODO: better warning
                        break
                    else:
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
                arm_modifier: bpy.types.ArmatureModifier = mesh_obj.modifiers.new( armature.data.name, type = 'ARMATURE') # type: ignore
                arm_modifier.show_expanded = False
                arm_modifier.use_vertex_groups = True
                arm_modifier.use_bone_envelopes = False
                arm_modifier.object = armature
        finally:
            pass

        return {'FINISHED'}

    def do_skl_import(self, context: bpy.types.Context, skn, mesh_obj, file_stem, path: str):
        try:
            skl = rust_wrap.import_skl(path) # type: ignore
            armature_data = bpy.data.armatures.new(file_stem)
            armature_obj = bpy.data.objects.new(f"RIG_{file_stem}", armature_data)
            armature_data.show_axes = False
            armature_obj.show_in_front = True

            context.collection.objects.link(armature_obj)

            # increases performance
            blend_indices = list(skn.vertex_blend_indices)
            blend_weights = list(skn.vertex_blend_weights)

            # set up vertex groups/blend weights
            vert_groups = {}
            for vert in range(len(skn.vertex_normals)):
                for i in range(4):
                    blend_idx = blend_indices[vert*4 + i]
                    blend_weight = blend_weights[vert*4 + i]
                    if blend_weight <= 0.0:
                        continue
                    if blend_idx not in vert_groups:
                        # blend_idx is an index into the .skl's joint influence list,
                        # so we need to get the actual joint index (via influence_lookup).
                        # since we only need the name, the influence_lookup directly gives you the joint name
                        vert_groups[blend_idx] = mesh_obj.vertex_groups.new(name = skl.influence_lookup[blend_idx])
                    vert_groups[blend_idx].add((vert, ), blend_weight, 'ADD')

            # set armature as active and go to edit mode
            # this way we can work with the edit bones
            util_obj_select(context, armature_obj)
            util_obj_set_active(context, armature_obj)
            utils_set_mode('EDIT')

            joints = list(skl.joints)
        
            # joint pass 1 - create all bones, give them names + head matrix
            for joint in joints:
                bone = armature_data.edit_bones.new(joint.name)
                # set a default tail so blender doesn't delete our bone later
                bone.tail = Vector((0.0,0.0,1.0))
                bone.matrix = self.global_mat @ Matrix(joint.ibm).inverted() 

            # joint pass 2 - establish parent-child hierarchy
            for joint in joints:
                bone = armature_data.edit_bones[joint.name]
                parent = None if joint.parent is None else armature_data.edit_bones[joint.parent]

                if parent is not None:
                    bone.parent = parent

            # final bone pass - set tail to average of children, or extrapolate tail from parent if we are leaf bones
            for bone in armature_data.edit_bones:
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

            armature_obj.data = armature_data
            return armature_obj
        except Exception as e:
            utils_set_mode('OBJECT')
            raise e



