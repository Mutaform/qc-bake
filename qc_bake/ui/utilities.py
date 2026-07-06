# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - Utilities sub-panel
# -----------------------------
# A collapsible sub-panel under the main QC Bake panel holding scene
# organisation utilities: two converters that rearrange named bake objects
# into either a flat (High / Low / Cage) or per-asset (Bake_<name>) collection
# layout under a single "Bake Group" head collection.

import bpy
from bpy.types import Panel

from .. import icons

TAB_CATEGORY = "QC Bake"


class QCBAKE_PT_utilities(Panel):
    bl_idname = "QCBAKE_PT_utilities"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_CATEGORY
    bl_parent_id = "QCBAKE_PT_main"
    bl_label = "Utilities"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2  # Visibility, then Utilities

    def draw_header(self, context):
        self.layout.label(text="", icon=icons.ICON_UTIL_ORGANIZE)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Collection Layout")
        col = layout.column(align=True)
        col.scale_y = 1.3
        op = col.operator("qcbake.organize",
                          text="Flat  ( High / Low )",
                          icon=icons.ICON_UTIL_FLAT)
        op.layout_mode = 'FLAT'
        op = col.operator("qcbake.organize",
                          text="Per Asset  ( Bake_name )",
                          icon=icons.ICON_UTIL_PERASSET)
        op.layout_mode = 'PER_ASSET'

        info = layout.column(align=True)
        info.scale_y = 0.85
        info.label(text="Head: 'Bake Group'", icon='INFO')
        info.label(text="Picked by name suffix only")


classes = (
    QCBAKE_PT_utilities,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
