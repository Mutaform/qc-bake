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
