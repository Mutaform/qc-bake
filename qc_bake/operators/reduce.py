# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - reduce bake groups operator

import math

import bpy
from mathutils import Vector
from bpy.types import Operator

from .. import core


def _classify(obj, low_suf, high_suf, cage_suf):
    name = obj.name
    if cage_suf and (name.endswith(cage_suf) or ("%s_" % cage_suf) in name):
        return 'CAGE'
    if name.endswith(high_suf) or ("%s_" % high_suf) in name:
        return 'HIGH'
    if name.endswith(low_suf) or ("%s_" % low_suf) in name:
        return 'LOW'
    return None


def _base_name(obj, low_suf, high_suf, cage_suf):
    name = obj.name
    for suf in (high_suf, low_suf, cage_suf):
        if not suf:
            continue
        marker = suf + "_"
        if marker in name:
            return name[: name.index(marker)]
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def _asset_bounds(asset, depsgraph):
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    has_bounds = False

    for obj in asset["objects"]:
        eval_obj = obj.evaluated_get(depsgraph)
        if not eval_obj.bound_box:
            continue
        for corner in eval_obj.bound_box:
            world = eval_obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)
            has_bounds = True

    if not has_bounds:
        return None
    return mins, maxs


def _bounds_distance(bounds_a, bounds_b):
    mins_a, maxs_a = bounds_a
    mins_b, maxs_b = bounds_b

    sq_dist = 0.0
    for axis in range(3):
        if maxs_a[axis] < mins_b[axis]:
            gap = mins_b[axis] - maxs_a[axis]
        elif maxs_b[axis] < mins_a[axis]:
            gap = mins_a[axis] - maxs_b[axis]
        else:
            gap = 0.0
        sq_dist += gap * gap
    return math.sqrt(sq_dist)


def _asset_volume(asset):
    mins, maxs = asset["bounds"]
    size = maxs - mins
    return size.x * size.y * size.z


def _clean_prefix(prefix):
    prefix = prefix.strip().replace(" ", "_")
    return prefix or "BakeGroup"


class QCBAKE_OT_reduce_groups(Operator):
    """Merge distant bake namepairs into fewer baking groups"""
    bl_idname = "qcbake.reduce_groups"
    bl_label = "Reduce Bake Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.qc_bake
        low_suf, high_suf, cage_suf = core.get_suffixes(settings)
        depsgraph = context.evaluated_depsgraph_get()

        if not low_suf or not high_suf:
            self.report({'ERROR'}, "Low/high suffixes must not be empty.")
            return {'CANCELLED'}

        assets, skipped = self._collect_assets(low_suf, high_suf, cage_suf, depsgraph)
        if len(assets) < 2:
            self.report({'WARNING'}, "Need at least two complete bake namepairs.")
            return {'CANCELLED'}

        groups = self._build_groups(assets, settings.reduce_min_gap)
        if len(groups) >= len(assets):
            self.report({'INFO'}, "No safe group reduction found.")
            return {'FINISHED'}

        rename_plan = self._make_rename_plan(
            groups,
            _clean_prefix(settings.reduce_group_prefix),
            low_suf,
            high_suf,
            cage_suf,
        )

        participants = {obj for obj, _ in rename_plan}
        if not settings.overwrite_names:
            for _, new_name in rename_plan:
                existing = bpy.data.objects.get(new_name)
                if existing is not None and existing not in participants:
                    self.report(
                        {'ERROR'},
                        "Name '%s' already taken. Enable 'Allow Name Collisions'."
                        % new_name,
                    )
                    return {'CANCELLED'}

        self._apply_rename_plan(rename_plan, settings.also_rename_datablock)

        merged_assets = sum(len(group) for group in groups if len(group) > 1)
        self.report(
            {'INFO'},
            "Reduced %d assets into %d bake groups (%d skipped incomplete)."
            % (merged_assets, len(groups), skipped),
        )
        return {'FINISHED'}

    def _collect_assets(self, low_suf, high_suf, cage_suf, depsgraph):
        by_base = {}
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            role = _classify(obj, low_suf, high_suf, cage_suf)
            if role is None:
                continue
            base = _base_name(obj, low_suf, high_suf, cage_suf)
            asset = by_base.setdefault(
                base,
                {"base": base, "LOW": [], "HIGH": [], "CAGE": [], "objects": []},
            )
            asset[role].append(obj)
            asset["objects"].append(obj)

        assets = []
        skipped = 0
        for asset in by_base.values():
            if not asset["LOW"] or not asset["HIGH"]:
                skipped += 1
                continue
            bounds = _asset_bounds(asset, depsgraph)
            if bounds is None:
                skipped += 1
                continue
            asset["bounds"] = bounds
            assets.append(asset)
        return assets, skipped

    def _build_groups(self, assets, min_gap):
        groups = []
        ordered = sorted(assets, key=lambda asset: (-_asset_volume(asset), asset["base"]))

        for asset in ordered:
            placed = False
            for group in groups:
                if all(
                    _bounds_distance(asset["bounds"], other["bounds"]) >= min_gap
                    for other in group
                ):
                    group.append(asset)
                    placed = True
                    break
            if not placed:
                groups.append([asset])

        return groups

    def _make_rename_plan(self, groups, prefix, low_suf, high_suf, cage_suf):
        plan = []

        for group_index, group in enumerate(groups, start=1):
            base = "%s_%02d" % (prefix, group_index)
            lows = []
            highs = []
            cages = []

            for asset in sorted(group, key=lambda item: item["base"]):
                lows.extend(sorted(asset["LOW"], key=lambda obj: obj.name))
                highs.extend(sorted(asset["HIGH"], key=lambda obj: obj.name))
                cages.extend(sorted(asset["CAGE"], key=lambda obj: obj.name))

            self._append_role_names(plan, lows, base, low_suf)
            self._append_role_names(plan, highs, base, high_suf)
            if cage_suf:
                self._append_role_names(plan, cages, base, cage_suf)

        return plan

    def _append_role_names(self, plan, objects, base, suffix):
        if not objects:
            return
        if len(objects) == 1:
            plan.append((objects[0], base + suffix))
            return
        for index, obj in enumerate(objects, start=1):
            plan.append((obj, "%s%s_%02d" % (base, suffix, index)))

    def _apply_rename_plan(self, rename_plan, rename_data):
        # Snapshot the current (pre-reduce) name of every participant before
        # touching anything, so a later "Restore Bake Groups" can put it back
        # even after a save/reload. Overwrites any backup left by an earlier,
        # un-restored Reduce pass - Restore always undoes the most recent one.
        for obj, _ in rename_plan:
            obj[core.REDUCE_PREV_NAME_KEY] = obj.name
            if rename_data and obj.data is not None:
                obj[core.REDUCE_PREV_DATA_NAME_KEY] = obj.data.name
            elif core.REDUCE_PREV_DATA_NAME_KEY in obj:
                del obj[core.REDUCE_PREV_DATA_NAME_KEY]

        temp_names = []
        for obj, _ in rename_plan:
            temp_name = "__qcbake_reduce_tmp__" + core.id_generator()
            obj.name = temp_name
            temp_names.append((obj, temp_name))

        for obj, new_name in rename_plan:
            obj.name = new_name
            if rename_data and obj.data is not None:
                obj.data.name = obj.name


