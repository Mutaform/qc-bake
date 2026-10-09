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
    'HPLP': ("_lp", "_hp", "_cage"),
    'CUSTOM': (None, None, None),  # resolved from user-provided strings
}

PRESET_ITEMS = [
    ('SUBSTANCE', "Substance ( _low / _high )",
     "Suffixes used by Substance Painter / Designer"),
    ('MARMOSET', "Marmoset ( _low / _high )",
     "Suffixes used by Marmoset Toolbag"),
    ('XNORMAL', "xNormal ( _lo / _hi )",
     "Short suffixes used by xNormal"),
    ('HPLP', "HP / LP ( _lp / _hp )",
     "Short high-poly / low-poly suffixes (_LP / _HP also match)"),
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


def match_suffix(name, suf):
    """Return the base part of ``name`` if it carries ``suf``, else None.

    Matching is case-insensitive, so a preset of ``_high`` also picks up
    objects named ``Asset_High`` or ``Asset_HIGH`` - production scenes come
    from several tools and artists, and the capitalisation of the role suffix
    is the one thing nobody keeps consistent. Two placements are accepted:

      * trailing:  ``Asset_high``            -> ``Asset``
      * indexed:   ``Asset_high_01``         -> ``Asset`` (multi-high members)

    The indexed form requires the suffix to be followed by ``_`` and digits
    only, so an unrelated substring like ``Plywood`` can never be mistaken
    for a ``_low`` marker.
    """
    if not suf:
        return None
    lname, lsuf = name.lower(), suf.lower()
    if lname.endswith(lsuf):
        return name[: len(name) - len(suf)]
    marker = lsuf + "_"
    idx = lname.rfind(marker)
    while idx != -1:
        if name[idx + len(marker):].isdigit():
            return name[:idx]
        idx = lname.rfind(marker, 0, idx)
    return None


def has_suffix(name, suf):
    """True when ``name`` carries ``suf`` (see match_suffix)."""
    return match_suffix(name, suf) is not None


def strip_known_suffixes(name, suffixes):
    """Remove any one suffix from the list, if present (case-insensitive)."""
    for suf in suffixes:
        base = match_suffix(name, suf)
        if base is not None:
            return base
    return name


def base_name(name, low_suf, high_suf, cage_suf):
    """Recover the shared base name of a namepair member.

    Cage is checked first, then high, then low, mirroring classify_role, so
    ``Asset_high_01`` and ``Asset_low`` both resolve to ``Asset``.
    """
    return strip_known_suffixes(name, (cage_suf, high_suf, low_suf))


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

    Case-insensitive; a suffix matches either at the end of the name or as an
    indexed ``<suffix>_NN`` member like ``asset_high_01`` (see match_suffix).
    """
    if has_suffix(name, cage_suf):
        return 'CAGE'
    if has_suffix(name, high_suf):
        return 'HIGH'
    if has_suffix(name, low_suf):
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
