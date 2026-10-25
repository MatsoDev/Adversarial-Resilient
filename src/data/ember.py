"""EMBER 2018 v2 loading, validation, vectorisation and preprocessing.

The local dataset is the published EMBER2018 feature version 2 release
(2381 dimensions).  This module contains an independent, clean-room
implementation of the published feature layout; the official
``elastic/ember`` extraction code is AGPL-3.0 and was not copied or vendored.

Raw records are JSONL with top-level keys ``sha256``, ``md5``, ``appeared``,
``label``, ``avclass``, ``histogram``, ``byteentropy``, ``strings``,
``general``, ``header``, ``section``, ``imports``, ``exports`` and
``datadirectories``.  There is no ``features`` wrapper.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import time
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction import FeatureHasher
from tqdm import tqdm

from src.data.preprocessing import (
    artifact_record,
    atomic_save_npy,
    code_revision,
    compute_scaler_stats,
    finalize_atomic_memmap,
    load_json,
    open_atomic_memmap,
    remove_rows_with_ids,
    sha256_file,
    time_based_split,
    utc_now_iso,
    verify_manifest_artifacts,
    write_json_atomic,
)
from src.utils.seed import set_seed

logger = logging.getLogger(__name__)

FEATURE_DIM = 2381
FEATURE_GROUPS: dict[str, tuple[int, int]] = {
    "histogram": (0, 256),
    "byteentropy": (256, 512),
    "strings": (512, 616),
    "general": (616, 626),
    "header": (626, 688),
    "section": (688, 943),
    "imports": (943, 2223),
    "exports": (2223, 2351),
    "datadirectories": (2351, 2381),
}

TRAIN_FILE_NAMES: tuple[str, ...] = tuple(f"train_features_{index}.jsonl" for index in range(6))
TEST_FILE_NAME = "test_features.jsonl"

EXPECTED_TRAIN_ROWS = 800_000
EXPECTED_TEST_ROWS = 200_000
EXPECTED_TRAIN_LABEL_COUNTS = {-1: 200_000, 0: 300_000, 1: 300_000}
EXPECTED_TEST_LABEL_COUNTS = {0: 100_000, 1: 100_000}

# SHA-256 of the exact local files verified for this project. Hashes are
# checked on every run unless --force / --skip-source-check is used.
SOURCE_SHA256: dict[str, str] = {
    "train_features_0.jsonl": "c2b11558db11e5c0983c49bf6a94bc93ff086b2254182728ec7257773205f3d1",
    "train_features_1.jsonl": "dd9b55d8282e1698610971bd132d570f5b4dbba9da7946d3108efefe1c3a7ca0",
    "train_features_2.jsonl": "d7d8155f4f22167c5dad83d37c65a03d1aaf286f44803f99a81493ba8ce990a7",
    "train_features_3.jsonl": "097a64704c500e6c665c725d87677de370e30da05cfe7d803d4a2af42885a032",
    "train_features_4.jsonl": "c701a968b741b030b65e5fed2b68becb8f851d48df2c9eb9305a03b628c7cba4",
    "train_features_5.jsonl": "f51fb4a02c3a92d0cbd6a5cf0fc38f51c5029135d1927f5c631d592f93e98bff",
    "test_features.jsonl": "8225d87aa4d2ec1c65583dc415c9058a126be9dc0e9292f59b779106f0da6ac9",
}

REQUIRED_KEYS: tuple[str, ...] = (
    "sha256",
    "md5",
    "appeared",
    "label",
    "avclass",
    "histogram",
    "byteentropy",
    "strings",
    "general",
    "header",
    "section",
    "imports",
    "exports",
    "datadirectories",
)

GENERAL_FIELDS: tuple[str, ...] = (
    "size",
    "vsize",
    "has_debug",
    "exports",
    "imports",
    "has_relocations",
    "has_resources",
    "has_signature",
    "has_tls",
    "symbols",
)

HEADER_OPTIONAL_FIELDS: tuple[str, ...] = (
    "major_image_version",
    "minor_image_version",
    "major_linker_version",
    "minor_linker_version",
    "major_operating_system_version",
    "minor_operating_system_version",
    "major_subsystem_version",
    "minor_subsystem_version",
    "sizeof_code",
    "sizeof_headers",
    "sizeof_heap_commit",
)

STRING_FIELDS: tuple[str, ...] = (
    "numstrings",
    "avlength",
    "printabledist",
    "printables",
    "entropy",
    "paths",
    "urls",
    "registry",
    "MZ",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_APPEARED_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class EmberSourceFiles:
    """Discovered EMBER source files."""

    train: tuple[Path, ...]
    test: Path

    @property
    def all(self) -> tuple[Path, ...]:
        return (*self.train, self.test)


def feature_names() -> list[str]:
    """Human-readable names for the 2381 vector positions."""
    names: list[str] = []
    for group, (start, stop) in FEATURE_GROUPS.items():
        width = stop - start
        if group == "strings":
            semantic = (
                "numstrings",
                "avlength",
                "printables",
                *(f"printabledist_{index}" for index in range(96)),
                "entropy",
                "paths",
                "urls",
                "registry",
                "MZ",
            )
            names.extend(f"strings_{label}" for label in semantic)
        elif group == "general":
            names.extend(f"general_{label}" for label in GENERAL_FIELDS)
        else:
            names.extend(f"{group}_{index}" for index in range(width))
    if len(names) != FEATURE_DIM:
        raise AssertionError(f"feature name layout has {len(names)} entries")
    return names


def _train_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"train_features_(\d+)\.jsonl$", path.name)
    return (int(match.group(1)) if match else 10**9, path.name)


def discover_ember_files(source_dir: str | Path, *, strict: bool = True) -> EmberSourceFiles:
    """Find the official EMBER JSONL files in a local directory."""
    source = Path(source_dir).expanduser()
    if not source.is_dir():
        raise FileNotFoundError(
            f"EMBER source directory not found: {source}. Set EMBER_DATA_DIR or pass --source."
        )
    train_files = tuple(sorted(source.glob("train_features_*.jsonl"), key=_train_sort_key))
    test_file = source / TEST_FILE_NAME
    if not train_files:
        raise FileNotFoundError(f"no train_features_*.jsonl files in {source}")
    if not test_file.is_file():
        raise FileNotFoundError(f"missing {TEST_FILE_NAME} in {source}")
    if strict:
        expected = list(TRAIN_FILE_NAMES)
        found = [path.name for path in train_files]
        if found != expected:
            raise FileNotFoundError(
                f"expected EMBER train files {expected}, found {found} in {source}"
            )
    return EmberSourceFiles(train=train_files, test=test_file)


def _validate_record(record: Mapping[str, Any], *, context: str) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in record]
    if missing:
        raise ValueError(f"{context}: missing required keys {missing}")

    sha256 = record["sha256"]
    if not isinstance(sha256, str) or not _SHA256_RE.match(sha256):
        raise ValueError(f"{context}: invalid sha256 {sha256!r}")

    appeared = record["appeared"]
    if not isinstance(appeared, str) or not _APPEARED_RE.match(appeared):
        raise ValueError(f"{context}: invalid appeared value {appeared!r}")

    label = record["label"]
    if label not in (-1, 0, 1):
        raise ValueError(f"{context}: label must be one of -1/0/1, got {label!r}")

    histogram = record["histogram"]
    if not isinstance(histogram, list) or len(histogram) != 256:
        raise ValueError(f"{context}: histogram must have 256 entries")

    byteentropy = record["byteentropy"]
    if not isinstance(byteentropy, list) or len(byteentropy) != 256:
        raise ValueError(f"{context}: byteentropy must have 256 entries")

    strings = record["strings"]
    if not isinstance(strings, dict):
        raise ValueError(f"{context}: strings must be an object")
    missing_strings = [key for key in STRING_FIELDS if key not in strings]
    if missing_strings:
        raise ValueError(f"{context}: strings missing fields {missing_strings}")
    if not isinstance(strings["printabledist"], list) or len(strings["printabledist"]) != 96:
        raise ValueError(f"{context}: strings.printabledist must have 96 entries")

    general = record["general"]
    if not isinstance(general, dict) or list(general) != list(GENERAL_FIELDS):
        raise ValueError(
            f"{context}: general must contain {list(GENERAL_FIELDS)} in the official order"
        )

    header = record["header"]
    if not isinstance(header, dict) or "coff" not in header or "optional" not in header:
        raise ValueError(f"{context}: header must contain 'coff' and 'optional'")
    coff = header["coff"]
    optional = header["optional"]
    if not isinstance(coff, dict) or not isinstance(optional, dict):
        raise ValueError(f"{context}: header.coff/header.optional must be objects")
    for key in ("timestamp", "machine", "characteristics"):
        if key not in coff:
            raise ValueError(f"{context}: header.coff missing {key!r}")
    for key in ("subsystem", "dll_characteristics", "magic", *HEADER_OPTIONAL_FIELDS):
        if key not in optional:
            raise ValueError(f"{context}: header.optional missing {key!r}")

    section = record["section"]
    if not isinstance(section, dict) or "entry" not in section or "sections" not in section:
        raise ValueError(f"{context}: section must contain 'entry' and 'sections'")
    if not isinstance(section["entry"], str):
        raise ValueError(f"{context}: section.entry must be a string")
    if not isinstance(section["sections"], list):
        raise ValueError(f"{context}: section.sections must be a list")
    for item in section["sections"]:
        if not isinstance(item, dict) or any(
            key not in item for key in ("name", "size", "entropy", "vsize", "props")
        ):
            raise ValueError(f"{context}: malformed section entry {item!r}")
        if not isinstance(item["props"], list):
            raise ValueError(f"{context}: section props must be a list")

    if not isinstance(record["imports"], dict):
        raise ValueError(f"{context}: imports must be an object")
    if not isinstance(record["exports"], list):
        raise ValueError(f"{context}: exports must be a list")
    if not isinstance(record["datadirectories"], list):
        raise ValueError(f"{context}: datadirectories must be a list")


def _normalized_counts(values: Sequence[float], *, expected: int, context: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    if array.size != expected:
        raise ValueError(f"{context}: expected {expected} counts, got {array.size}")
    total = float(array.sum())
    if total > 0:
        array = array / total
    else:
        array = np.zeros_like(array)
    return array


class EmberVectorizer:
    """Convert one EMBER raw JSON record to the official 2381-dim vector.

    ``sklearn.feature_extraction.FeatureHasher`` is used with the same
    ``n_features`` / ``input_type`` (and default signed hashing) as the
    published feature specification. Hashers are cached per instance; the
    class is stateless apart from that cache.
    """

    def __init__(self) -> None:
        self._h10 = FeatureHasher(n_features=10, input_type="string")
        self._h50_pair = FeatureHasher(n_features=50, input_type="pair")
        self._h50_string = FeatureHasher(n_features=50, input_type="string")
        self._h256 = FeatureHasher(n_features=256, input_type="string")
        self._h1024 = FeatureHasher(n_features=1024, input_type="string")
        self._h128 = FeatureHasher(n_features=128, input_type="string")

    @staticmethod
    def _hashed(hasher: FeatureHasher, tokens: Sequence[Any]) -> np.ndarray:
        matrix = hasher.transform([list(tokens)]).toarray()[0]
        return np.asarray(matrix, dtype=np.float32)

    def transform(self, record: Mapping[str, Any], *, context: str = "record") -> np.ndarray:
        _validate_record(record, context=context)
        output = np.zeros(FEATURE_DIM, dtype=np.float32)

        output[0:256] = _normalized_counts(
            record["histogram"], expected=256, context=f"{context}: histogram"
        )
        output[256:512] = _normalized_counts(
            record["byteentropy"], expected=256, context=f"{context}: byteentropy"
        )

        strings = record["strings"]
        printables = float(strings["printables"])
        divisor = printables if printables > 0 else 1.0
        printabledist = np.asarray(strings["printabledist"], dtype=np.float32) / divisor
        output[512:616] = np.concatenate(
            [
                np.asarray(
                    [
                        strings["numstrings"],
                        strings["avlength"],
                        strings["printables"],
                    ],
                    dtype=np.float32,
                ),
                printabledist.astype(np.float32),
                np.asarray(
                    [
                        strings["entropy"],
                        strings["paths"],
                        strings["urls"],
                        strings["registry"],
                        strings["MZ"],
                    ],
                    dtype=np.float32,
                ),
            ]
        )

        general = record["general"]
        output[616:626] = np.asarray([general[key] for key in GENERAL_FIELDS], dtype=np.float32)

        header = record["header"]
        coff = header["coff"]
        optional = header["optional"]
        output[626] = float(coff["timestamp"])
        output[627:637] = self._hashed(self._h10, [str(coff["machine"])])
        output[637:647] = self._hashed(self._h10, [str(value) for value in coff["characteristics"]])
        output[647:657] = self._hashed(self._h10, [str(optional["subsystem"])])
        output[657:667] = self._hashed(
            self._h10, [str(value) for value in optional["dll_characteristics"]]
        )
        output[667:677] = self._hashed(self._h10, [str(optional["magic"])])
        output[677:688] = np.asarray(
            [optional[key] for key in HEADER_OPTIONAL_FIELDS], dtype=np.float32
        )

        section = record["section"]
        sections = section["sections"]
        entry = section["entry"]
        output[688] = len(sections)
        output[689] = sum(1 for item in sections if float(item["size"]) == 0.0)
        output[690] = sum(1 for item in sections if str(item["name"]) == "")
        output[691] = sum(
            1 for item in sections if "MEM_READ" in item["props"] and "MEM_EXECUTE" in item["props"]
        )
        output[692] = sum(1 for item in sections if "MEM_WRITE" in item["props"])
        pair_sizes = [(str(item["name"]), float(item["size"])) for item in sections]
        pair_entropy = [(str(item["name"]), float(item["entropy"])) for item in sections]
        pair_vsize = [(str(item["name"]), float(item["vsize"])) for item in sections]
        output[693:743] = self._hashed(self._h50_pair, pair_sizes)
        output[743:793] = self._hashed(self._h50_pair, pair_entropy)
        output[793:843] = self._hashed(self._h50_pair, pair_vsize)
        output[843:893] = self._hashed(self._h50_string, [str(entry)])
        entry_props = [
            str(prop)
            for item in sections
            if str(item["name"]) == str(entry)
            for prop in item["props"]
        ]
        output[893:943] = self._hashed(self._h50_string, entry_props)

        imports = record["imports"]
        libraries = sorted({str(library).lower() for library in imports})
        functions = [
            f"{str(library).lower()}:{str(function)}"
            for library, entries in imports.items()
            for function in (entries or [])
        ]
        output[943:1199] = self._hashed(self._h256, libraries)
        output[1199:2223] = self._hashed(self._h1024, functions)

        output[2223:2351] = self._hashed(self._h128, [str(export) for export in record["exports"]])

        for index, entry_info in enumerate(record["datadirectories"][:15]):
            size = entry_info.get("size") if isinstance(entry_info, dict) else None
            address = entry_info.get("virtual_address") if isinstance(entry_info, dict) else None
            output[2351 + 2 * index] = float(size) if size is not None else 0.0
            output[2351 + 2 * index + 1] = float(address) if address is not None else 0.0

        if output.shape != (FEATURE_DIM,):
            raise AssertionError(f"unexpected feature shape {output.shape}")
        if not np.isfinite(output).all():
            raise ValueError(f"{context}: vector contains NaN or infinite values")
        return output


def iter_ember_records(path: str | Path) -> Iterable[tuple[int, dict[str, Any]]]:
    """Yield ``(zero_based_line, record)`` from a JSONL file without loading it."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line_index, line in enumerate(handle):
            if not line.strip():
                continue
            yield line_index, json.loads(line)


