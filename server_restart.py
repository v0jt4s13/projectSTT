import os
import sys
import time
import logging
import threading

logger = logging.getLogger(__name__)


def restart_server(delay: float = 1.5) -> None:
    """Replace the current process with a fresh instance after `delay` seconds.

    Werkzeug passes its listening socket to the child via --fd / WERKZEUG_SERVER_FD,
    so FDs must NOT be closed before execv — the new process inherits and reuses them.
    """
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
            os.execv(sys.executable, [sys.executable] + args)
        except Exception as exc:
            logger.error("[server_restart] os.execv nie powiodło się: %s", exc)

    threading.Thread(target=_worker, daemon=True).start()
