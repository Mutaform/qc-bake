# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - core
# --------------
# Pure helpers with no operator or UI dependencies. Everything here is about
# naming conventions and mesh geometry, so it can be reasoned about (and unit
# tested) independently of Blender's operator machinery.

import random
import string

import bmesh

# -----------------------------------------------------------------------------
# Naming convention presets
# -----------------------------------------------------------------------------
# Each preset maps to (low_suffix, high_suffix, cage_suffix).
NAMING_PRESETS = {
    'SUBSTANCE': ("_low", "_high", "_cage"),
    'MARMOSET': ("_low", "_high", "_cage"),
    'XNORMAL': ("_lo", "_hi", "_cage"),
    'CUSTOM': (None, None, None),  # resolved from user-provided strings
}

PRESET_ITEMS = [
    ('SUBSTANCE', "Substance ( _low / _high )",
     "Suffixes used by Substance Painter / Designer"),
    ('MARMOSET', "Marmoset ( _low / _high )",
     "Suffixes used by Marmoset Toolbag"),
    ('XNORMAL', "xNormal ( _lo / _hi )",
     "Short suffixes used by xNormal"),
    ('CUSTOM', "Custom",
     "Define your own suffixes below"),
]

HILO_CRITERION_ITEMS = [
    ('TRIS', "Triangles", "Compare triangle counts (most reliable)"),
    ('FACES', "Faces", "Compare face (polygon) counts"),
    ('VERTS', "Vertices", "Compare vertex counts"),
]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """Return a random uppercase/digit identifier of the given length."""
    return ''.join(random.choice(chars) for _ in range(size))


def get_suffixes(settings):
    """Return (low_suffix, high_suffix, cage_suffix) for the given settings."""
    if settings.naming_preset == 'CUSTOM':
        return (
            settings.custom_low_suffix,
            settings.custom_high_suffix,
            settings.custom_cage_suffix,
        )
    return NAMING_PRESETS[settings.naming_preset]


def mesh_metrics(obj, depsgraph):
    """Return (verts, faces, tris) for the evaluated mesh of obj.

    Builds a bmesh from the evaluated object so modifiers are taken into
    account, and frees it deterministically. Non-mesh geometry returns zeros.
    """
    bm = bmesh.new()
    try:
        bm.from_object(obj, depsgraph)
        verts = len(bm.verts)
        faces = len(bm.faces)
        tris = sum(len(f.verts) - 2 for f in bm.faces)  # fan triangulation count
    except (RuntimeError, ValueError):
        verts = faces = tris = 0
    finally:
        bm.free()
    return verts, faces, tris


def metric_for(criterion, metrics):
    """Pick the requested metric out of a (verts, faces, tris) tuple."""
    verts, faces, tris = metrics
    if criterion == 'VERTS':
        return verts
    if criterion == 'FACES':
        return faces
    return tris


def strip_known_suffixes(name, suffixes):
    """Remove any one trailing suffix from the list, if present."""
    for suf in suffixes:
        if suf and name.endswith(suf):
            return name[: -len(suf)]
    return name


# -----------------------------------------------------------------------------
# Bake-group quality tags (Outliner collection colors)
# -----------------------------------------------------------------------------
# A per-asset "Bake_<name>" collection is only bakeable when it contains both a
# low and a high member. We surface that health check as a collection color_tag
# so problems are visible at a glance in the Outliner.
#
#   GREEN  (COLOR_04) - both _low and _high present: ready to bake.
#   RED    (COLOR_01) - only _low OR only _high: something is missing, look here.
BAKEGROUP_TAG_OK = 'COLOR_04'    # green
BAKEGROUP_TAG_WARN = 'COLOR_01'  # red


def classify_role(name, low_suf, high_suf, cage_suf):
    """Return 'LOW', 'HIGH', 'CAGE' or None for a name, by suffix.

    Mirrors the participation rule used when organizing: a suffix matches
    either at the end of the name or as an embedded "<suffix>_" marker, which
    covers indexed members like ``asset_high_01``.
    """
    if cage_suf and (name.endswith(cage_suf) or ("%s_" % cage_suf) in name):
        return 'CAGE'
    if high_suf and (name.endswith(high_suf) or ("%s_" % high_suf) in name):
        return 'HIGH'
    if low_suf and (name.endswith(low_suf) or ("%s_" % low_suf) in name):
        return 'LOW'
    return None


def bakegroup_color_tag(object_names, low_suf, high_suf, cage_suf):
    """Return the color_tag a per-asset bake collection should carry.

    Green when both a low and a high member are present (a complete namepair,
    ready to bake); red otherwise (only lows or only highs - a member is
    missing and the group needs attention). Cage-only members do not by
    themselves make a group complete.
    """
    has_low = has_high = False
    for name in object_names:
        role = classify_role(name, low_suf, high_suf, cage_suf)
        if role == 'LOW':
            has_low = True
        elif role == 'HIGH':
            has_high = True
    return BAKEGROUP_TAG_OK if (has_low and has_high) else BAKEGROUP_TAG_WARN


# -----------------------------------------------------------------------------
# Reduce Bake Groups - reversible rename backup
# -----------------------------------------------------------------------------
# "Reduce Bake Groups" merges small namepairs into fewer groups by renaming
# objects (and optionally their mesh data). That's destructive unless the
# pre-rename names are kept somewhere. We stash them as custom properties on
# the objects themselves rather than in a separate list, because:
#   - it survives file save/reload and outlasts Blender's native undo stack;
#   - it needs no id-by-name bookkeeping that renaming would immediately break;
#   - it is automatically consistent even if objects are later deleted.
# A "Restore Bake Groups" operator reads these back and clears them.
REDUCE_PREV_NAME_KEY = "qcbake_reduce_prev_name"
REDUCE_PREV_DATA_NAME_KEY = "qcbake_reduce_prev_data_name"


# -----------------------------------------------------------------------------
# Add-on version (read from blender_manifest.toml at runtime)
# -----------------------------------------------------------------------------
def addon_version():
    """Return the running add-on's (major, minor, patch) version tuple.

    Reads it from the installed extension's manifest via addon_utils, so the
    UI never drifts out of sync with blender_manifest.toml - there is only
    ever one place the version number is written down.
    """
    import sys
    import addon_utils

    # This module's __name__ is "<addon_root_package>.core"; the add-on's own
    # package is one level up regardless of which repository it's installed
    # under (bl_ext.user_default.qc_bake, bl_ext.some_repo.qc_bake, ...).
    root_pkg = __name__.rsplit(".", 1)[0]
    mod = sys.modules.get(root_pkg)
    info = addon_utils.module_bl_info(mod) if mod else None
    if not info:
        return (0, 0, 0)
    return tuple(info.get("version", (0, 0, 0)))


def addon_version_string():
    """Return the running add-on's version as 'X.Y.Z'."""
    return ".".join(str(part) for part in addon_version())
