import bpy

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs
from bpy_extras.io_utils import axis_conversion


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

    def execute(self, context: bpy.types.Context):
        from mathutils import Vector
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, LOLPrefs)

        obj = context.active_object

        # TODO: handle armature selected instead

        if obj.type == "MESH":
            # Armatures need to be exported and skinned meshes enabled to create a skinned mesh node
            for modifier in obj.modifiers:
                # We only need to find one armature to know it should be an armature node
                if modifier.type == 'ARMATURE':
                    print("found armature!")
                    break

            mat = axis_conversion(
                from_forward='-Y',
                from_up='Z',
                to_forward='Z',
                to_up='Y',
            ).to_4x4()

            obj.data.transform(mat)

            # for i, vert in enumerate(obj.data.vertices):
            #     print(i, vert.index)
            # for tri in obj.data.loop_triangles:
            #     print(tri.vertices[0], tri.vertices[1], tri.vertices[2])
            l = modules["league_toolkit"]
            filepath = self.properties.directory
            vertices = list(
                map(lambda v: l.Vertex(list(v.co.xyz), list(v.normal.xyz)), obj.data.vertices))
            for tri in obj.data.loop_triangles:
                for i, v in enumerate(tri.vertices):
                    vertices[v].normal = list(Vector(tri.split_normals[i]).xyz)
            l.export_skn(
                bpy.path.ensure_ext(filepath, self.output_name + ".skn"),
                vertices,
                list(map(lambda v: list(v.vertices), obj.data.loop_triangles)),
            )
            
            obj.data.transform(mat.inverted())

        return {'FINISHED'}
