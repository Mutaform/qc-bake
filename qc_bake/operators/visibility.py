# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - visibility operator

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from .. import core


class QCBAKE_OT_toggle_visibility(Operator):
    """Show or hide all renamed high/low/cage objects"""
    bl_idname = "qcbake.toggle_visibility"
    bl_label = "Toggle Renamed Objects"
    bl_options = {'INTERNAL', 'UNDO'}

    group: EnumProperty(
        items=[
            ('HIGH', "High polys", "High"),
            ('LOW', "Low polys", "Low"),
            ('CAGE', "Cages", "Cage"),
            ('ALL', "All renamed", "All"),
        ]
    )
    action: EnumProperty(
        items=[
            ('SHOW', "Show", "Show"),
            ('HIDE', "Hide", "Hide"),
        ]
    )

    def execute(self, context):
        settings = context.scene.qc_bake
        low_suf, high_suf, cage_suf = core.get_suffixes(settings)

        if self.group == 'HIGH':
            suffixes = (high_suf,)
        elif self.group == 'LOW':
            suffixes = (low_suf,)
        elif self.group == 'CAGE':
            suffixes = (cage_suf,) if cage_suf else ()
        else:
            suffixes = tuple(s for s in (low_suf, high_suf, cage_suf) if s)

        if not suffixes:
            self.report({'WARNING'}, "No suffix defined for this group.")
            return {'CANCELLED'}

        # Group-suffixed multi-high objects end with e.g. "_high_01".
        hide = self.action == 'HIDE'
        for obj in bpy.data.objects:
            name = obj.name
            match = any(
                name.endswith(s) or ("%s_" % s) in name
                for s in suffixes
            )
            if match:
                obj.hide_set(hide)
        return {'FINISHED'}
