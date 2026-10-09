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
import re
import string

import bmesh

# -----------------------------------------------------------------------------
# Naming conventions
# -----------------------------------------------------------------------------
# Two separate questions, answered by two separate tables:
#
#   1. Which names do we *write* when creating or reducing namepairs?
#      -> NAMING_PRESETS: the concrete (low, high, cage) suffix strings.
#   2. Which names do we *recognise* as bake geometry when organising, hiding,
#      swapping or reducing?  -> ROLE_TOKENS plus the matchers below.
#
# Recognition is deliberately far more permissive than writing. Production
# scenes arrive from several artists and tools, and the role marker is the one
# thing nobody keeps consistent, so a role token is accepted:
#
#   * in any case:            Chair_high    Chair_High    Chair_HIGH
#   * as a suffix:            Chair_high    Chair.high    Chair-high
#   * as an indexed suffix:   Chair_high_01    Chair_high.001  (Blender dupes)
#   * as a prefix:            high_Chair    HP_Chair
#   * glued in CamelCase:     ChairHigh     ChairHP
#     (the token must be capitalised and follow a lowercase letter or digit,
#     so "Pillow" or "Hollow" can never read as a _low marker)
#
# The 'AUTO' preset recognises every token family at once; the other presets
# only their own family. Written names always use the preset's suffixes
# (AUTO writes Substance-style _low / _high).

NAMING_PRESETS = {
    'AUTO': ("_low", "_high", "_cage"),
    'SUBSTANCE': ("_low", "_high", "_cage"),
    'MARMOSET': ("_low", "_high", "_cage"),
    'XNORMAL': ("_lo", "_hi", "_cage"),
    'HPLP': ("_lp", "_hp", "_cage"),
    'CUSTOM': (None, None, None),  # resolved from user-provided strings
}

# Lowercase role tokens recognised by each preset. An underscore inside a
# token stands for "any separator" (low_poly matches low-poly / low.poly).
ROLE_TOKENS = {
    'AUTO': {
        'LOW': ("low", "lo", "lp", "lowpoly", "low_poly", "lowres"),
        'HIGH': ("high", "hi", "hp", "highpoly", "high_poly", "hires"),
        'CAGE': ("cage",),
    },
    'SUBSTANCE': {'LOW': ("low",), 'HIGH': ("high",), 'CAGE': ("cage",)},
    'MARMOSET': {'LOW': ("low",), 'HIGH': ("high",), 'CAGE': ("cage",)},
    'XNORMAL': {'LOW': ("lo",), 'HIGH': ("hi",), 'CAGE': ("cage",)},
    'HPLP': {'LOW': ("lp",), 'HIGH': ("hp",), 'CAGE': ("cage",)},
}

# Explicit numeric values keep files saved with an older version on the same
# preset: enum values are stored by number, so inserting 'AUTO' at the top of
# the list must not shift everything else down by one.
PRESET_ITEMS = [
    ('AUTO', "Auto ( any known )",
     "Recognise _low/_high, _lo/_hi, _lp/_hp and friends in any case, as "
     "suffix, prefix or CamelCase; new names are written as _low / _high",
     'NONE', 5),
    ('SUBSTANCE', "Substance ( _low / _high )",
     "Suffixes used by Substance Painter / Designer", 'NONE', 0),
    ('MARMOSET', "Marmoset ( _low / _high )",
     "Suffixes used by Marmoset Toolbag", 'NONE', 1),
    ('XNORMAL', "xNormal ( _lo / _hi )",
     "Short suffixes used by xNormal", 'NONE', 2),
    ('HPLP', "HP / LP ( _lp / _hp )",
     "Short high-poly / low-poly suffixes (_LP / _HP also match)", 'NONE', 4),
    ('CUSTOM', "Custom",
     "Define your own suffixes below", 'NONE', 3),
]

HILO_CRITERION_ITEMS = [
    ('TRIS', "Triangles", "Compare triangle counts (most reliable)"),
    ('FACES', "Faces", "Compare face (polygon) counts"),
    ('VERTS', "Vertices", "Compare vertex counts"),
]

# Cage is checked first, then high, then low, so a name carrying two markers
# resolves the same way everywhere in the add-on.
ROLE_ORDER = ('CAGE', 'HIGH', 'LOW')

