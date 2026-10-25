# EMBER 2018 v2 feature layout (2381 dimensions)

This project uses the published **EMBER2018 feature version 2** files
(`train_features_0.jsonl` … `train_features_5.jsonl`,
`test_features.jsonl`). EMBER2024 uses feature version 3 and is out of scope.

Raw records have no `features` wrapper. The top-level keys are:

```text
sha256, md5, appeared, label, avclass, histogram, byteentropy, strings,
general, header, section, imports, exports, datadirectories
```

`src/data/ember.py` implements the layout below independently from the
published specification. The official `elastic/ember` extraction code is
AGPL-3.0 and was **not copied or vendored**; the EMBER data files themselves
are distributed under MIT terms. See
[`../data_cards/ember2018.md`](../data_cards/ember2018.md) for the license and
dataset card.

## Group offsets

All vectors are `float32`, row-major, with exactly 2381 positions:

| Group | Start | Stop | Dim | Processing |
|---|---:|---:|---:|---|
| `histogram` | 0 | 256 | 256 | raw byte counts normalised to sum 1 |
| `byteentropy` | 256 | 512 | 256 | raw 16×16 byte/entropy counts flattened and normalised to sum 1 |
| `strings` | 512 | 616 | 104 | string statistics (see below) |
| `general` | 616 | 626 | 10 | scalar PE/file counts |
| `header` | 626 | 688 | 62 | timestamp, five 10-dim hashes, eleven scalars |
| `section` | 688 | 943 | 255 | five counts plus five 50-dim hashes |
| `imports` | 943 | 2223 | 1280 | 256 library + 1024 `library:function` hashes |
| `exports` | 2223 | 2351 | 128 | exported-function-name hash |
| `datadirectories` | 2351 | 2381 | 30 | size and virtual address of the first 15 entries |

Histogram and byte-entropy groups are divided by their raw sum. If a raw
counter is all zero, this implementation writes a zero vector instead of
producing `NaN`.

## Strings — 104 dimensions

```text
512:  numstrings
513:  avlength
514:  printables
515:  printabledist[0..95] / max(1, printables)
611:  entropy
612:  paths
613:  urls
614:  registry
615:  MZ
```

The 96-bin printable-character histogram is normalised by `printables`, with
a divisor of 1 when `printables == 0`.

## General — 10 dimensions

The canonical raw-JSON order is preserved:

```text
616: size          621: has_relocations
617: vsize         622: has_resources
618: has_debug     623: has_signature
619: exports       624: has_tls
620: imports       625: symbols
```

## Header — 62 dimensions

```text
626:      coff.timestamp
627:637  FeatureHasher(10, string) over coff.machine
637:647  FeatureHasher(10, string) over coff.characteristics
647:657  FeatureHasher(10, string) over optional.subsystem
657:667  FeatureHasher(10, string) over optional.dll_characteristics
667:677  FeatureHasher(10, string) over optional.magic
677:688  eleven optional-header scalar fields, in this order:
         major_image_version, minor_image_version,
         major_linker_version, minor_linker_version,
         major_operating_system_version, minor_operating_system_version,
         major_subsystem_version, minor_subsystem_version,
         sizeof_code, sizeof_headers, sizeof_heap_commit
```

The header nested objects are `header.coff` and `header.optional` in the JSON
files. Hashers use the scikit-learn defaults (signed hashing,
`alternate_sign=True`) to match the published feature semantics.

## Section — 255 dimensions

```text
688:  number of sections
689:  number of sections with size == 0
690:  number of sections with an empty name
691:  number of sections that are both MEM_READ and MEM_EXECUTE
692:  number of sections with MEM_WRITE

693:743   FeatureHasher(50, pair) over (section name, size)
743:793   FeatureHasher(50, pair) over (section name, entropy)
793:843   FeatureHasher(50, pair) over (section name, vsize)
843:893   FeatureHasher(50, string) over the entry-point section name
893:943   FeatureHasher(50, string) over the entry section's property strings
```

## Imports — 1280 dimensions

```text
943:1199   FeatureHasher(256, string) over unique lower-cased library names
1199:2223  FeatureHasher(1024, string) over "library:function" strings
```

Library names are lower-cased; function names are kept as published. Ordinal
imports remain strings such as `ordinal123`.

## Exports — 128 dimensions

```text
2223:2351  FeatureHasher(128, string) over exported function names
```

## Data directories — 30 dimensions

For the first 15 entries in the order present in `datadirectories` (not sorted
by name), write `size` then `virtual_address`:

```text
2351 + 2*i      size of entry i
2351 + 2*i + 1  virtual_address of entry i
```

Missing entries are left as zeros. This matches the official order
(`EXPORT_TABLE`, `IMPORT_TABLE`, …, `CLR_RUNTIME_HEADER` in the released
files), while still preserving the JSON order if a record differs.

## Validation and robustness

Every record is validated before vectorisation: required keys, 64-char
lowercase `sha256`, `appeared` in `YYYY-MM`, label in `{-1, 0, 1}`, group
shapes, and a finite 2381-dim `float32` result. Empty `imports`, `exports`, or
`section.sections` produce zero hashed blocks rather than crashing.

`label = -1` (unlabelled) rows are counted in source statistics but excluded
from the supervised train/val arrays. The official 200k test set is preserved
and never used to fit the scaler or choose the validation split.
