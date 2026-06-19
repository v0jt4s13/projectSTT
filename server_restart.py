import os
import sys
import time
import resource
import logging
import threading

logger = logging.getLogger(__name__)


def _close_inherited_fds() -> None:
    """Close all file descriptors except stdin/stdout/stderr before exec.

    os.execv inherits open FDs, including Flask's listening socket.
    Closing them here lets the new process bind to the same port cleanly.
    """
    try:
        soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        os.closerange(3, soft)
    except Exception as exc:
        logger.warning("[server_restart] closerange nie powiodło się: %s", exc)


def restart_server(delay: float = 1.5) -> None:
    """Replace the current process with a fresh instance after `delay` seconds."""
    def _worker():
        time.sleep(delay)
        try:
            args = list(sys.argv)
            if '--no-local-models' not in args:
                args.append('--no-local-models')
            logger.warning(
                "[server_restart] Wykonuję os.execv: %s %s",
                sys.executable, args,
            )
            _close_inherited_fds()
            os.execv(sys.executable, [sys.executable] + args)
        except Exception as exc:
            logger.error("[server_restart] os.execv nie powiodło się: %s", exc)

    threading.Thread(target=_worker, daemon=True).start()
