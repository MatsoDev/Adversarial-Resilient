"""Synthetic dataset fixtures for the Sprint 2 tests (no real data needed)."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

GENERAL_FIELDS = (
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
HEADER_OPTIONAL_FIELDS = (
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
DATADIRECTORY_NAMES = (
    "EXPORT_TABLE",
    "IMPORT_TABLE",
    "RESOURCE_TABLE",
    "EXCEPTION_TABLE",
    "CERTIFICATE_TABLE",
    "BASE_RELOCATION_TABLE",
    "DEBUG",
    "ARCHITECTURE",
    "GLOBAL_PTR",
    "TLS_TABLE",
    "LOAD_CONFIG_TABLE",
    "BOUND_IMPORT",
    "IAT",
    "DELAY_IMPORT_DESCRIPTOR",
    "CLR_RUNTIME_HEADER",
)


def fake_sha(seed: int | str) -> str:
    return hashlib.sha256(str(seed).encode("utf-8")).hexdigest()


def ember_record(
    seed: int | str,
    label: int,
    appeared: str,
    *,
    size: int = 4096,
    sections: list[dict] | None = None,
    imports: dict[str, list[str]] | None = None,
    exports: list[str] | None = None,
    datadirectories: list[dict] | None = None,
    histogram: list[int] | None = None,
    byteentropy: list[int] | None = None,
) -> dict:
    if sections is None:
        sections = [
            {
                "name": ".text",
                "size": 1024,
                "entropy": 6.1,
                "vsize": 1000,
                "props": ["CNT_CODE", "MEM_EXECUTE", "MEM_READ"],
            },
            {
                "name": ".data",
                "size": 512,
                "entropy": 2.5,
                "vsize": 500,
                "props": ["CNT_INITIALIZED_DATA", "MEM_READ", "MEM_WRITE"],
            },
        ]
    if imports is None:
        imports = {"KERNEL32.dll": ["CreateFileA", "ReadFile"], "USER32.dll": ["MessageBoxA"]}
    if exports is None:
        exports = ["ExportedFunction"]
    if datadirectories is None:
        datadirectories = [
            {"name": name, "size": index * 10, "virtual_address": index * 100}
            for index, name in enumerate(DATADIRECTORY_NAMES)
        ]
    if histogram is None:
        histogram = [1] * 256
    if byteentropy is None:
        byteentropy = [2] * 256
    record = {
        "sha256": fake_sha(seed),
        "md5": fake_sha(f"md5-{seed}")[:32],
        "appeared": appeared,
        "label": label,
        "avclass": "",
        "histogram": histogram,
        "byteentropy": byteentropy,
        "strings": {
            "numstrings": 10,
            "avlength": 5.5,
            "printabledist": [1] * 96,
            "printables": 96,
            "entropy": 3.2,
            "paths": 1,
            "urls": 2,
            "registry": 0,
            "MZ": 1,
        },
        "general": {
            "size": size,
            "vsize": size * 2,
            "has_debug": 1,
            "exports": len(exports),
            "imports": sum(len(values) for values in imports.values()),
            "has_relocations": 0,
            "has_resources": 1,
            "has_signature": 0,
            "has_tls": 0,
            "symbols": 0,
        },
        "header": {
            "coff": {
                "timestamp": 1234567890,
                "machine": "I386",
                "characteristics": ["CHARA_32BIT_MACHINE", "EXECUTABLE_IMAGE"],
            },
            "optional": {
                "subsystem": "WINDOWS_GUI",
                "dll_characteristics": [],
                "magic": "PE32",
                **{field: index for index, field in enumerate(HEADER_OPTIONAL_FIELDS)},
            },
        },
        "section": {"entry": sections[0]["name"] if sections else "", "sections": sections},
        "imports": imports,
        "exports": exports,
        "datadirectories": datadirectories,
    }
    return record


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=False) + "\n")


def write_ember_source(
    root: Path,
    *,
    train_files: list[list[dict]],
    test_records: list[dict],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for index, records in enumerate(train_files):
        write_jsonl(root / f"train_features_{index}.jsonl", records)
    write_jsonl(root / "test_features.jsonl", test_records)
    return root


CICIDS_COLUMNS = (
    " Destination Port",
    " Flow Duration",
    " Fwd Header Length",
    " Fwd Header Length.1",
    " Flow Bytes/s",
    " Label",
)


def cicids_rows(
    count_benign: int = 30, count_attack: int = 15, *, offset: int = 0
) -> list[list[object]]:
    rows: list[list[object]] = []
    for index in range(count_benign):
        rows.append(
            [
                1000 + offset + index,
                10 + offset + index,
                40 + offset + index,
                40 + offset + index,
                100.0 + offset + index,
                "BENIGN",
            ]
        )
    attack_labels = ["DDoS", "Web Attack \ufffd Brute Force", "PortScan"]
    for index in range(count_attack):
        rows.append(
            [
                2000 + offset + index,
                100 + offset + index,
                50 + offset + index,
                50 + offset + index,
                200.0 + offset + index,
                attack_labels[index % len(attack_labels)],
            ]
        )
    return rows


def write_cicids_source(
    root: Path,
    *,
    files: dict[str, list[list[object]]],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, rows in files.items():
        with open(root / name, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(CICIDS_COLUMNS)
            writer.writerows(rows)
    return root


def standard_cicids_source(root: Path) -> Path:
    """Two files with benign/attack rows, one within-file and one cross-file duplicate."""
    monday = cicids_rows()
    tuesday = cicids_rows(count_benign=10, count_attack=5, offset=10_000)
    duplicate = list(monday[0])
    monday.append(duplicate)
    tuesday.append(list(monday[1]))
    return write_cicids_source(
        root,
        files={
            "Monday-WorkingHours.pcap_ISCX.csv": monday,
            "Tuesday-WorkingHours.pcap_ISCX.csv": tuesday,
        },
    )
