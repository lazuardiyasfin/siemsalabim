import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileState:
    offset: int = 0
    inode: int = 0


class StateManager:
    def __init__(self, state_file_path: Path) -> None:
        self._path = state_file_path
        self._states: dict[str, FileState] = {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        if not self._path.exists():
            logger.info("No existing state file at %s, starting fresh.", self._path)
            return

        try:
            raw = self._path.read_text(encoding="utf-8")
            data: dict[str, dict[str, int]] = json.loads(raw)
            for file_path, values in data.items():
                self._states[file_path] = FileState(
                    offset=values.get("offset", 0),
                    inode=values.get("inode", 0),
                )
            logger.info(
                "Loaded state for %d file(s) from %s.",
                len(self._states),
                self._path,
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("Corrupt state file %s, starting fresh: %s", self._path, exc)
            self._states.clear()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")
        data = {
            fp: {"offset": s.offset, "inode": s.inode} for fp, s in self._states.items()
        }
        tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_path.replace(self._path)
        logger.debug("State saved to %s.", self._path)

    # Offset management

    def get_offset(self, file_path: str) -> int:
        current_inode = self._get_inode(file_path)
        state = self._states.get(file_path)

        if state is None:
            self._states[file_path] = FileState(offset=0, inode=current_inode)
            return 0

        if current_inode != 0 and current_inode != state.inode:
            logger.info(
                "Rotation detected for %s (inode %d → %d), resetting offset.",
                file_path,
                state.inode,
                current_inode,
            )
            state.offset = 0
            state.inode = current_inode

        return state.offset

    def set_offset(self, file_path: str, offset: int) -> None:
        state = self._states.get(file_path)
        if state is None:
            self._states[file_path] = FileState(
                offset=offset, inode=self._get_inode(file_path)
            )
        else:
            state.offset = offset

    # Internals

    @staticmethod
    def _get_inode(file_path: str) -> int:
        try:
            return os.stat(file_path).st_ino
        except OSError:
            return 0
