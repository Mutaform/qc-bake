# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - icons
# ---------------
# A single source of truth for every icon the UI uses. Panels reference the
# semantic names here (e.g. ICON_CREATE) rather than hard-coding Blender icon
# identifiers inline, so restyling the whole add-on is a one-file change.
#
# All identifiers below are validated against Blender 5.x's icon set.

# Primary actions
ICON_CREATE = 'OUTLINER_OB_MESH'   # main "Create Namepair" button
ICON_SWAP = 'ARROW_LEFTRIGHT'      # swap high/low roles

# Section headers
ICON_NAMING = 'SORTALPHA'          # naming convention section
ICON_DETECT = 'MOD_REMESH'         # hi/lo detection criterion
ICON_OPTIONS = 'PREFERENCES'       # options section
ICON_VISIBILITY = 'HIDE_OFF'       # visibility section
ICON_BRAND = 'SHADERFX'            # reserved (currently no header icon)

# Poly roles
ICON_HIGH = 'MOD_SUBSURF'          # high poly
ICON_LOW = 'MESH_CUBE'             # low poly
ICON_CAGE = 'MOD_MESHDEFORM'       # cage
ICON_ALL = 'OUTLINER_COLLECTION'   # all renamed

# Toggle buttons
ICON_SHOW = 'HIDE_OFF'
ICON_HIDE = 'HIDE_ON'

# Option rows
ICON_RANDOM = 'FILE_REFRESH'
ICON_DATABLOCK = 'MESH_DATA'
ICON_DETECT_CAGE = 'MOD_MESHDEFORM'
ICON_COLLECTION = 'OUTLINER_COLLECTION'
ICON_HIDE_AFTER = 'RESTRICT_VIEW_ON'
ICON_OVERWRITE = 'ERROR'

# Utilities tab
ICON_UTIL_ORGANIZE = 'OUTLINER_COLLECTION'   # collection-layout section
ICON_UTIL_FLAT = 'MENU_PANEL'                # flat High/Low layout
ICON_UTIL_PERASSET = 'PACKAGE'               # per-asset Bake_<name> layout
ICON_UTIL_REDUCE = 'MOD_BUILD'               # reduce bake groups by distance
ICON_UTIL_RESTORE = 'LOOP_BACK'              # undo the last reduce pass
