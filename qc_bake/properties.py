# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - properties

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import PropertyGroup

from . import core


class QCBakeSettings(PropertyGroup):
    naming_preset: EnumProperty(
        name="Naming Convention",
        items=core.PRESET_ITEMS,
        default='SUBSTANCE',
    )
    custom_low_suffix: StringProperty(name="Low Suffix", default="_low")
    custom_high_suffix: StringProperty(name="High Suffix", default="_high")
    custom_cage_suffix: StringProperty(name="Cage Suffix", default="_cage")

    hilo_criterion: EnumProperty(
        name="Detect By",
        items=core.HILO_CRITERION_ITEMS,
        default='TRIS',
    )

    generate_random_name: BoolProperty(
        name="Generate Random Name", default=False,
        description="Use a random base name instead of the low poly's name",
    )
    hide_after_renaming: BoolProperty(
        name="Hide After Renaming", default=False,
        description="Hide the objects once they have been renamed",
    )
    also_rename_datablock: BoolProperty(
        name="Also Rename Mesh Data", default=True,
        description="Rename the object's mesh datablock to match",
    )
    detect_cage: BoolProperty(
        name="Detect Cage", default=True,
        description="Treat a selected object ending in the cage suffix as the cage",
    )
    move_to_collection: BoolProperty(
        name="Move to Collection", default=False,
        description="Move the namepair into a 'Bake_<name>' collection",
    )
    overwrite_names: BoolProperty(
        name="Allow Name Collisions", default=False,
        description="Let Blender auto-suffix (.001) instead of aborting on clashes",
    )
    reduce_group_prefix: StringProperty(
        name="Group Prefix",
        default="BakeGroup",
        description="Base name used when reducing existing bake pairs into fewer groups",
    )
    reduce_min_gap: FloatProperty(
        name="Minimum Gap",
        default=0.05,
        min=0.0,
        soft_max=10.0,
        unit='LENGTH',
        description=(
            "Minimum world-space distance required between asset bounds before "
            "they can share one bake group"
        ),
    )


classes = (QCBakeSettings,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.qc_bake = bpy.props.PointerProperty(type=QCBakeSettings)


def unregister():
    del bpy.types.Scene.qc_bake
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
