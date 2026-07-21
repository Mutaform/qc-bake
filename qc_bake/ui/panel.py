# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - UI panel
# ------------------
# The N-panel lives under the "QC Bake" tab. The layout is split into a main
# panel with the primary actions and three collapsible sub-panels (Naming,
# Options, Visibility) so the interface stays compact by default. All icons
# come from the central icons module.

import bpy
from bpy.types import Panel

from .. import core, icons

TAB_CATEGORY = "QC Bake"
PANEL_TITLE = "QC Bake by Mutaform Studio"


class QCBAKE_PT_main(Panel):
    bl_idname = "QCBAKE_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_CATEGORY
    bl_label = PANEL_TITLE

    def draw_header_preset(self, context):
        # Right-aligned "ver X.Y.Z" tag on the panel's title row. Sourced live
        # from blender_manifest.toml via core.addon_version_string(), so it
        # can never fall out of sync with the actual installed version.
        self.layout.label(text="ver %s" % core.addon_version_string())

    def draw(self, context):
        layout = self.layout

        # Primary actions, given visual weight.
        col = layout.column(align=True)
        col.scale_y = 1.4
        col.operator("qcbake.create_namepair",
                     text="Create Namepair", icon=icons.ICON_CREATE)

        row = layout.row(align=True)
        row.scale_y = 1.1
        row.operator("qcbake.swap", text="Swap High / Low", icon=icons.ICON_SWAP)


class QCBAKE_PT_naming(Panel):
    bl_idname = "QCBAKE_PT_naming"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_CATEGORY
    bl_parent_id = "QCBAKE_PT_main"
    bl_label = "Naming"
    bl_order = 3  # Visibility, Utilities, then Naming

    def draw_header(self, context):
        self.layout.label(text="", icon=icons.ICON_NAMING)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        settings = context.scene.qc_bake

        layout.prop(settings, "naming_preset", text="Convention")
        if settings.naming_preset == 'CUSTOM':
            sub = layout.column(align=True)
            sub.prop(settings, "custom_low_suffix", text="Low")
            sub.prop(settings, "custom_high_suffix", text="High")
            sub.prop(settings, "custom_cage_suffix", text="Cage")

        layout.separator()
        layout.prop(settings, "hilo_criterion", text="Detect By",
                    icon=icons.ICON_DETECT)


class QCBAKE_PT_options(Panel):
    bl_idname = "QCBAKE_PT_options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_CATEGORY
    bl_parent_id = "QCBAKE_PT_main"
    bl_label = "Options"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4  # Options last

    def draw_header(self, context):
        self.layout.label(text="", icon=icons.ICON_OPTIONS)

    def draw(self, context):
        layout = self.layout
        settings = context.scene.qc_bake

        # Draw each toggle as a checkbox + left-aligned icon/label on its own
        # row, so labels start at a fixed left margin instead of being centred
        # by the per-row icon.
        col = layout.column(align=True)
        self._toggle(col, settings, "generate_random_name",
                     "Generate Random Name", icons.ICON_RANDOM)
        self._toggle(col, settings, "also_rename_datablock",
                     "Also Rename Mesh Data", icons.ICON_DATABLOCK)
        self._toggle(col, settings, "detect_cage",
                     "Detect Cage", icons.ICON_DETECT_CAGE)
        self._toggle(col, settings, "move_to_collection",
                     "Move to Collection", icons.ICON_COLLECTION)
        self._toggle(col, settings, "hide_after_renaming",
                     "Hide After Renaming", icons.ICON_HIDE_AFTER)

        col.separator()
        self._toggle(col, settings, "overwrite_names",
                     "Allow Name Collisions", icons.ICON_OVERWRITE)

    def _toggle(self, layout, settings, prop, label, icon):
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        row.prop(settings, prop, text="")
        row.label(text=label, icon=icon)


class QCBAKE_PT_visibility(Panel):
    bl_idname = "QCBAKE_PT_visibility"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_CATEGORY
    bl_parent_id = "QCBAKE_PT_main"
    bl_label = "Visibility"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1  # Visibility first

    def draw_header(self, context):
        self.layout.label(text="", icon=icons.ICON_VISIBILITY)

    def draw(self, context):
        layout = self.layout
        settings = context.scene.qc_bake
        col = layout.column(align=True)
        self._toggle_row(col, context, settings, 'HIGH', "High", icons.ICON_HIGH)
        self._toggle_row(col, context, settings, 'LOW', "Low", icons.ICON_LOW)
        self._toggle_row(col, context, settings, 'CAGE', "Cage", icons.ICON_CAGE)
        col.separator()
        self._toggle_row(col, context, settings, 'ALL', "All", icons.ICON_ALL)

    def _group_suffixes(self, settings, group):
        low_suf, high_suf, cage_suf = core.get_suffixes(settings)
        if group == 'HIGH':
            return (high_suf,)
        if group == 'LOW':
            return (low_suf,)
        if group == 'CAGE':
            return (cage_suf,) if cage_suf else ()
        return tuple(s for s in (low_suf, high_suf, cage_suf) if s)

    def _group_state(self, settings, group):
        """Return 'SHOWN', 'HIDDEN', 'MIXED' or None (no matching objects)."""
        suffixes = self._group_suffixes(settings, group)
        if not suffixes:
            return None
        objs = [o for o in bpy.data.objects
                if any(o.name.endswith(s) or ("%s_" % s) in o.name
                       for s in suffixes)]
        if not objs:
            return None
        hidden = sum(1 for o in objs if o.hide_get())
        if hidden == 0:
            return 'SHOWN'
        if hidden == len(objs):
            return 'HIDDEN'
        return 'MIXED'

    def _toggle_row(self, layout, context, settings, group, label, icon):
        state = self._group_state(settings, group)
        row = layout.row(align=True)
        row.label(text=label, icon=icon)

        # The eye icon rides the button that reflects the current state:
        # when the group is fully shown, "Show" is depressed and wears the
        # open-eye icon; when fully hidden, "Hide" is depressed with the
        # closed-eye icon. A mixed/empty group shows neither depressed.
        show_active = state == 'SHOWN'
        hide_active = state == 'HIDDEN'

        sub = row.row(align=True)
        sub.enabled = state is not None

        op = sub.operator(
            "qcbake.toggle_visibility", text="Show",
            icon=icons.ICON_SHOW if show_active else 'BLANK1',
            depress=show_active,
        )
        op.group = group
        op.action = 'SHOW'

        op = sub.operator(
            "qcbake.toggle_visibility", text="Hide",
            icon=icons.ICON_HIDE if hide_active else 'BLANK1',
            depress=hide_active,
        )
        op.group = group
        op.action = 'HIDE'


classes = (
    QCBAKE_PT_main,
    QCBAKE_PT_naming,
    QCBAKE_PT_options,
    QCBAKE_PT_visibility,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
