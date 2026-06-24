class PostGameserverMixin:
    def _handle_post_gameserver(self):
        if self.path == "/v1/gameserver/start":
            from api.routes.handlers.gameserver_handler import handle_gameserver_start

            handle_gameserver_start(self)
            return True

        # /v1/gameserver/stop
        if self.path == "/v1/gameserver/stop":
            from api.routes.handlers.gameserver_handler import handle_gameserver_stop

            handle_gameserver_stop(self)
            return True

        # /v1/gameserver/restart
        if self.path == "/v1/gameserver/restart":
            from api.routes.handlers.gameserver_handler import handle_gameserver_restart

            handle_gameserver_restart(self)
            return True

        # /v1/gameserver/command
        if self.path == "/v1/gameserver/command":
            from api.routes.handlers.gameserver_handler import handle_gameserver_command

            handle_gameserver_command(self)
            return True

        if self.path == "/v1/gameserver/register":
            from api.routes.handlers.gameserver_handler import (
                handle_gameserver_register,
            )

            handle_gameserver_register(self)
            return True

        if self.path == "/v1/gameserver/expose":
            from api.routes.handlers.gameserver_handler import handle_gameserver_expose

            handle_gameserver_expose(self)
            return True

        # ── Journalist Autonomous OSINT ─────────────────────────────────────────────
        if self.path == "/v1/gameserver/backup":
            from api.routes.handlers.gameserver_handler import handle_gameserver_backup

            handle_gameserver_backup(self)
            return True

        # /v1/sessions/spawn — Crea un nuevo subproceso ask_deepseek.py --session <id>
        return False