_SEP = r"[ _.\-]"
_IDX = r"(?:%s\d+){0,2}" % _SEP   # _01, .001, or _01.001
_pattern_cache = {}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """Return a random uppercase/digit identifier of the given length."""
    return ''.join(random.choice(chars) for _ in range(size))


def get_suffixes(settings):
    """Return the (low, high, cage) suffixes used when *writing* names."""
    if settings.naming_preset == 'CUSTOM':
        return (
            settings.custom_low_suffix,
            settings.custom_high_suffix,
            settings.custom_cage_suffix,
        )
    return NAMING_PRESETS[settings.naming_preset]


def role_tokens(settings):
    """Return {'LOW': (...), 'HIGH': (...), 'CAGE': (...)} tokens to recognise."""
    preset = settings.naming_preset
    if preset == 'CUSTOM':
        return {
            'LOW': (settings.custom_low_suffix,),
            'HIGH': (settings.custom_high_suffix,),
            'CAGE': (settings.custom_cage_suffix,),
        }
    return ROLE_TOKENS.get(preset, ROLE_TOKENS['AUTO'])


def _token_patterns(token):
    """Compile the matchers for one role token (see the module comment)."""
    token = (token or "").strip(" _.-").lower()
    if not token:
        return []
    body = _SEP.join(re.escape(part) for part in token.split("_") if part)
    patterns = [
        # suffix, optionally indexed:  <base>_token  <base>_token_01  <base>_token.001
        re.compile(r"^(?P<base>.+?)%s%s%s$" % (_SEP, body, _IDX), re.IGNORECASE),
        # prefix:  token_<base>
        re.compile(r"^%s%s(?P<base>.+)$" % (body, _SEP), re.IGNORECASE),
    ]
    if len(token) >= 2 and "_" not in token:
        # CamelCase, case-sensitive on purpose:  <base>Token / <base>TOKEN
        patterns.append(re.compile(
            r"^(?P<base>.*[a-z0-9])(?:%s|%s)%s$"
            % (re.escape(token.capitalize()), re.escape(token.upper()), _IDX)))
    return patterns


def _matchers(settings):
    tokens = role_tokens(settings)
    key = tuple((role, tuple(tokens[role])) for role in ROLE_ORDER)
    matchers = _pattern_cache.get(key)
    if matchers is None:
        matchers = [
            (role, [p for tok in tokens[role] for p in _token_patterns(tok)])
            for role in ROLE_ORDER
        ]
        _pattern_cache[key] = matchers
    return matchers


def detect_role(name, settings):
    """Return (role, base) for an object name, or (None, None).

    role is 'LOW', 'HIGH' or 'CAGE'; base is the shared namepair name with the
    role marker (and any index / Blender duplicate counter) removed.
    """
    for role, patterns in _matchers(settings):
        for pattern in patterns:
            match = pattern.match(name)
            if match:
                return role, match.group("base")
    return None, None


def classify_role(name, settings):
    """Return 'LOW', 'HIGH', 'CAGE' or None for a name."""
    return detect_role(name, settings)[0]


def base_name(name, settings):
    """Recover the shared base name of a namepair member (name if none)."""
    base = detect_role(name, settings)[1]
    return name if base is None else base


def has_role(name, settings, group):
    """True when the name carries the given role; group 'ALL' means any role."""
    role = classify_role(name, settings)
    if group == 'ALL':
        return role is not None
    return role == group


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


# -----------------------------------------------------------------------------
# Bake-group quality tags (Outliner collection colors)
# -----------------------------------------------------------------------------
# A per-asset "Bake_<name>" collection is only bakeable when it contains both a
# low and a high member. We surface that health check as a collection color_tag
# so problems are visible at a glance in the Outliner.
#
#   GREEN  (COLOR_04) - both low and high present: ready to bake.
#   RED    (COLOR_01) - only low OR only high: something is missing, look here.
BAKEGROUP_TAG_OK = 'COLOR_04'    # green
BAKEGROUP_TAG_WARN = 'COLOR_01'  # red


def bakegroup_color_tag(object_names, settings):
    """Return the color_tag a per-asset bake collection should carry.

    Green when both a low and a high member are present (a complete namepair,
    ready to bake); red otherwise (only lows or only highs - a member is
    missing and the group needs attention). Cage-only members do not by
    themselves make a group complete.
    """
    has_low = has_high = False
    for name in object_names:
        role = classify_role(name, settings)
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
