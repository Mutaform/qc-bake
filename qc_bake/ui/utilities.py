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
        settings = context.scene.qc_bake

        layout.label(text="Group Reduction")
        reduce_box = layout.column(align=True)
        reduce_box.prop(settings, "reduce_group_prefix", text="Prefix")
        reduce_box.prop(settings, "reduce_min_gap", text="Minimum Gap")

        row = layout.row(align=True)
        row.scale_y = 1.25
        row.operator("qcbake.reduce_groups",
                     text="Reduce Bake Groups",
                     icon=icons.ICON_UTIL_REDUCE)
        restore_sub = row.row(align=True)
        restore_sub.enabled = bool(
            bpy.ops.qcbake.restore_reduce_groups.poll())
        restore_sub.operator("qcbake.restore_reduce_groups",
                             text="", icon=icons.ICON_UTIL_RESTORE)

        layout.separator()

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
