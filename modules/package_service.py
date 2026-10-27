"""PubCast application-level packaging for portable, verifiable conversation exports.

Exports are staged outside the destination and published only after manifest/hash
verification succeeds. A failed export therefore never masquerades as a complete one.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .conversation_archive import ConversationArchive, sha256_file


class PackageVerificationError(IOError):
    """Raised when a package fails its post-write integrity verification."""


class PackageService:
    MANIFEST_SCHEMA = "pubcast.conversation.package.v2"
    LIBRARY_SCHEMA = "pubcast.conversation.library.v1"

    def __init__(self, archive: ConversationArchive):
        self.archive = archive

    @staticmethod
    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        for number in range(2, 10000):
            candidate = path.with_name(f"{path.stem}_{number}{path.suffix}")
            if not candidate.exists():
                return candidate
        raise FileExistsError(f"unable to find collision-free name for {path}")

    @staticmethod
    def _stamp() -> str:
        return datetime.now().astimezone().strftime("%m-%d-%Y_%H-%M-%S")

    @staticmethod
    def _publish_tree(staged: Path, final: Path) -> None:
        """Publish a verified directory with one same-filesystem rename."""
        final.parent.mkdir(parents=True, exist_ok=True)
        pending = final.parent / f".{final.name}.pending-{uuid.uuid4().hex}"
        try:
            shutil.copytree(staged, pending)
            os.rename(pending, final)
        except Exception:
            shutil.rmtree(pending, ignore_errors=True)
            raise

    @staticmethod
    def _publish_file(staged: Path, final: Path) -> None:
        """Publish a verified file without exposing a partially copied final path."""
        final.parent.mkdir(parents=True, exist_ok=True)
        pending = final.parent / f".{final.name}.pending-{uuid.uuid4().hex}"
        try:
            shutil.copy2(staged, pending)
            os.rename(pending, final)
        except Exception:
            pending.unlink(missing_ok=True)
            raise

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _file_inventory(root: Path, *, exclude: set[str] | None = None) -> list[dict[str, Any]]:
        excluded = exclude or set()
        inventory: list[dict[str, Any]] = []
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            relative = path.relative_to(root).as_posix()
            if relative in excluded:
                continue
            inventory.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
        return inventory

    @staticmethod
    def _verify_inventory(root: Path, inventory: Iterable[dict[str, Any]]) -> None:
        root = root.resolve()
        for item in inventory:
            candidate = (root / item["path"]).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise PackageVerificationError(f"manifest path escapes package root: {item['path']}") from exc
            if not candidate.is_file():
                raise PackageVerificationError(f"manifest file missing: {item['path']}")
            if candidate.stat().st_size != item["bytes"]:
                raise PackageVerificationError(f"size mismatch: {item['path']}")
            if sha256_file(candidate) != item["sha256"]:
                raise PackageVerificationError(f"checksum mismatch: {item['path']}")

    def _materialize_conversation(self, conversation_id: str, root: Path) -> dict[str, Any]:
        conversation = self.archive.get_conversation(conversation_id)
        transcript_dir = root / "Transcript"
        transcript_dir.mkdir(parents=True, exist_ok=False)
        self.archive.export_documents(conversation_id, transcript_dir)
        inventory = self._file_inventory(root)
        for item in inventory:
            suffix = Path(item["path"]).suffix.lower().lstrip(".")
            if suffix in {"txt", "md", "json", "jsonl", "html"}:
                item["kind"] = suffix
        manifest = {
            "schema": self.MANIFEST_SCHEMA,
            "conversation_id": conversation_id,
            "title": conversation["title"],
            "discussion_type": conversation.get("discussion_type", "chat"),
            "project_id": conversation.get("project_id"),
            "build_id": conversation.get("build_id"),
            "created_at": conversation["created_at"],
            "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "files": inventory,
        }
        self._write_json(root / "manifest.json", manifest)
        checksummed = inventory + [{
            "path": "manifest.json",
            "bytes": (root / "manifest.json").stat().st_size,
            "sha256": sha256_file(root / "manifest.json"),
        }]
        (root / "SHA256SUMS.txt").write_text(
            "".join(f"{item['sha256']}  {item['path']}\n" for item in checksummed), encoding="utf-8"
        )
        self._verify_inventory(root, checksummed)
        return manifest

    def save_conversation_raw(self, conversation_id: str, destination: Path | str) -> dict[str, Any]:
        destination = Path(destination)
        conversation = self.archive.get_conversation(conversation_id)
        safe_title = self.archive._safe_stem(conversation["title"])
        parent = destination / "Chats"
        parent.mkdir(parents=True, exist_ok=True)
        final = self._unique_path(parent / f"PubCast_Chat_{safe_title}_{self._stamp()}")
        with tempfile.TemporaryDirectory(prefix="pubcast-stage-") as temp:
            staged = Path(temp) / "package"
            staged.mkdir()
            manifest = self._materialize_conversation(conversation_id, staged)
            self._publish_tree(staged, final)
        return {
            "root": final,
            "manifest": final / "manifest.json",
            "checksums": final / "SHA256SUMS.txt",
            "files": {p.suffix.lstrip("."): p for p in (final / "Transcript").iterdir() if p.is_file()},
            "manifest_data": manifest,
        }

    def save_conversation_zip(self, conversation_id: str, destination: Path | str) -> dict[str, Any]:
        destination = Path(destination)
        archives = destination / "Archives"
        archives.mkdir(parents=True, exist_ok=True)
        conversation = self.archive.get_conversation(conversation_id)
        safe_title = self.archive._safe_stem(conversation["title"])
        final = self._unique_path(archives / f"PubCast_Chat_{safe_title}_{self._stamp()}.zip")
        with tempfile.TemporaryDirectory(prefix="pubcast-package-") as temp:
            stage_root = Path(temp) / "raw"
            stage_root.mkdir()
            self._materialize_conversation(conversation_id, stage_root)
            staged_zip = Path(temp) / "package.zip"
            self._write_zip(stage_root, staged_zip)
            self._verify_zip(staged_zip)
            self._publish_file(staged_zip, final)
        self._verify_zip(final)
        return {"zip": final, "sha256": sha256_file(final), "members": self._zip_names(final), "verified": True}

    def save_library_raw(
        self, conversation_ids: Iterable[str], destination: Path | str, *, owner_id: str,
        extra_files: Mapping[str, bytes] | None = None,
    ) -> dict[str, Any]:
        """Export an owner-filtered conversation library as ordinary files/folders."""
        ids = list(dict.fromkeys(conversation_ids))
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        final = self._unique_path(destination / f"PubCast_Conversation_Library_{self._stamp()}")

        with tempfile.TemporaryDirectory(prefix="pubcast-library-stage-") as temp:
            staged = Path(temp) / "library"
            chats = staged / "Chats"
            chats.mkdir(parents=True)
            entries: list[dict[str, Any]] = []
            for index, conversation_id in enumerate(ids, start=1):
                conversation = self.archive.get_conversation(conversation_id)
                if conversation.get("metadata", {}).get("owner") != owner_id:
                    raise PermissionError(f"conversation is not owned by exporter: {conversation_id}")
                safe_title = self.archive._safe_stem(conversation["title"])
                folder_name = f"{index:04d}_{safe_title}_{conversation_id}"
                conversation_root = chats / folder_name
                conversation_root.mkdir()
                child_manifest = self._materialize_conversation(conversation_id, conversation_root)
                entries.append({
                    "conversation_id": conversation_id,
                    "title": conversation["title"],
                    "path": f"Chats/{folder_name}",
                    "manifest_sha256": sha256_file(conversation_root / "manifest.json"),
                    "message_count": len(conversation["messages"]),
                    "discussion_type": conversation.get("discussion_type", "chat"),
                    "project_id": conversation.get("project_id"),
                    "build_id": conversation.get("build_id"),
                    "schema": child_manifest["schema"],
                })

            for relative, contents in (extra_files or {}).items():
                # No caller-controlled paths may escape the staged package.
                if relative != 'PrivateCharacters/transcripts.json' or not isinstance(contents, bytes):
                    raise ValueError('Unapproved export attachment')
                attachment = staged / relative
                attachment.parent.mkdir(parents=True, exist_ok=True)
                attachment.write_bytes(contents)

            inventory = self._file_inventory(staged, exclude={"library_manifest.json", "SHA256SUMS.txt"})
            manifest = {
                "schema": self.LIBRARY_SCHEMA,
                "owner_id": owner_id,
                "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "conversation_count": len(entries),
                "conversations": entries,
                "files": inventory,
            }
            self._write_json(staged / "library_manifest.json", manifest)
            manifest_item = {
                "path": "library_manifest.json",
                "bytes": (staged / "library_manifest.json").stat().st_size,
                "sha256": sha256_file(staged / "library_manifest.json"),
            }
            verified = inventory + [manifest_item]
            (staged / "SHA256SUMS.txt").write_text(
                "".join(f"{item['sha256']}  {item['path']}\n" for item in verified), encoding="utf-8"
            )
            self._verify_inventory(staged, verified)
            self._publish_tree(staged, final)

        return {
            "root": final,
            "manifest": final / "library_manifest.json",
            "checksums": final / "SHA256SUMS.txt",
            "conversation_count": len(entries),
            "verified": True,
        }

    def save_library_zip(
        self, conversation_ids: Iterable[str], destination: Path | str, *, owner_id: str,
        extra_files: Mapping[str, bytes] | None = None,
    ) -> dict[str, Any]:
        destination = Path(destination)
        archives = destination / "Archives"
        archives.mkdir(parents=True, exist_ok=True)
        final = self._unique_path(archives / f"PubCast_Conversation_Library_{self._stamp()}.zip")
        with tempfile.TemporaryDirectory(prefix="pubcast-library-zip-") as temp:
            raw = self.save_library_raw(conversation_ids, Path(temp), owner_id=owner_id,
                                        extra_files=extra_files)
            staged_zip = Path(temp) / "library.zip"
            self._write_zip(raw["root"], staged_zip)
            self._verify_zip(staged_zip)
            self._publish_file(staged_zip, final)
        self._verify_zip(final)
        return {"zip": final, "sha256": sha256_file(final), "members": self._zip_names(final), "verified": True}

    @staticmethod
    def _write_zip(root: Path, path: Path) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
            for file_path in sorted(p for p in root.rglob("*") if p.is_file()):
                package.write(file_path, file_path.relative_to(root).as_posix())

    @staticmethod
    def _zip_names(path: Path) -> list[str]:
        with zipfile.ZipFile(path, "r") as package:
            return package.namelist()

    @staticmethod
    def _verify_zip(path: Path) -> None:
        with zipfile.ZipFile(path, "r") as package:
            bad_member = package.testzip()
            names = package.namelist()
            if len(names) != len(set(names)):
                raise PackageVerificationError("ZIP contains duplicate member names")
            for info in package.infolist():
                member = Path(info.filename)
                if member.is_absolute() or ".." in member.parts:
                    raise PackageVerificationError(f"unsafe ZIP member: {info.filename}")
        if bad_member is not None:
            raise PackageVerificationError(f"ZIP integrity verification failed at {bad_member}")


__all__ = ["PackageService", "PackageVerificationError"]
