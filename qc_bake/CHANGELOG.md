# Changelog

## 2.1.0

### Added
- **Auto naming preset** (new default for new scenes). Role detection now
  understands any common convention at once: `_low/_high`, `_lo/_hi`,
  `_lp/_hp`, `_lowpoly/_highpoly`, `_hires`, `_cage` - in any case, as a
  suffix (`Chair_High`), an indexed suffix (`Chair_high_01`, Blender's
  `Chair_high.001`), a prefix (`high_Chair`, `HP_Chair`) or glued CamelCase
  (`ChairHigh`, `ChairHP`). Separators `_`, `.`, `-` and space all count.
  The other presets keep recognising only their own family, but with the
  same case / placement tolerance. New names are still written with the
  preset's suffixes (Auto writes `_low` / `_high`).

### Fixed
- **Visibility buttons stayed greyed out** on `_High` / `_Low` scenes: the
  panel kept its own case-sensitive name check. Every name check in the
  add-on (panel, visibility, Flat / Per Asset, Reduce, Swap, Create) now
  goes through one shared detector in `core`.
- **Swap High / Low** exchanges the two objects' names outright, so the
  pair keeps its own naming style instead of being rewritten to the preset.
- Preset enum values are pinned, so files saved with an older version keep
  their chosen convention after the list was reordered.

## 2.0.1

### Fixed
- **Suffix matching is now case-insensitive.** Scenes named `_High` / `_Low`
  (or `_HIGH` / `_LOW`) were invisible to *Flat*, *Per Asset*, *Reduce Bake
  Groups*, the visibility toggles and *Swap* because the presets only matched
  the exact lowercase `_high` / `_low`. All role detection now goes through a
  single `core.match_suffix` helper that ignores case.
- **Indexed members are matched strictly.** The multi-high form (`_high_01`)
  now requires the suffix to be followed by `_` plus digits, so an unrelated
  name fragment can no longer be mistaken for a role marker.

### Added
- **HP / LP naming preset** (`_lp` / `_hp`, with `_LP` / `_HP` matching too).

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
