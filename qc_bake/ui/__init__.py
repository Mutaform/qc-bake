# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake - ui package

from . import panel, utilities


def register():
    panel.register()
    utilities.register()


def unregister():
    utilities.unregister()
    panel.unregister()
