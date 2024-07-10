import bpy

from lol_blender.addons.lol_blender.config import __addon_name__
from lol_blender.addons.lol_blender.i18n.dictionary import dictionary
from lol_blender.common.class_loader import auto_load
from lol_blender.common.class_loader.auto_load import add_properties, remove_properties
from lol_blender.common.i18n.dictionary import common_dictionary
from lol_blender.common.i18n.i18n import load_dictionary

# Add-on info
bl_info = {
    "name": "Basic Add-on Sample",
    "author": "[You name]",
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "description": "This is a template for building addons",
    "warning": "",
    "doc_url": "[documentation url]",
    "tracker_url": "[contact email]",
    "support": "COMMUNITY",
    "category": "3D View"
}

_addon_properties = {}


# You may declare properties like following, framework will automatically add and remove them.
# Do not define your own property group class in the __init__.py file. Define it in a separate file and import it here.
# _addon_properties = {
#     bpy.types.Scene: {
#         "property_name": bpy.props.StringProperty(name="property_name"),
#     },
# }

# Best practice: Please do not define Blender classes in the __init__.py file.
# Define them in separate files and import them here. This is because the __init__.py file would be copied during
# addon packaging, and defining Blender classes in the __init__.py file may cause unexpected problems.
def register():
    print("registering")
    # Register classes
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    print("{} addon is installed.".format(bl_info["name"]))


def unregister():
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    # unRegister classes
    auto_load.unregister()
    remove_properties(_addon_properties)

    print("{} addon is uninstalled.".format(bl_info["name"]))
