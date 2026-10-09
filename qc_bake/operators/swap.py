# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - swap operator

from bpy.types import Operator

from .. import core


class QCBAKE_OT_swap(Operator):
    """Swap the low and high roles of two selected objects"""
    bl_idname = "qcbake.swap"
    bl_label = "Swap High / Low"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 2

    def execute(self, context):
        settings = context.scene.qc_bake
        objs = context.selected_objects
        roles = {o.name: core.classify_role(o.name, settings) for o in objs}
        lows = [o for o in objs if roles[o.name] == 'LOW']
        highs = [o for o in objs if roles[o.name] == 'HIGH']

        if len(lows) != 1 or len(highs) != 1:
            self.report(
                {'ERROR'},
                "Select exactly one low and one high object (by name marker).",
            )
            return {'CANCELLED'}

        low, high = lows[0], highs[0]

        # Swap the ROLES of the two objects by exchanging their names outright,
        # so whatever naming style the pair uses (_low/_high, _LP/_HP,
        # high_<name>, <name>High ...) is preserved exactly. Both are parked on
        # temporary names first so neither target name is momentarily occupied.
        low_name, high_name = low.name, high.name
        low.name = "__qcbake_tmp_low__" + core.id_generator()
        high.name = "__qcbake_tmp_high__" + core.id_generator()

        low.name = high_name   # old low object -> now high
        high.name = low_name   # old high object -> now low

        if settings.also_rename_datablock:
            if low.data:
                low.data.name = low.name
            if high.data:
                high.data.name = high.name

        self.report({'INFO'}, "Swapped high/low roles.")
        return {'FINISHED'}