def _scan_ember_file(task: tuple[str, str, bool]) -> dict[str, Any]:
    path_str, partition, show_progress = task
    path = Path(path_str)
    records: list[tuple[str, str, str, int, int, int]] = []
    label_counts: Counter[int] = Counter()
    missing_counts: Counter[str] = Counter()
    total_lines = 0
    with open(path, "rb") as handle:
        iterator: Iterable[bytes]
        if show_progress:
            iterator = tqdm(handle, desc=path.name, unit="rec", leave=False)
        else:
            iterator = handle
        offset = 0
        for line_index, line in enumerate(iterator):
            current_offset = offset
            offset += len(line)
            total_lines += 1
            if not line.strip():
                continue
            record = json.loads(line)
            missing_counts.update(key for key in REQUIRED_KEYS if key not in record)
            label = int(record.get("label", -999))
            label_counts[label] += 1
            records.append(
                (
                    str(record.get("sha256", "")),
                    str(record.get("md5", "")),
                    str(record.get("appeared", "")),
                    label,
                    line_index,
                    current_offset,
                )
            )
    frame = pd.DataFrame(
        records,
        columns=["sha256", "md5", "appeared", "label", "source_index", "source_offset"],
    )
    frame["source_file"] = path.name
    frame["partition"] = partition
    frame["label"] = frame["label"].astype(np.int16)
    frame["source_index"] = frame["source_index"].astype(np.int64)
    frame["source_offset"] = frame["source_offset"].astype(np.int64)
    return {
        "name": path.name,
        "partition": partition,
        "rows": total_lines,
        "label_counts": {int(key): int(value) for key, value in label_counts.items()},
        "missing_keys": dict(missing_counts),
        "frame": frame,
    }


