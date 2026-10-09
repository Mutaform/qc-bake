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
        if self.group == 'CAGE' and not any(core.role_tokens(settings)['CAGE']):
            self.report({'WARNING'}, "No cage suffix defined.")
            return {'CANCELLED'}

        # Role detection is shared with the rest of the add-on (core.detect_role):
        # any case, suffix / prefix / CamelCase, indexed multi-high members.
        hide = self.action == 'HIDE'
        for obj in bpy.data.objects:
            if core.has_role(obj.name, settings, self.group):
                obj.hide_set(hide)
        return {'FINISHED'}
