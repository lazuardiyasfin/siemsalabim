import asyncio
import logging
import sys

from .config import ExporterConfig
from .pipeline import Pipeline


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    config = ExporterConfig()
    _setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info(
        "Starting exporter '%s', watching: %s",
        config.exporter_id,
        config.watch_paths_list,
    )

    pipeline = Pipeline(config)

    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        logger.info("Exporter interrupted by user.")


if __name__ == "__main__":
    main()
