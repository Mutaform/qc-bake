# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - operators package

import bpy

from .create import QCBAKE_OT_create_namepair
from .organize import QCBAKE_OT_organize
from .swap import QCBAKE_OT_swap
from .visibility import QCBAKE_OT_toggle_visibility

classes = (
    QCBAKE_OT_create_namepair,
    QCBAKE_OT_swap,
    QCBAKE_OT_toggle_visibility,
    QCBAKE_OT_organize,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
