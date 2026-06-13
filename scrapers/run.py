"""
Run all scrapers and log results.
Usage: python run.py [--bbts] [--amiami]
If no flags given, runs both.
"""

import argparse
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("runner")


def main():
    parser = argparse.ArgumentParser(description="Run action figure price scrapers")
    parser.add_argument("--bbts", action="store_true", help="Run BBTS scraper only")
    parser.add_argument("--amiami", action="store_true", help="Run AmiAmi scraper only")
    args = parser.parse_args()

    run_all = not args.bbts and not args.amiami

    start = time.time()
    total = 0

    if run_all or args.amiami:
        log.info("=== Starting AmiAmi scraper ===")
        import amiami
        count = amiami.run()
        log.info("AmiAmi: saved %d listings", count)
        total += count

    if run_all or args.bbts:
        log.info("=== Starting BBTS scraper ===")
        import bbts
        count = bbts.run()
        log.info("BBTS: saved %d listings", count)
        total += count

    elapsed = time.time() - start
    log.info("Done. Total listings saved: %d in %.1fs", total, elapsed)


if __name__ == "__main__":
    main()
