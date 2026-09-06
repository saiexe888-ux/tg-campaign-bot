import asyncio
import logging
import threading

from telegram import Update


logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Runs the async Telegram Application inside a background thread,
    so Flask (sync) can feed updates into it.
    """

    def __init__(self, application):
        self.application = application
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.ready = threading.Event()
        self.error = None

        self.thread.start()

        if not self.ready.wait(timeout=60):
            raise RuntimeError("Bot startup timed out")

        if self.error:
            raise self.error

    async def _startup(self):
        await self.application.initialize()
        await self.application.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._startup())
        except Exception as exc:
            logger.exception("Webhook bot failed to start")
            self.error = exc
            self.ready.set()
            return

        self.ready.set()
        self.loop.run_forever()

    def enqueue(self, update_dict: dict) -> None:
        """
        Put a Telegram webhook update into the bot's update queue.
        """
        if self.error:
            raise self.error

        update = Update.de_json(update_dict, self.application.bot)

        if update is None:
            return

        async def _put_update():
            if getattr(self.application, "update_queue", None) is not None:
                await self.application.update_queue.put(update)
            else:
                await self.application.process_update(update)

        future = asyncio.run_coroutine_threadsafe(_put_update(), self.loop)
        future.result(timeout=15)
