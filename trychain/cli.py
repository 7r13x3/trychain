"""
TryChain — CLI entry point
"""
import argparse
import asyncio
import sys

from .config import load
from .core.server import TryChainServer
from . import logger
from . import __version__


def cmd_start(args):
    cfg = load(args.config)
    server = TryChainServer(cfg)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.warn("Stopped by user")


def cmd_check(args):
    try:
        cfg = load(args.config)
    except Exception as e:
        logger.error(f"Config error: {e}")
        sys.exit(1)

    logger.success("Config OK")
    logger.info(f"Listen: {cfg.listen}:{cfg.port}")
    logger.info(f"Mode: {cfg.mode}  (min_hops={cfg.min_hops})")
    logger.chain_table(cfg.proxies)
    logger.features_table(cfg.security.as_dict())


def cmd_gui(args):
    try:
        from .gui.app import run
    except ImportError as e:
        logger.error(f"GUI unavailable: {e}")
        sys.exit(1)
    run()


def main():
    parser = argparse.ArgumentParser(
        prog="trychain",
        description="TryChain — proxy chaining tool",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="Start the local SOCKS5 server")
    p_start.add_argument("--config", "-c", required=True,
                         help="Path to config TOML")
    p_start.set_defaults(func=cmd_start)

    p_check = sub.add_parser("check", help="Validate config and exit")
    p_check.add_argument("--config", "-c", required=True)
    p_check.set_defaults(func=cmd_check)

    p_gui = sub.add_parser("gui", help="Launch the GUI")
    p_gui.set_defaults(func=cmd_gui)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
