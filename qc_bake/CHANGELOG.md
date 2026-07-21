# Changelog

## 2.0.0

Major update - accumulated a batch of workflow fixes since 1.1.0, most
notably making Reduce Bake Groups non-destructive.

### Added
- **Restore Bake Groups**: a new button next to *Reduce Bake Groups* that
  undoes the most recent reduce pass, restoring every renamed object (and
  mesh datablock) to its prior name. The backup is stored on the objects
  themselves, so it survives file save/reload and outlives Blender's native
  undo stack - not just a Ctrl+Z.
- **Per-Asset health colors**: in the *Per Asset* collection layout, each
  `Bake_<name>` collection is now color-tagged in the Outliner - green when
  it holds a complete low/high namepair, red when only a low or only a high
  is present (a member is missing or was accidentally deleted).
- **Version display**: the add-on's version now shows right-aligned in the
  N-panel header ("ver X.Y.Z"), read live from `blender_manifest.toml`.

### Changed
- **Collection Layout (Flat & Per Asset)**: newly built collections are now
  automatically collapsed in the Outliner after organizing, instead of being
  left fully expanded.

## 1.1.0

- Initial tracked release: namepair creation, swap, visibility toggles,
  reduce bake groups, and Flat / Per Asset collection organizing.
