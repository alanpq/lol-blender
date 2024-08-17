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

class MenuExportSkinned(ExpandableUi):
    target_id = "TOPBAR_MT_file_export"

    def draw(self, context):
        self.layout.operator(ExportSkinned.bl_idname, text="LoL Skinned Mesh (.skn/.skl)")

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

    def __init__(self):
        self.armature_obj = None

    def invoke(self, context, event):
        try:
            (mesh, armature) = get_mesh_and_armature_from_context(context)
            self.mesh = mesh
            self.armature = armature
        except RuntimeError as e:
            self.report({'ERROR_INVALID_CONTEXT'}, str(e))

        
        self.recall_mode = context.object.mode
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self.properties, "export_skl")

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

    def export_armature(self, context: bpy.types.Context, l: Any, mat):
        influences = list(map(lambda v: get_influences(v, self.mesh), range(len(self.mesh.data.vertices))))

        # we can't just check if a vertex group exists for a bone, because we cap a vertex's influence count to 4,
        # which means there can be a bone that would've been the 5th strongest influence on a vertex,
        # and influence no other vertices - which means that bone should NOT be included in the rig's influence list
        is_influence = {}
        for influence in influences:
            for (bone, _) in influence:
                is_influence[bone] = True

        def map_bone(b: bpy.types.Bone):
            parent = "" if b.parent is None else b.parent.name
            ibm = b.matrix_local
            # local = b.matrix.to_4x4() @ mat
            local = Matrix()
            return (b.name, l.Bone(parent, local, ibm.inverted() @ mat.inverted(), is_influence.get(b.name, False)))


        # map of blender bone names to league influence joint indices
        joint_map = l.export_skl(
            dict(map(map_bone, self.armature.data.bones)),
            bpy.path.ensure_ext(os.path.splitext(self.filepath)[0], ".skl") if self.export_skl else None,
        )

        for i in range(len(influences)):
            influences[i] = list(map(lambda i: (joint_map[i[0]], i[1]), influences[i]))

        return influences


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

        mesh_transformed = False

        try:
            self.mesh.data.transform(mat)
            mesh_transformed = True

            # we need to build the final rig (regardless of if we're actually exporting the arm),
            # in order to get the blend weight indices we need for the skn vert buffer
            influences = self.export_armature(context, l, mat)

            vertices = list(
                map(lambda v: l.Vertex(
                    list(v[1].co.xyz),
                    list(v[1].normal.xyz),
                    list(map(lambda x: x[0], influences[v[0]])),
                    list(map(lambda x: x[1], influences[v[0]])),
                ), enumerate(self.mesh.data.vertices))
            )
            for tri in self.mesh.data.loop_triangles:
                for i, v in enumerate(tri.vertices):
                    vertices[v].normal = list(Vector(tri.split_normals[i]).xyz)
            
            l.export_skn(
                bpy.path.ensure_ext(self.filepath, ".skn"),
                vertices,
                list(map(lambda v: list(v.vertices), self.mesh.data.loop_triangles)),

                influences
            )
        finally:
            if mesh_transformed: # undo transform if we did it
                self.mesh.data.transform(mat.inverted())

        return {'FINISHED'}


