# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - create namepair operator

import bpy
from bpy.types import Operator

from .. import core


class QCBAKE_OT_create_namepair(Operator):
    """Rename selected objects into a high/low baking namepair"""
    bl_idname = "qcbake.create_namepair"
    bl_label = "Create Namepair"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    def execute(self, context):
        settings = context.scene.qc_bake
        depsgraph = context.evaluated_depsgraph_get()

        selected = [o for o in context.selected_objects if o.type == 'MESH']
        if len(selected) < 2:
            self.report({'ERROR'}, "Select at least two mesh objects.")
            return {'CANCELLED'}

        low_suf, high_suf, cage_suf = core.get_suffixes(settings)
        if not low_suf or not high_suf:
            self.report({'ERROR'}, "Low/high suffixes must not be empty.")
            return {'CANCELLED'}
        if low_suf == high_suf:
            self.report({'ERROR'}, "Low and high suffixes must differ.")
            return {'CANCELLED'}

        crit = settings.hilo_criterion
        all_suffixes = [low_suf, high_suf]
        if cage_suf:
            all_suffixes.append(cage_suf)

        # Identify the cage object (if any) before we sort hi/lo.
        cage_obj = None
        candidates = list(selected)
        if settings.detect_cage and cage_suf:
            for o in list(candidates):
                if o.name.endswith(cage_suf):
                    cage_obj = o
                    candidates.remove(o)
                    break

        if len(candidates) < 2:
            self.report({'ERROR'}, "Need at least two non-cage meshes.")
            return {'CANCELLED'}

        # Two-object mode vs. group mode.
        if len(candidates) == 2:
            pairs = self._resolve_single_pair(candidates, depsgraph, crit)
            if pairs is None:
                self.report({'ERROR'},
                            "Both meshes have the same %s count." % crit.lower())
                return {'CANCELLED'}
            high_polys, low_polys = pairs
        else:
            # Group mode: the low poly is the base, the rest are high polys.
            # Prefer the active object if it's part of the selection; otherwise
            # fall back to the mesh with the smallest geometry count so the
            # operator never dead-ends on a stray active object.
            active = context.active_object
            if active is not None and active in candidates:
                low_ref_obj = active
            else:
                low_ref_obj = min(
                    candidates,
                    key=lambda o: core.metric_for(crit, core.mesh_metrics(o, depsgraph)),
                )
            low_polys = [low_ref_obj]
            high_polys = [o for o in candidates if o is not low_ref_obj]

        # Determine the base name.
        low_ref = low_polys[0]
        if settings.generate_random_name:
            base = core.id_generator()
        else:
            base = core.strip_known_suffixes(low_ref.name, all_suffixes)

        # Collision check.
        wanted = [base + low_suf]
        if len(high_polys) == 1:
            wanted += [base + high_suf]
        else:
            wanted += ["%s%s_%02d" % (base, high_suf, i + 1)
                       for i in range(len(high_polys))]
        if cage_obj:
            wanted.append(base + cage_suf)

        renaming = set(low_polys + high_polys + ([cage_obj] if cage_obj else []))
        for wname in wanted:
            existing = bpy.data.objects.get(wname)
            if existing is not None and existing not in renaming:
                if not settings.overwrite_names:
                    self.report(
                        {'ERROR'},
                        "Name '%s' already taken. Enable 'Allow Name Collisions' "
                        "or rename the base object." % wname,
                    )
                    return {'CANCELLED'}

        # Apply names.
        rename_data = settings.also_rename_datablock

        def apply(obj, new_name):
            obj.name = new_name
            if rename_data and obj.data is not None:
                obj.data.name = obj.name

        apply(low_ref, base + low_suf)  # low first so the base is claimed
        if len(high_polys) == 1:
            apply(high_polys[0], base + high_suf)
        else:
            for i, hp in enumerate(high_polys):
                apply(hp, "%s%s_%02d" % (base, high_suf, i + 1))
        if cage_obj:
            apply(cage_obj, base + cage_suf)

        renamed = [low_ref] + high_polys + ([cage_obj] if cage_obj else [])

        # Move to a collection, if requested (with cleanup of empties).
        if settings.move_to_collection:
            self._organize_collection(context, base, renamed)
            self._cleanup_empty_bake_collections()

        # Hide, if requested.
        if settings.hide_after_renaming:
            for obj in renamed:
                obj.hide_set(True)

        self.report(
            {'INFO'},
            "Namepair created: base '%s' (%d high, 1 low%s)."
            % (base, len(high_polys), ", 1 cage" if cage_obj else ""),
        )
        return {'FINISHED'}

    # --- internal helpers ---------------------------------------------------
    def _resolve_single_pair(self, two_objs, depsgraph, crit):
        a, b = two_objs
        ma = core.metric_for(crit, core.mesh_metrics(a, depsgraph))
        mb = core.metric_for(crit, core.mesh_metrics(b, depsgraph))
        if ma == mb:
            return None
        if ma > mb:
            return [a], [b]  # high, low
        return [b], [a]

    def _organize_collection(self, context, base, objects):
        coll_name = "Bake_" + base
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            coll = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(coll)
        for obj in objects:
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            coll.objects.link(obj)

    def _cleanup_empty_bake_collections(self):
        """Remove leftover empty 'Bake_' collections from earlier runs."""
        for coll in list(bpy.data.collections):
            if coll.name.startswith("Bake_") and len(coll.objects) == 0 \
                    and len(coll.children) == 0:
                bpy.data.collections.remove(coll)
