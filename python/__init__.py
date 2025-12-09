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


from .operators.skinned import IO_FH_skn_skl
from .operators.skinned.Import import ImportSkinned
# from .operators.skinned.Export import ExportSkinned

import rust_wrap


def menu_func(self, context):
    self.layout.operator(ImportSkinned.bl_idname, text="LoL Skinned Mesh (.skn/.skl)")

def register():
    bpy.utils.register_class(IO_FH_skn_skl)
    bpy.utils.register_class(ImportSkinned)
    # bpy.utils.register_class(ExportSkinned)
    
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_class(IO_FH_skn_skl)
    bpy.utils.unregister_class(ImportSkinned)
    # bpy.utils.unregister_class(ExportSkinned)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