class QCBAKE_OT_restore_reduce_groups(Operator):
    """Undo the most recent Reduce Bake Groups pass, restoring prior names"""
    bl_idname = "qcbake.restore_reduce_groups"
    bl_label = "Restore Bake Groups"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(core.REDUCE_PREV_NAME_KEY in obj.keys() for obj in bpy.data.objects)

    def execute(self, context):
        settings = context.scene.qc_bake
        candidates = [obj for obj in bpy.data.objects
                      if core.REDUCE_PREV_NAME_KEY in obj.keys()]
        if not candidates:
            self.report({'WARNING'}, "No reduce backup found to restore.")
            return {'CANCELLED'}

        participants = set(candidates)
        if not settings.overwrite_names:
            for obj in candidates:
                prev_name = obj.get(core.REDUCE_PREV_NAME_KEY)
                existing = bpy.data.objects.get(prev_name)
                if existing is not None and existing not in participants:
                    self.report(
                        {'ERROR'},
                        "Name '%s' already taken by another object. Enable "
                        "'Allow Name Collisions' or rename it first."
                        % prev_name,
                    )
                    return {'CANCELLED'}

        # Two-phase rename through temp names, same trick Reduce uses, so
        # restored names can never collide with each other mid-pass.
        temp_names = []
        for obj in candidates:
            temp_name = "__qcbake_restore_tmp__" + core.id_generator()
            obj.name = temp_name
            temp_names.append(obj)

        restored = 0
        for obj in temp_names:
            prev_name = obj.get(core.REDUCE_PREV_NAME_KEY)
            prev_data_name = obj.get(core.REDUCE_PREV_DATA_NAME_KEY)
            if prev_name:
                obj.name = prev_name
            if prev_data_name and obj.data is not None:
                obj.data.name = prev_data_name
            if core.REDUCE_PREV_NAME_KEY in obj:
                del obj[core.REDUCE_PREV_NAME_KEY]
            if core.REDUCE_PREV_DATA_NAME_KEY in obj:
                del obj[core.REDUCE_PREV_DATA_NAME_KEY]
            restored += 1

        self.report(
            {'INFO'},
            "Restored %d objects to their pre-reduce names. Re-run "
            "'Collection Layout' if you rely on the Bake_<name> collections."
            % restored,
        )
        return {'FINISHED'}
