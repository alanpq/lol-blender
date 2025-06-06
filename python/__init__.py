# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy
import numpy as np

# this is the module from the wheel
import rust_wrap


def read_input(context):
    mesh = context.active_object.data

    vertices = mesh.vertices
    triangles = mesh.loop_triangles

    # feels a bit clunky but is pretty fast
    flat_vertices = np.empty(len(vertices) * 3, dtype="float32")
    flat_triangles = np.empty(len(triangles) * 3, dtype="int32")
    vertices.foreach_get("co", flat_vertices)
    triangles.foreach_get("vertices", flat_triangles)

    return flat_vertices, flat_triangles


def write_output(context, flat_samples):
    # boilerplate to create object and mesh
    new_obj_name = f"{context.active_object.name} - Inside Samples"
    new_mesh_name = f"{context.active_object.data.name} - Inside Samples"

    new_mesh = bpy.data.meshes.get(new_mesh_name)
    if new_mesh is None:
        new_mesh = bpy.data.meshes.new(new_mesh_name)
    new_obj = bpy.data.objects.get(new_obj_name)
    if new_obj is None:
        new_obj = bpy.data.objects.new(new_obj_name, new_mesh)
    if new_obj.name not in context.collection.all_objects:
        context.collection.objects.link(new_obj)

    # actually allocate space and write samples
    new_mesh.clear_geometry()
    new_mesh.vertices.add(len(flat_samples) // 3)
    new_mesh.vertices.foreach_set("co", flat_samples)


class SampleInside(bpy.types.Operator):
    """My Sample Inside Script"""  # Use this as a tooltip for menu items and buttons.

    bl_idname = "object.sample_inside"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Sample Object's Inside"  # Display name in the interface.
    bl_options = {"REGISTER", "UNDO"}  # Enable undo for the operator.

    @classmethod
    def poll(cls, context):
        # Checks to see if there's any active mesh object (selected or in edit mode)
        active_object = context.active_object
        return (
            active_object is not None
            and active_object.type == "MESH"
            and (context.mode == "EDIT_MESH" or active_object.select_get())
        )

    def execute(self, context):  # execute() is called when running the operator.
        flat_vertices, flat_triangles = read_input(context)

        flat_samples = rust_wrap.sample_inside(flat_vertices, flat_triangles)

        write_output(context, flat_samples)

        return {"FINISHED"}  # Lets Blender know the operator finished successfully.


def menu_func(self, _context):
    self.layout.operator(SampleInside.bl_idname)


def register():
    bpy.utils.register_class(SampleInside)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SampleInside)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
