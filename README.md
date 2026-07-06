# QC Bake

QC Bake is a Blender Extension by Mutaform Studio for preparing high-poly and low-poly object name pairs for texture baking workflows.

It helps rename selected objects into matching bake pairs, supports multiple high-poly meshes, optional cage objects, visibility switching, and collection organization for production baking setup.

## Compatibility

- Blender 5.0 or newer
- Packaged as a Blender Extension

## Install From Blender Repository

Add the extension repository URL in Blender:

```text
https://mutaform.github.io/qc-bake/index.json
```

Then sync repositories and search for `QC Bake`.

## Manual Install

1. Download the release ZIP from GitHub Releases or GitHub Pages.
2. In Blender, open `Edit > Preferences > Extensions`.
3. Use `Install from Disk`.
4. Select `qc_bake.zip`.
5. Enable `QC Bake`.

## Build Release ZIP

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_release.ps1
```

The release archive will be written to:

```text
dist/qc_bake.zip
```

## Repository Layout

```text
qc_bake/
  blender_manifest.toml
  __init__.py
  core.py
  properties.py
  operators/
  ui/
tools/
  build_release.ps1
```

## Publishing Notes

For GitHub Pages auto-install/update support, publish the repository from the `gh-pages` branch, root folder. Blender should use the direct `index.json` URL.

## License

This project is licensed under GPL-2.0-or-later, matching the Blender Extension manifest and source headers.
