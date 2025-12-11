from typing import Any

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import axis_conversion, ExportHelper

import os
from mathutils import Vector, Matrix

import functools
import operator
import numpy as np

from ... import types

import rust_wrap

def get_weight(group: bpy.types.VertexGroup, idx):
    try:
        return group.weight(idx)
    except:
        return 0.0

def get_influences(vert_idx, object: bpy.types.Object):
    return list(sorted(
        map(lambda g: (g[0], get_weight(g[1],vert_idx)), object.vertex_groups.items()),
        key=lambda x: -x[1]
    )[:4])

def get_armature_for_mesh(mesh):
    modifiers = [x for x in mesh.modifiers if x.type == "ARMATURE"]
    if len(modifiers) == 0:
        raise RuntimeError("Mesh must have an armature")
    if len(modifiers) > 1:
        raise RuntimeError("Mesh must have only one armature modifier")
    return modifiers[0].object

def get_mesh_and_armature_from_context(context) -> tuple[bpy.types.Object, bpy.types.Object]:
    if len(context.view_layer.objects.selected) == 0:
        raise RuntimeError("At least one object must be selected")
    
    mesh = None
    armature = None
    for obj in context.view_layer.objects.selected:
        if obj.type == "MESH":
            if mesh is not None:
                raise RuntimeError("No more than one mesh can be selected")
            mesh = obj
        elif obj.type == "ARMATURE":
            if armature is not None:
                raise RuntimeError("No more than one armature can be selected")
            armature = obj
    
    if mesh is None and armature is None:
        raise RuntimeError("An armature/mesh must be selected")

    if mesh:
        mesh_arm = get_armature_for_mesh(mesh)
        if armature is not None and mesh_arm != armature:
            raise RuntimeError("Selected mesh must have the same armature as the selected armature")
        armature = mesh_arm

    # get armature's mesh (if we don't already have it)
    if armature and mesh is None:
        for child in armature.children_recursive:
            if child.type == "MESH":
                if mesh is not None:
                    raise RuntimeError("Armature must have only one mesh associated")
                mesh_arm = get_armature_for_mesh(child)
                if mesh_arm == armature:
                    mesh = child
    
    if mesh is None or armature is None:
        print("SOMEHOW COULDNT FIND MESH/ARMATURE - ", (mesh, armature))
        raise RuntimeError("Somehow couldn't find either mesh/armature")
    return (mesh, armature)

def compute_bone_transforms(armature_obj, bone, axis_correct):
    original_mode = armature_obj.mode
    
    bpy.ops.object.mode_set(mode='OBJECT')

    # WORLD World Space – The most global space in Blender.
    #
    # POSE Pose Space – The pose space of a bone (its armature’s object space).
    #
    # LOCAL_WITH_PARENT Local With Parent – The rest pose local space of a bone (this matrix includes parent transforms).
    #
    # LOCAL Local Space – The local space of an object/bone.

    # local = armature_obj.convert_space(pose_bone=bone, matrix=bone.matrix_basis, from_space='LOCAL_WITH_PARENT', to_space='LOCAL');
    if bone.bone.parent is None:
        local = bone.bone.matrix_local# @ axis_correct
    else:
        # local = bone.bone.parent.matrix_local.inverted() @ bone.bone.matrix_local
        local = axis_correct @ bone.bone.parent.matrix_local.inverted() @ bone.bone.matrix_local 

    ibm = bone.bone.matrix_local.inverted()
    if original_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode=original_mode)

    return local @ axis_correct.inverted(), ibm @ axis_correct.inverted()
    # return local @ axis_correct, ibm @ axis_correct 
    # return axis_correct @ local, axis_correct @ ibm