def scan_ember_metadata(
    files: EmberSourceFiles,
    *,
    jobs: int = 1,
    show_progress: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Scan metadata for all EMBER files (bounded memory, JSONL streaming)."""
    tasks = [(str(path), "train", show_progress and jobs <= 1) for path in files.train] + [
        (str(files.test), "test", show_progress and jobs <= 1)
    ]

    if jobs <= 1:
        results = [_scan_ember_file(task) for task in tasks]
    else:
        results_by_name: dict[str, dict[str, Any]] = {}
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            futures = {executor.submit(_scan_ember_file, task): task for task in tasks}
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="scanning EMBER", unit="file"
            ):
                result = future.result()
                results_by_name[result["name"]] = result
        ordered_names = [path.name for path in files.train] + [files.test.name]
        results = [results_by_name[name] for name in ordered_names]

    train_frames = [result["frame"] for result in results if result["partition"] == "train"]
    test_frames = [result["frame"] for result in results if result["partition"] == "test"]
    train_frame = pd.concat(train_frames, ignore_index=True) if train_frames else pd.DataFrame()
    test_frame = pd.concat(test_frames, ignore_index=True) if test_frames else pd.DataFrame()
    file_stats = [
        {key: value for key, value in result.items() if key != "frame"} for result in results
    ]
    return train_frame, test_frame, file_stats


def _sample_frame(frame: pd.DataFrame, *, max_samples: int | None, seed: int) -> pd.DataFrame:
    if max_samples is None or max_samples >= len(frame):
        return frame.reset_index(drop=True)
    if max_samples < 1:
        raise ValueError("max_samples must be positive")
    from sklearn.model_selection import train_test_split

    labels = frame["label"].to_numpy()
    n_classes = len(np.unique(labels))
    if max_samples < n_classes:
        raise ValueError(f"max_samples must be at least the number of classes ({n_classes})")
    chosen, _ = train_test_split(
        np.arange(len(frame)),
        train_size=max_samples,
        random_state=seed,
        stratify=labels,
    )
    return frame.iloc[np.sort(chosen)].reset_index(drop=True)


def _check_ember_source_counts(file_stats: Sequence[dict[str, Any]], *, force: bool) -> None:
    if force:
        return
    train_rows = sum(stat["rows"] for stat in file_stats if stat["partition"] == "train")
    test_rows = sum(stat["rows"] for stat in file_stats if stat["partition"] == "test")
    train_labels: Counter[int] = Counter()
    test_labels: Counter[int] = Counter()
    for stat in file_stats:
        target = train_labels if stat["partition"] == "train" else test_labels
        target.update(stat["label_counts"])
    problems: list[str] = []
    if train_rows != EXPECTED_TRAIN_ROWS:
        problems.append(f"train rows {train_rows} != {EXPECTED_TRAIN_ROWS}")
    if test_rows != EXPECTED_TEST_ROWS:
        problems.append(f"test rows {test_rows} != {EXPECTED_TEST_ROWS}")
    if dict(train_labels) != EXPECTED_TRAIN_LABEL_COUNTS:
        problems.append(f"train labels {dict(train_labels)} != {EXPECTED_TRAIN_LABEL_COUNTS}")
    if dict(test_labels) != EXPECTED_TEST_LABEL_COUNTS:
        problems.append(f"test labels {dict(test_labels)} != {EXPECTED_TEST_LABEL_COUNTS}")
    if problems:
        raise ValueError(
            "EMBER source does not match the expected EMBER2018 v2 composition: "
            + "; ".join(problems)
            + " (use --force to override)"
        )


def _source_file_info(
    paths: Sequence[Path], *, verify_hashes: bool, force: bool = False
) -> list[dict[str, Any]]:
    infos: list[dict[str, Any]] = []
    for path in paths:
        info: dict[str, Any] = {"name": path.name, "size_bytes": path.stat().st_size}
        if verify_hashes:
            digest = sha256_file(path)
            info["sha256"] = digest
            expected = SOURCE_SHA256.get(path.name)
            if expected and digest != expected and not force:
                raise ValueError(
                    f"sha256 mismatch for {path.name}: expected {expected}, found {digest} "
                    "(use --force to override)"
                )
        infos.append(info)
    return infos


def _vectorize_ember_file(task: tuple[Any, ...]) -> dict[str, Any]:
    (
        path_str,
        line_indices,
        offsets,
        split_codes,
        target_rows,
        file_rows,
        output_paths,
        show_progress,
    ) = task
    vectorizer = EmberVectorizer()
    outputs: dict[int, np.memmap] = {}
    for code in sorted({int(value) for value in split_codes}):
        outputs[code] = np.load(output_paths[code], mmap_mode="r+")

    n_selected = len(line_indices)
    started = time.perf_counter()

    def _process(line: bytes, selection_position: int, line_index: int) -> None:
        context = f"{Path(path_str).name}:{line_index + 1}"
        try:
            record = json.loads(line)
            vector = vectorizer.transform(record, context=context)
        except Exception as error:  # add file/line context and re-raise
            raise RuntimeError(f"{context}: {error}") from error
        code = int(split_codes[selection_position])
        row = int(target_rows[selection_position])
        outputs[code][row] = vector

    if n_selected:
        if n_selected < file_rows * 0.5:
            with open(path_str, "rb") as handle:
                positions: Iterable[int] = (
                    tqdm(range(n_selected), desc=Path(path_str).name, unit="rec", leave=False)
                    if show_progress
                    else range(n_selected)
                )
                for selection_position in positions:
                    handle.seek(int(offsets[selection_position]))
                    line = handle.readline()
                    line_index = int(line_indices[selection_position])
                    _process(line, selection_position, line_index)
        else:
            selected_position = 0
            with open(path_str, "rb") as handle:
                iterator: Iterable[bytes] = (
                    tqdm(
                        handle,
                        total=file_rows,
                        desc=Path(path_str).name,
                        unit="rec",
                        leave=False,
                    )
                    if show_progress
                    else handle
                )
                for line_index, line in enumerate(iterator):
                    if selected_position >= n_selected:
                        break
                    if line_index == int(line_indices[selected_position]):
                        _process(line, selected_position, line_index)
                        selected_position += 1
            if selected_position != n_selected:
                raise RuntimeError(
                    f"{path_str}: expected {n_selected} selected records, "
                    f"found {selected_position}"
                )

    for output in outputs.values():
        output.flush()
        del output
    return {
        "file": Path(path_str).name,
        "rows": int(n_selected),
        "seconds": round(time.perf_counter() - started, 3),
    }


def _assign_target_rows(frame: pd.DataFrame, split_name: str, code: int) -> pd.DataFrame:
    frame = frame.copy()
    frame["split"] = split_name
    frame["split_code"] = np.int8(code)
    frame["target_row"] = np.arange(len(frame), dtype=np.int64)
    return frame


def _write_csv_atomic(frame: pd.DataFrame, path: Path, columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    frame.loc[:, list(columns)].to_csv(tmp, index=False, lineterminator="\n")
    with open(tmp, "rb+") as handle:
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _split_metadata_for_json(frame: pd.DataFrame) -> dict[str, Any]:
    counts = frame["label"].value_counts().sort_index()
    return {
        "rows": int(len(frame)),
        "label_counts": {str(int(key)): int(value) for key, value in counts.items()},
        "min_appeared": str(frame["appeared"].min()) if len(frame) else None,
        "max_appeared": str(frame["appeared"].max()) if len(frame) else None,
    }


def _guard_subset_output(output: Path, *, subset: bool) -> None:
    if not subset:
        return
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        return
    existing = load_json(manifest_path)
    if not existing.get("subset", True):
        raise RuntimeError(
            f"refusing to overwrite full-run artifacts in {output} with a subset run; "
            "choose a different --output-dir"
        )


def run_ember_preprocessing(
    source_dir: str | Path,
    output_dir: str | Path,
    *,
    seed: int = 42,
    max_samples: int | None = None,
    jobs: int = 1,
    force: bool = False,
    verify_source: bool = True,
    scaler: bool = True,
    val_fraction: float = 0.15,
) -> dict[str, Any]:
    """Run the complete EMBER preprocessing pipeline and write a manifest."""
    set_seed(seed)
    source = Path(source_dir).expanduser()
    output = Path(output_dir).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    subset = max_samples is not None
    _guard_subset_output(output, subset=subset)

    files = discover_ember_files(source, strict=verify_source)
    logger.info(
        "EMBER source: %d train files + test file under %s",
        len(files.train),
        source,
    )

    source_infos = _source_file_info(files.all, verify_hashes=verify_source, force=force)
    source_info_by_name = {info["name"]: info for info in source_infos}

    train_meta_full, test_meta_full, file_stats = scan_ember_metadata(
        files, jobs=jobs, show_progress=True
    )
    if verify_source:
        _check_ember_source_counts(file_stats, force=force)
    for stat in file_stats:
        if stat["missing_keys"]:
            raise ValueError(f"{stat['name']} is missing required keys: {stat['missing_keys']}")
    invalid_labels = sorted(
        set(train_meta_full["label"].unique()) | set(test_meta_full["label"].unique())
    )
    if not set(invalid_labels).issubset({-1, 0, 1}):
        raise ValueError(f"unexpected EMBER labels {invalid_labels}")

    labeled_full = train_meta_full.loc[train_meta_full["label"].isin([0, 1])].reset_index(drop=True)
    if subset:
        labeled_selected = _sample_frame(labeled_full, max_samples=max_samples, seed=seed)
        test_selected = _sample_frame(test_meta_full, max_samples=max_samples, seed=seed)
    else:
        labeled_selected = labeled_full
        test_selected = test_meta_full

    test_shas = set(test_meta_full["sha256"].astype(str))
    labeled_clean, removed_test_duplicates = remove_rows_with_ids(
        labeled_selected, id_col="sha256", blocked_ids=test_shas
    )
    if labeled_clean.empty:
        raise RuntimeError("no labeled EMBER training rows remain after duplicate removal")

    duplicate_sha_rows = int(len(labeled_clean) - labeled_clean["sha256"].nunique())
    duplicate_sha_groups = int((labeled_clean.groupby("sha256").size() > 1).sum())
    split_array, split_info = time_based_split(
        labeled_clean,
        val_fraction=val_fraction,
        label_col="label",
        time_col="appeared",
        id_col="sha256",
        min_val_per_class=50,
    )
    if split_info["label_conflicts"]:
        raise ValueError(
            f"found {split_info['label_conflicts']} duplicate sha256 groups with conflicting labels"
        )
    labeled_clean = labeled_clean.copy()
    labeled_clean["time_split"] = split_array

    sort_columns = ["appeared", "sha256", "source_file", "source_index"]
    train_frame = (
        labeled_clean.loc[labeled_clean["time_split"] == 0]
        .sort_values(sort_columns, kind="mergesort")
        .reset_index(drop=True)
    )
    val_frame = (
        labeled_clean.loc[labeled_clean["time_split"] == 1]
        .sort_values(sort_columns, kind="mergesort")
        .reset_index(drop=True)
    )
    test_frame = test_selected.sort_values(
        ["source_file", "source_index"], kind="mergesort"
    ).reset_index(drop=True)

    train_shas = set(train_frame["sha256"].astype(str))
    val_shas = set(val_frame["sha256"].astype(str))
    if train_shas & val_shas:
        raise AssertionError("duplicate sha256 found across train and val")
    if (train_shas | val_shas) & test_shas:
        raise AssertionError("train/val sha256 found in the official test set")

    train_frame = _assign_target_rows(train_frame, "train", 0)
    val_frame = _assign_target_rows(val_frame, "val", 1)
    test_frame = _assign_target_rows(test_frame, "test", 2)

    total_rows = len(train_frame) + len(val_frame) + len(test_frame)
    estimated_bytes = total_rows * FEATURE_DIM * 4
    free_bytes = shutil.disk_usage(output).free
    if estimated_bytes > 0 and free_bytes < int(estimated_bytes * 1.2):
        raise RuntimeError(
            f"not enough free disk under {output}: need about "
            f"{estimated_bytes * 1.2 / 1e9:.1f} GB, have {free_bytes / 1e9:.1f} GB"
        )

    combined = pd.concat(
        [
            train_frame.assign(split_code=np.int8(0)),
            val_frame.assign(split_code=np.int8(1)),
            test_frame.assign(split_code=np.int8(2)),
        ],
        ignore_index=True,
    )
    file_rows = {stat["name"]: stat["rows"] for stat in file_stats}

    output_specs: dict[str, dict[str, Any]] = {}
    for split_name, frame in (("train", train_frame), ("val", val_frame), ("test", test_frame)):
        final_path = output / f"{split_name}_X.npy"
        memmap, tmp_path = open_atomic_memmap(
            final_path, shape=(len(frame), FEATURE_DIM), dtype="float32"
        )
        memmap.flush()
        del memmap
        output_specs[split_name] = {
            "final": final_path,
            "tmp": tmp_path,
            "shape": (len(frame), FEATURE_DIM),
            "code": {"train": 0, "val": 1, "test": 2}[split_name],
        }

    tasks: list[tuple[Any, ...]] = []
    output_paths = {int(spec["code"]): str(spec["tmp"]) for spec in output_specs.values()}
    for file_name in [path.name for path in files.train] + [files.test.name]:
        selected = combined.loc[combined["source_file"] == file_name].sort_values(
            "source_index", kind="mergesort"
        )
        if selected.empty:
            continue
        tasks.append(
            (
                str(source / file_name),
                selected["source_index"].to_numpy(dtype=np.int64),
                selected["source_offset"].to_numpy(dtype=np.int64),
                selected["split_code"].to_numpy(dtype=np.int8),
                selected["target_row"].to_numpy(dtype=np.int64),
                file_rows[file_name],
                output_paths,
                jobs <= 1,
            )
        )

    try:
        if jobs <= 1:
            results = [_vectorize_ember_file(task) for task in tasks]
        else:
            results = []
            with ProcessPoolExecutor(max_workers=jobs) as executor:
                futures = {executor.submit(_vectorize_ember_file, task): task[0] for task in tasks}
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="vectorising EMBER",
                    unit="file",
                ):
                    result = future.result()
                    results.append(result)
                    logger.info(
                        "vectorised %s: %d rows in %.1fs",
                        result["file"],
                        result["rows"],
                        result["seconds"],
                    )
        total_vectorized = sum(result["rows"] for result in results)
    except Exception:
        for spec in output_specs.values():
            try:
                os.unlink(spec["tmp"])
            except FileNotFoundError:
                pass
        raise

    expected_vectorized = len(train_frame) + len(val_frame) + len(test_frame)
    if total_vectorized != expected_vectorized:
        raise RuntimeError(f"vectorised {total_vectorized} rows, expected {expected_vectorized}")

    for split_name, frame in (("train", train_frame), ("val", val_frame), ("test", test_frame)):
        spec = output_specs[split_name]
        memmap = np.load(spec["tmp"], mmap_mode="r+")
        finalize_atomic_memmap(memmap, spec["tmp"], spec["final"])
        labels_path = output / f"{split_name}_y.npy"
        atomic_save_npy(labels_path, frame["label"].to_numpy(dtype=np.int8))
        logger.info("wrote %s and %s_y.npy (%d rows)", spec["final"].name, split_name, len(frame))

    feature_names_path = output / "feature_names.json"
    write_json_atomic(feature_names_path, feature_names())
    label_mapping_path = output / "label_mapping.json"
    write_json_atomic(
        label_mapping_path,
        {
            "dataset": "ember2018",
            "target": "binary",
            "labels": {"-1": "unlabeled", "0": "benign", "1": "malicious"},
            "supervised_labels": {"0": 0, "1": 1},
        },
    )

    metadata_columns = [
        "sha256",
        "appeared",
        "label",
        "source_file",
        "source_index",
        "split",
    ]
    for split_name, frame in (("train", train_frame), ("val", val_frame), ("test", test_frame)):
        _write_csv_atomic(frame, output / f"{split_name}_metadata.csv", metadata_columns)

    scaler_files: list[Path] = []
    if scaler:
        mean, scale = compute_scaler_stats(output / "train_X.npy")
        mean_path = output / "scaler_mean.npy"
        scale_path = output / "scaler_scale.npy"
        atomic_save_npy(mean_path, mean)
        atomic_save_npy(scale_path, scale)
        scaler_files = [mean_path, scale_path]
        write_json_atomic(
            output / "scaler.json",
            {
                "dataset": "ember2018",
                "fit_split": "train",
                "n_samples": int(len(train_frame)),
                "n_features": FEATURE_DIM,
                "zero_variance_scale": 1.0,
            },
        )

    artifacts: dict[str, Any] = {}
    for split_name, frame in (("train", train_frame), ("val", val_frame), ("test", test_frame)):
        artifacts[f"{split_name}_X"] = artifact_record(
            output / f"{split_name}_X.npy",
            root=output,
            shape=(len(frame), FEATURE_DIM),
            dtype="float32",
        )
        artifacts[f"{split_name}_y"] = artifact_record(
            output / f"{split_name}_y.npy",
            root=output,
            shape=(len(frame),),
            dtype="int8",
        )
        artifacts[f"{split_name}_metadata"] = artifact_record(
            output / f"{split_name}_metadata.csv", root=output
        )
    artifacts["feature_names"] = artifact_record(feature_names_path, root=output)
    artifacts["label_mapping"] = artifact_record(label_mapping_path, root=output)
    for path in scaler_files:
        artifacts[path.stem] = artifact_record(path, root=output)
    if scaler:
        artifacts["scaler"] = artifact_record(output / "scaler.json", root=output)

    source_files: list[dict[str, Any]] = []
    for stat in file_stats:
        info = dict(source_info_by_name[stat["name"]])
        info.update(
            {
                "partition": stat["partition"],
                "rows": stat["rows"],
                "label_counts": {
                    str(int(key)): int(value) for key, value in sorted(stat["label_counts"].items())
                },
            }
        )
        source_files.append(info)

    manifest: dict[str, Any] = {
        "dataset": "ember2018",
        "dataset_version": "EMBER2018 feature version 2 (2381 dimensions)",
        "subset": subset,
        "seed": seed,
        "generated_at": utc_now_iso(),
        "code_revision": code_revision(),
        "source_resolution": (
            "CLI --source > EMBER_DATA_DIR > data/raw/EMBER-Dataset > " "~/Documents/EMBER-Dataset"
        ),
        "source": {
            "files": source_files,
            "train_rows": int(len(train_meta_full)),
            "test_rows": int(len(test_meta_full)),
            "train_label_counts": {
                str(int(key)): int(value)
                for key, value in sorted(train_meta_full["label"].value_counts().items())
            },
            "test_label_counts": {
                str(int(key)): int(value)
                for key, value in sorted(test_meta_full["label"].value_counts().items())
            },
        },
        "sampling": {
            "max_samples": max_samples,
            "labeled_train_selected": int(len(labeled_selected)),
            "test_selected": int(len(test_selected)),
        },
        "preprocessing": {
            "vectorizer": "clean-room EMBER v2 implementation (src/data/ember.py)",
            "feature_dim": FEATURE_DIM,
            "feature_groups": {
                name: {"start": start, "stop": stop, "dim": stop - start}
                for name, (start, stop) in FEATURE_GROUPS.items()
            },
            "hasher": "sklearn.feature_extraction.FeatureHasher (official n_features/input_type)",
            "histogram_normalization": "sum to 1 (zero vector if sum is 0)",
            "byteentropy_normalization": "sum to 1 (zero vector if sum is 0)",
            "test_handling": "official test file preserved and never used for tuning",
            "scaler_fit_split": "train" if scaler else None,
            "validation_fraction": val_fraction,
        },
        "splits": {
            "train": _split_metadata_for_json(train_frame),
            "val": _split_metadata_for_json(val_frame),
            "test": _split_metadata_for_json(test_frame),
        },
        "split_strategy": split_info,
        "duplicates": {
            "removed_train_or_val_rows_duplicating_test": int(removed_test_duplicates),
            "duplicate_sha256_rows_in_supervised_train": duplicate_sha_rows,
            "duplicate_sha256_groups_in_supervised_train": duplicate_sha_groups,
            "cross_split_sha256": 0,
        },
        "artifacts": artifacts,
        "notes": [
            "label=-1 rows are counted but excluded from supervised train/val and arrays",
            "processed arrays are gitignored; only this manifest is committed",
            "no resampling or class weighting is applied in Sprint 2",
        ],
    }
    if subset:
        manifest["notes"].append(
            "subset=true: artifacts are a deterministic stratified sample and must not "
            "overwrite full-run artifacts"
        )

    manifest_path = output / "manifest.json"
    write_json_atomic(manifest_path, manifest)
    errors = verify_manifest_artifacts(manifest, output)
    if errors:
        raise RuntimeError("manifest verification failed: " + "; ".join(errors))
    logger.info("wrote manifest %s", manifest_path)
    return manifest
