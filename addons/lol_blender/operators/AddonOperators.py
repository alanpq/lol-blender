from typing import Any
import bpy

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs
import mathutils
from bpy_extras.io_utils import axis_conversion

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

class ExportSkinned(bpy.types.Operator):
    """Export skinned mesh w/ rig"""
    bl_idname = "export_mesh.league_skinned"
    bl_label = "Export LoL Skinned Mesh"
    bl_description = "Export the selected object's mesh + skeleton"

    bl_options = {'PRESET'}

    output_name: bpy.props.StringProperty(
        name="Output Name", description="Name of the skn/skl files")
    directory: bpy.props.StringProperty(
        name="Directory", description="Directory of the file", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.recall_mode = context.object.mode
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self.properties, "output_name", icon="FILE_FOLDER")

    def recall(self):
        bpy.ops.object.mode_set(mode=self.recall_mode)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None
    

    def export_armature(self, context: bpy.types.Context, l: Any, obj: bpy.types.Object, armature: bpy.types.Object, mat):
        print("found armature!")
        print(armature)
        # return
        filepath = self.properties.directory

        print("mat: ", mat)

        influences = list(map(lambda v: get_influences(v, obj), range(len(obj.data.vertices))))
        is_influence = {}
        for influence in influences:
            for (bone, _) in influence:
                is_influence[bone] = True

        def map_bone(b: bpy.types.Bone):
            parent = "" if b.parent is None else b.parent.name
            ibm = b.matrix_local
            # local = b.matrix.to_4x4() @ mat
            local = mathutils.Matrix()
            return (b.name, l.Bone(parent, local, ibm.inverted() @ mat.inverted(), is_influence[b.name]))


        # map of blender bone names to league influence joint indices
        joint_map = l.export_skl(
            bpy.path.ensure_ext(filepath, self.output_name + ".skl"),
            dict(map(map_bone, armature.data.bones)),
        )

        for i in range(len(influences)):
            influences[i] = list(map(lambda i: (joint_map[i[0]], i[1]), influences[i]))

        return influences
        # for bone in armature.data.bones:
            # if bone.parent is None:
                # print(bone, '->', bone.)


    def execute(self, context: bpy.types.Context):
        from mathutils import Vector
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, LOLPrefs)

        obj = context.active_object

        # TODO: handle armature selected instead

        if obj.type == "MESH":
            l = modules["league_toolkit"]

            mat = axis_conversion(
                from_forward='-Y',
                from_up='Z',
                to_forward='Z',
                to_up='Y',
            ).to_4x4()

            obj.data.transform(mat)

            
            # Armatures need to be exported and skinned meshes enabled to create a skinned mesh node
            armature = obj.find_armature()
            influences = None
            if armature:
                influences = self.export_armature(context, l, obj, armature, mat)
                print("influences!!", influences)
                # return {'FINISHED'}

            # for i, vert in enumerate(obj.data.vertices):
            #     print(i, vert.index)
            # for tri in obj.data.loop_triangles:
            #     print(tri.vertices[0], tri.vertices[1], tri.vertices[2])
            filepath = self.properties.directory
            vertices = list(
                map(lambda v: l.Vertex(
                    list(v[1].co.xyz),
                    list(v[1].normal.xyz),
                    list(map(lambda x: x[0], influences[v[0]])),
                    list(map(lambda x: x[1], influences[v[0]])),
                ), enumerate(obj.data.vertices))
            )
            for tri in obj.data.loop_triangles:
                for i, v in enumerate(tri.vertices):
                    vertices[v].normal = list(Vector(tri.split_normals[i]).xyz)
            l.export_skn(
                bpy.path.ensure_ext(filepath, self.output_name + ".skn"),
                vertices,
                list(map(lambda v: list(v.vertices), obj.data.loop_triangles)),

                influences
            )
            
            obj.data.transform(mat.inverted())

        return {'FINISHED'}


