import bpy
from bpy_extras.io_utils import poll_file_object_drop

class IO_FH_skn_skl(bpy.types.FileHandler):
    bl_idname = "IO_FH_lol_skn_skl"
    bl_label = "LoL .skn/.skl"
    bl_import_operator = "lol_skn_import.operator"
    bl_export_operator = "lol_skn_export.operator"
    bl_file_extensions = ".skn;.skl"

    @classmethod
    def poll_drop(cls, context):
        return poll_file_object_drop(context)