from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from . import admin
from . import config
from . import database as db
from . import handlers


def create_application() -> Application:
    """
    Create the Telegram bot application and register all handlers.
    """
    config.require_config()

    # Make sure database tables exist.
    db.init_db()

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .build()
    )

    # User commands
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_cmd))
    application.add_handler(CommandHandler("cancel", handlers.cancel))
    application.add_handler(CommandHandler("campaigns", handlers.campaigns_cmd))
    application.add_handler(CommandHandler("instagram", handlers.instagram_cmd))
    application.add_handler(CommandHandler("history", handlers.history_cmd))
    application.add_handler(CommandHandler("earnings", handlers.earnings_cmd))

    # Admin commands
    application.add_handler(CommandHandler("admin", admin.admin_command))
    application.add_handler(CommandHandler("newcampaign", admin.newcampaign_command))
    application.add_handler(CommandHandler("setdesc", admin.setdesc_command))
    application.add_handler(CommandHandler("setrules", admin.setrules_command))
    application.add_handler(CommandHandler("togglecampaign", admin.togglecampaign_command))
    application.add_handler(CommandHandler("approve", admin.approve_command))
    application.add_handler(CommandHandler("reject", admin.reject_command))
    application.add_handler(CommandHandler("setviews", admin.setviews_command))
    application.add_handler(CommandHandler("broadcast", admin.broadcast_command))

    # Inline button callbacks
    application.add_handler(CallbackQueryHandler(handlers.on_callback))

    # Text input flows
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text)
    )

    # Global error handler
    application.add_error_handler(handlers.error_handler)

    return application
