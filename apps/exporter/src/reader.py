import logging

from .state import StateManager

logger = logging.getLogger(__name__)


def read_new_lines(file_path: str, state: StateManager) -> list[str]:
    offset = state.get_offset(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, 2)  # seek to end
            file_size = fh.tell()

            if file_size < offset:
                logger.info(
                    "File %s truncated (%d < %d), resetting offset.",
                    file_path,
                    file_size,
                    offset,
                )
                offset = 0

            fh.seek(offset)
            data = fh.read()

            if not data:
                return []

            if data.endswith("\n"):
                new_offset = offset + len(data.encode("utf-8"))
                lines = [ln for ln in data.splitlines() if ln.strip()]
            else:
                last_newline = data.rfind("\n")
                if last_newline == -1:
                    return []
                complete = data[: last_newline + 1]
                new_offset = offset + len(complete.encode("utf-8"))
                lines = [ln for ln in complete.splitlines() if ln.strip()]

            state.set_offset(file_path, new_offset)
            logger.debug(
                "Read %d line(s) from %s (offset %d → %d).",
                len(lines),
                file_path,
                offset,
                new_offset,
            )
            return lines

    except FileNotFoundError:
        logger.warning("File not found: %s", file_path)
        return []
    except PermissionError:
        logger.warning("Permission denied: %s", file_path)
        return []
