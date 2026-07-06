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
        low_suf, high_suf, _ = core.get_suffixes(settings)

        objs = context.selected_objects
        lows = [o for o in objs if o.name.endswith(low_suf)]
        highs = [o for o in objs if o.name.endswith(high_suf)]

        if len(lows) != 1 or len(highs) != 1:
            self.report(
                {'ERROR'},
                "Select exactly one '%s' and one '%s' object." % (low_suf, high_suf),
            )
            return {'CANCELLED'}

        low, high = lows[0], highs[0]
        low_base = low.name[: -len(low_suf)]
        high_base = high.name[: -len(high_suf)]

        # Swap the ROLES of the two objects: the object currently named
        # <base>_low becomes <base>_high and vice versa. Both are parked on
        # temporary names first so neither target name is momentarily occupied
        # (important because a namepair usually shares the same base name).
        tmp_low = "__qcbake_tmp_low__" + core.id_generator()
        tmp_high = "__qcbake_tmp_high__" + core.id_generator()
        low.name = tmp_low
        high.name = tmp_high

        low.name = low_base + high_suf   # old low object -> now high
        high.name = high_base + low_suf  # old high object -> now low

        if settings.also_rename_datablock:
            if low.data:
                low.data.name = low.name
            if high.data:
                high.data.name = high.name

        self.report({'INFO'}, "Swapped high/low roles.")
        return {'FINISHED'}
