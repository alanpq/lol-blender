import bpy

from addons.lol_blender.config import __addon_name__
from addons.lol_blender.dependencies import modules
from addons.lol_blender.preference.AddonPreferences import LOLPrefs


class ExportSkinned(bpy.types.Operator):
    """Export skinned mesh w/ rig"""
    bl_idname = "export_mesh.league_skinned"
    bl_label = "Export LoL Skinned Mesh"
    bl_description = "Export the selected object's mesh + skeleton"

    bl_options = {'PRESET'}

    output_name: bpy.props.StringProperty(
        name="Output Name", description="Name of the skn/skl files")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, LOLPrefs)
        # use operator
        # bpy.ops.transform.resize(value=(2, 2, 2))

        # manipulate the scale directly

        obj = context.active_object

        # TODO: handle armature selected instead

        if obj.type == "MESH":
            # Armatures need to be exported and skinned meshes enabled to create a skinned mesh node
            for modifier in obj.modifiers:
                # We only need to find one armature to know it should be an armature node
                if modifier.type == 'ARMATURE':
                    print("found armature!")
                    break
            # for i, vert in enumerate(obj.data.vertices):
            #     print(i, vert.index)
            # for tri in obj.data.loop_triangles:
            #     print(tri.vertices[0], tri.vertices[1], tri.vertices[2])
            l = modules["league_toolkit"]
            l.export_skn(
                list(map(lambda v: l.Vertex(list(v.co)), obj.data.vertices))
            )

        return {'FINISHED'}