class ExportSkinned(bpy.types.Operator, ExportHelper):
    """Export skinned mesh w/ rig"""
    bl_idname = "lol_skn_export.operator"
    bl_label = "Export LoL Skinned Mesh"
    bl_description = "Export the selected object's mesh + skeleton"

    bl_options = {'INTERNAL',  'PRESET', 'UNDO'}

    filename_ext = ".skn"

    filter_glob: StringProperty( # type: ignore
        default="*.skn;*.skl",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    export_skl: BoolProperty(
        name="Export Skeleton",
        description="Whether to export the armature as a .skl, alongside the .skn",
        default=True
    ) # type: ignore

    scale_factor: FloatProperty( # type: ignore[misc]
        name = "Scale Factor",
        description="How much to scale everything up by when exporting (0.01 = 1/100 scale = 100x smaller). This is the inverse of the scale factor used on import! (1/x)",
        default=10
    )

    recall_mode: types.ObjectModeItems
    armature_obj = None

    def invoke(self, context, event) -> set[types.OperatorReturnItems]:
        try:
            (mesh, armature) = get_mesh_and_armature_from_context(context)
            self.mesh = mesh
            self.armature = armature
        except RuntimeError as e:
            self.report({'ERROR_INVALID_CONTEXT'}, str(e))

        if context.object is None:
            return {'RUNNING_MODAL'}
        self.recall_mode = context.object.mode
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self.properties, "export_skl")
        layout.prop(self.properties, "scale_factor")

    def recall(self):
        bpy.ops.object.mode_set(mode=self.recall_mode)

    @classmethod
    def poll(cls, context):
        try:
            get_mesh_and_armature_from_context(context)
        except RuntimeError as e:
            cls.poll_message_set(str(e))
            return False
        return True

    def export_armature(self, context: bpy.types.Context, mat):
        assert isinstance(self.mesh.data, bpy.types.Mesh)

        influences = list(map(lambda v: get_influences(v, self.mesh), range(len(self.mesh.data.vertices))))

        # we can't just check if a vertex group exists for a bone, because we cap a vertex's influence count to 4,
        # which means there can be a bone that would've been the 5th strongest influence on a vertex,
        # and influence no other vertices - which means that bone should NOT be included in the rig's influence list
        is_influence = {}
        for influence in influences:
            for (bone, _) in influence:
                is_influence[bone] = True

        def map_bone(b: bpy.types.PoseBone):
            parent = "" if b.bone.parent is None else b.bone.parent.name
            local, ibm = compute_bone_transforms(self.armature, b, mat)
            return (b.bone.name, rust_wrap.Bone(parent, local, ibm, is_influence.get(b.name, False))) # type: ignore


        # map of blender bone names to league influence joint indices
        joint_map = rust_wrap.export_skl( # type: ignore
            dict(map(map_bone, self.armature.pose.bones)),
            bpy.path.ensure_ext(os.path.splitext(self.filepath)[0], ".skl") if self.export_skl else None,
        )

        for i in range(len(influences)):
            influences[i] = list(map(lambda i: (joint_map[i[0]], i[1]), influences[i]))

        return influences


    def execute(self, context: bpy.types.Context):  # type: ignore[override]
        assert isinstance(self.mesh.data, bpy.types.Mesh)

        mat = axis_conversion(
            from_forward='-Y',
            from_up='Z',
            to_forward='Z',
            to_up='Y',
        ).to_4x4() @ Matrix.Scale(self.scale_factor, 4)

        mesh_transformed = False

        try:
            self.mesh.data.transform(mat)
            mesh_transformed = True

            # we need to build the final rig (regardless of if we're actually exporting the arm),
            # in order to get the blend weight indices we need for the skn vert buffer
            influences = self.export_armature(context, mat)

            # vertices = list(
            #     map(lambda v: rust_wrap.Vertex( # type: ignore
            #         list(v[1].co.xyz), # type: ignore
            #         list(v[1].normal.xyz), # type: ignore
            #         list(map(lambda x: x[0], influences[v[0]])),
            #         list(map(lambda x: x[1], influences[v[0]])),
            #     ), enumerate(self.mesh.data.vertices))
            # )

            v_positions     = list(map(lambda v:     list(v.co.xyz), self.mesh.data.vertices)) # type: ignore
            v_normals       = list(map(lambda v: list(v.normal.xyz), self.mesh.data.vertices)) # type: ignore
            v_blend_indices = list(map(lambda v: list(map(lambda x: x[0], influences[v])), range(len(self.mesh.data.vertices))))
            v_blend_weights = list(map(lambda v: list(map(lambda x: x[1], influences[v])), range(len(self.mesh.data.vertices))))
            # v_blend_indices = [[0.0]*4] * (len(self.mesh.data.vertices))
            # v_blend_weights =  [[0.0]*4] * (len(self.mesh.data.vertices))

            for tri in self.mesh.data.loop_triangles:
                for i, v in enumerate(tri.vertices):
                    v_normals[v] = list(Vector(tri.split_normals[i]).xyz) # type: ignore
            
            rust_wrap.export_skn( # type: ignore
                bpy.path.ensure_ext(self.filepath, ".skn"),
                np.array(v_positions, np.float32).ravel(),
                np.array(v_normals, np.float32).ravel(),
                np.array(v_blend_indices, np.uint8).ravel(),
                np.array(v_blend_weights, np.float32).ravel(),
                np.array([], np.uint8), # vert uvs
                np.array(list(map(lambda v: list(v.vertices), self.mesh.data.loop_triangles)), np.int64).ravel(),
            )
        finally:
            pass
            if mesh_transformed: # undo transform if we did it
                self.mesh.data.transform(mat.inverted())

        return {'FINISHED'}

