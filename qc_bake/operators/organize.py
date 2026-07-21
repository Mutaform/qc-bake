# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - organize operators
# ----------------------------
# Reorganise an already-named scene into one of two collection layouts, both
# nested under a single "Bake Group" head collection:
#
#   FLAT       Bake Group -> High / Low / Cage        (grouped by role)
#   PER_ASSET  Bake Group -> Bake_<base> / ...        (grouped by namepair)
#
# Participation is decided purely by name suffixes, so props and helper meshes
# are never touched. Each operator can rebuild from any prior state.

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from .. import core

HEAD_NAME = "Bake Group"
FLAT_SUBS = ("High", "Low", "Cage")


def _classify(obj, low_suf, high_suf, cage_suf):
    """Return 'LOW', 'HIGH', 'CAGE' or None for an object, by name suffix."""
    return core.classify_role(obj.name, low_suf, high_suf, cage_suf)


def _base_name(obj, low_suf, high_suf, cage_suf):
    """Recover the shared base name of a namepair member."""
    name = obj.name
    # Strip a trailing "_NN" index on multi-high objects first.
    for suf in (high_suf, low_suf, cage_suf):
        if not suf:
            continue
        # e.g. FMN204_high_01 -> cut at the suffix
        marker = suf + "_"
        if marker in name:
            return name[: name.index(marker)]
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def _collect_participants(low_suf, high_suf, cage_suf):
    """Return dict role -> [objects] for everything that looks like bake geo."""
    buckets = {'LOW': [], 'HIGH': [], 'CAGE': []}
    for obj in bpy.data.objects:
        role = _classify(obj, low_suf, high_suf, cage_suf)
        if role:
            buckets[role].append(obj)
    return buckets


def _unlink_everywhere(obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)


def _cleanup_bake_collections(keep):
    """Remove empty Bake_/Bake Group/High/Low/Cage collections we no longer use."""
    managed_prefixes = ("Bake_",)
    managed_exact = {HEAD_NAME, "High", "Low", "Cage"}
    for coll in list(bpy.data.collections):
        if coll in keep:
            continue
        is_managed = coll.name.startswith(managed_prefixes) or coll.name in managed_exact
        if is_managed and len(coll.objects) == 0 and len(coll.children) == 0:
            bpy.data.collections.remove(coll)


def _collapse_outliner():
    """Fold every Outliner tree back closed after (re)building the hierarchy.

    Blender doesn't expose a per-collection "expanded" property through bpy,
    so this leans on the same trick the Outliner's own collapse-all keymap
    uses: bpy.ops.outliner.show_one_level(open=False), run against a real
    Outliner area/region via a context override. Every newly created or
    relinked collection starts out expanded, which turns into a wall of
    nested rows to fold by hand after each run - this does it once,
    automatically. Silently does nothing if no Outliner is visible (e.g. a
    background/headless context), since that's a convenience, not something
    the operator should ever fail over.
    """
    try:
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                if area.type != 'OUTLINER':
                    continue
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region is None:
                    continue
                with bpy.context.temp_override(window=win, area=area, region=region):
                    # A couple of passes is enough to fully close both levels
                    # of nesting our layouts ever produce (head -> role/asset
                    # sub-collections), with headroom to spare.
                    for _ in range(3):
                        bpy.ops.outliner.show_one_level(open=False)
                area.tag_redraw()
    except RuntimeError:
        # No Outliner area/region available to override onto - nothing to do.
        pass


class QCBAKE_OT_organize(Operator):
    """Reorganise named bake objects into a collection layout"""
    bl_idname = "qcbake.organize"
    bl_label = "Organize Bake Collections"
    bl_options = {'REGISTER', 'UNDO'}

    layout_mode: EnumProperty(
        items=[
            ('FLAT', "Flat (High / Low)",
             "Bake Group with High, Low and Cage sub-collections"),
            ('PER_ASSET', "Per Asset",
             "Bake Group with one Bake_<name> collection per namepair"),
        ],
        default='FLAT',
    )

    def execute(self, context):
        settings = context.scene.qc_bake
        low_suf, high_suf, cage_suf = core.get_suffixes(settings)

        buckets = _collect_participants(low_suf, high_suf, cage_suf)
        total = sum(len(v) for v in buckets.values())
        if total == 0:
            self.report({'WARNING'},
                        "No named bake objects found (nothing with %s / %s)."
                        % (low_suf, high_suf))
            return {'CANCELLED'}

        scene_coll = context.scene.collection

        # Fresh head collection.
        head = bpy.data.collections.get(HEAD_NAME)
        if head is None:
            head = bpy.data.collections.new(HEAD_NAME)
            scene_coll.children.link(head)

        keep = {head}

        if self.layout_mode == 'FLAT':
            self._build_flat(head, buckets, keep)
        else:
            self._build_per_asset(head, buckets, low_suf, high_suf, cage_suf, keep)

        _cleanup_bake_collections(keep)
        _collapse_outliner()

        self.report({'INFO'}, "Organized %d objects into '%s' (%s)."
                    % (total, HEAD_NAME, self.layout_mode.replace('_', ' ').title()))
        return {'FINISHED'}

    # --- layouts ------------------------------------------------------------
    def _build_flat(self, head, buckets, keep):
        role_to_name = {'HIGH': "High", 'LOW': "Low", 'CAGE': "Cage"}
        for role, sub_name in role_to_name.items():
            objs = buckets[role]
            if not objs:
                continue
            sub = bpy.data.collections.get(sub_name)
            if sub is None:
                sub = bpy.data.collections.new(sub_name)
            if sub.name not in [c.name for c in head.children]:
                # detach from any previous parent first
                for p in bpy.data.collections:
                    if sub.name in [c.name for c in p.children]:
                        p.children.unlink(sub)
                if sub.name in [c.name for c in bpy.context.scene.collection.children]:
                    bpy.context.scene.collection.children.unlink(sub)
                head.children.link(sub)
            keep.add(sub)
            # Flat role collections carry no per-asset health meaning; make
            # sure a stale tag from a previous Per-Asset run doesn't linger.
            sub.color_tag = 'NONE'
            for obj in objs:
                _unlink_everywhere(obj)
                sub.objects.link(obj)

    def _build_per_asset(self, head, buckets, low_suf, high_suf, cage_suf, keep):
        # Group every participant by its recovered base name.
        by_base = {}
        for role, objs in buckets.items():
            for obj in objs:
                base = _base_name(obj, low_suf, high_suf, cage_suf)
                by_base.setdefault(base, []).append(obj)

        for base, objs in by_base.items():
            cname = "Bake_" + base
            sub = bpy.data.collections.get(cname)
            if sub is None:
                sub = bpy.data.collections.new(cname)
            if sub.name not in [c.name for c in head.children]:
                for p in bpy.data.collections:
                    if sub.name in [c.name for c in p.children]:
                        p.children.unlink(sub)
                if sub.name in [c.name for c in bpy.context.scene.collection.children]:
                    bpy.context.scene.collection.children.unlink(sub)
                head.children.link(sub)
            keep.add(sub)
            for obj in objs:
                _unlink_everywhere(obj)
                sub.objects.link(obj)

            # Health check: green when the group holds a complete low/high
            # namepair, red when a member is missing (only lows or only highs).
            sub.color_tag = core.bakegroup_color_tag(
                [o.name for o in objs], low_suf, high_suf, cage_suf)
