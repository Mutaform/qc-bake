# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# ##### END GPL LICENSE BLOCK #####
#
# QC Bake
# =======
# A baking-namepair utility by Mutaform Studio.
#
# Select the low/high poly meshes for an asset and press "Create Namepair".
# QC Bake determines which object is high and which is low (by triangle, face,
# or vertex count) and renames them into a matching pair using the suffixes of
# the chosen naming convention. Multiple high-poly meshes, an optional cage,
# and automatic collection organisation are supported.
#
# This file only orchestrates registration; the actual functionality lives in
# the core / properties / operators / ui modules.

from . import operators, properties, ui

# Registration order matters: properties (PropertyGroup + Scene pointer) must
# exist before operators and panels reference scene.qc_bake.
_modules = (properties, operators, ui)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
