import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from . import config
from . import database as db
from . import keyboards
from . import texts
from . import utils


logger = logging.getLogger(__name__)


async def _respond(update: Update, text: str, reply_markup=None) -> None:
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except Exception as exc:
            if "message is not modified" in str(exc).lower():
                return

            logger.exception("Failed to edit admin callback message")

            if update.effective_message:
                await update.effective_message.reply_html(
                    text,
                    reply_markup=reply_markup,
                )
            return

    if update.effective_message:
        await update.effective_message.reply_html(
            text,
            reply_markup=reply_markup,
        )


async def _show_panel(update: Update) -> None:
    await _respond(
        update,
        texts.ADMIN_PANEL,
        keyboards.admin_panel_keyboard(),
    )


async def _show_pending(update: Update) -> None:
    pending = await asyncio.to_thread(db.list_pending_submissions, 20)

    if not pending:
        await _respond(
            update,
            texts.ADMIN_PENDING_EMPTY,
            keyboards.admin_back_keyboard(),
        )
        return

    await _respond(
        update,
        texts.ADMIN_PENDING_TITLE,
        keyboards.admin_pending_keyboard(pending),
    )


async def _show_campaigns(update: Update) -> None:
    campaigns = await asyncio.to_thread(db.get_campaigns_admin)

    await _respond(
        update,
        texts.ADMIN_CAMPAIGNS_TITLE,
        keyboards.admin_campaigns_keyboard(campaigns),
    )


async def _show_stats(update: Update) -> None:
    stats = await asyncio.to_thread(db.admin_stats)

    text = texts.ADMIN_STATS.format(
        users=stats["users"],
        active_campaigns=stats["active_campaigns"],
        pending=stats["pending"],
        approved=stats["approved"],
        rejected=stats["rejected"],
        payout=utils.format_money(stats["total_payout"]),
    )

    await _respond(update, text, keyboards.admin_back_keyboard())


async def _show_submission(update: Update, submission_id: str) -> None:
    submission = await asyncio.to_thread(db.get_submission, submission_id)

    if not submission:
        await _respond(update, texts.SUBMISSION_NOT_FOUND, keyboards.admin_back_keyboard())
        return

    username = submission.get("user_username") or "unknown"

    text = (
        f"🧾 <code>{submission['id']}</code>\n"
        f"Status: {submission['status']}\n"
        f"User ID: <code>{submission['user_id']}</code>\n"
        f"Username: @{utils.esc(username)}\n"
        f"Campaign: {utils.esc(submission['campaign_name'])}\n"
        f"Views: {submission['views']}\n"
        f"Payout: {utils.format_money(submission['payout'])}\n"
        f"Link: {submission['link']}\n"
    )

    if submission["admin_note"]:
        text += f"\nAdmin note: {utils.esc(submission['admin_note'])}\n"

    if submission["status"] == "pending":
        reply_markup = keyboards.admin_submission_keyboard(submission_id)
    else:
        reply_markup = keyboards.admin_back_pending_keyboard()

    await _respond(update, text, reply_markup)


async def _approve_submission(context: ContextTypes.DEFAULT_TYPE, submission_id: str):
    """
    Approve submission and notify user.
    """
    submission = await asyncio.to_thread(
        db.set_submission_status,
        submission_id,
        "approved",
        None,
    )

    if not submission:
        return None

    try:
        await context.bot.send_message(
            chat_id=submission["user_id"],
            text=texts.APPROVED_MSG.format(
                sub_id=submission["id"],
                campaign=utils.esc(submission["campaign_name"]),
            ),
            parse_mode="HTML",
        )
    except Exception:
        logger.info("Could not notify user %s about approval", submission["user_id"])

    return submission


async def _reject_submission(
    context: ContextTypes.DEFAULT_TYPE,
    submission_id: str,
    reason: str,
):
    """
    Reject submission and notify user.
    """
    submission = await asyncio.to_thread(
        db.set_submission_status,
        submission_id,
        "rejected",
        reason,
    )

    if not submission:
        return None

    try:
        await context.bot.send_message(
            chat_id=submission["user_id"],
            text=texts.REJECTED_MSG.format(
                sub_id=submission["id"],
                reason=utils.esc(reason),
            ),
            parse_mode="HTML",
        )
    except Exception:
        logger.info("Could not notify user %s about rejection", submission["user_id"])

    return submission


@utils.require_admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /admin command.
    """
    await _show_panel(update)# ------------------------------------------------------------------
# Admin callback router
# ------------------------------------------------------------------

@utils.require_admin
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle admin inline button presses.
    """
    query = update.callback_query
    if not query:
        return

    data = query.data or ""

    await query.answer()

    if data in {"admin_panel", "admin_main"}:
        await _show_panel(update)

    elif data == "admin_pending":
        await _show_pending(update)

    elif data == "admin_campaigns":
        await _show_campaigns(update)

    elif data == "admin_stats":
        await _show_stats(update)

    elif data == "admin_broadcast":
        context.user_data["waiting_for"] = "admin_broadcast"
        await _respond(
            update,
            texts.ADMIN_BROADCAST_PROMPT,
            keyboards.admin_back_keyboard(),
        )

    elif data == "admin_help":
        await _respond(
            update,
            texts.ADMIN_COMMANDS_HELP,
            keyboards.admin_back_keyboard(),
        )

    elif data.startswith("asub:"):
        submission_id = data.split(":", 1)[1]
        await _show_submission(update, submission_id)

    elif data.startswith("appr:"):
        submission_id = data.split(":", 1)[1]
        submission = await _approve_submission(context, submission_id)

        if submission:
            await _respond(
                update,
                f"✅ Approved <code>{submission_id}</code>",
                keyboards.admin_back_pending_keyboard(),
            )
        else:
            await _respond(
                update,
                texts.SUBMISSION_NOT_FOUND,
                keyboards.admin_back_pending_keyboard(),
            )

    elif data.startswith("rej:"):
        submission_id = data.split(":", 1)[1]

        context.user_data["waiting_for"] = "admin_reject_reason"
        context.user_data["reject_sub_id"] = submission_id

        await _respond(
            update,
            f"Send rejection reason for <code>{submission_id}</code>.\n\n"
            "Use /cancel to abort.",
            keyboards.admin_back_keyboard(),
        )

    elif data.startswith("togcamp:"):
        try:
            campaign_id = int(data.split(":", 1)[1])
        except (IndexError, ValueError):
            campaign_id = None

        if campaign_id is not None:
            await asyncio.to_thread(db.toggle_campaign, campaign_id)

        await _show_campaigns(update)

    else:
        await _show_panel(update)# ------------------------------------------------------------------
# Admin text flows
# ------------------------------------------------------------------

async def handle_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle admin rejection reason input.
    """
    user = update.effective_user
    message = update.effective_message

    if not user or user.id not in config.ADMIN_IDS:
        return

    if not message:
        return

    submission_id = context.user_data.pop("reject_sub_id", None)
    context.user_data.pop("waiting_for", None)

    if not submission_id:
        await message.reply_text("No active rejection flow.")
        return

    reason = (message.text or "").strip() or "Not accepted."

    submission = await _reject_submission(context, submission_id, reason)

    if submission:
        await message.reply_html(
            f"❌ Rejected <code>{submission_id}</code>",
            reply_markup=keyboards.admin_panel_keyboard(),
        )
    else:
        await message.reply_text(
            texts.SUBMISSION_NOT_FOUND,
            reply_markup=keyboards.admin_panel_keyboard(),
        )


async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle admin broadcast message input.
    """
    user = update.effective_user
    message = update.effective_message

    if not user or user.id not in config.ADMIN_IDS:
        return

    if not message:
        return

    text = (message.text or "").strip()

    context.user_data.pop("waiting_for", None)

    if not text:
        await message.reply_text("Broadcast message is empty.")
        return

    asyncio.create_task(_broadcast(context, text))

    await message.reply_html(
        texts.ADMIN_BROADCAST_STARTED,
        reply_markup=keyboards.admin_panel_keyboard(),
    )


async def _broadcast(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """
    Send message to all users (slow, to respect Telegram limits).
    """
    sent = 0
    failed = 0

    user_ids = await asyncio.to_thread(db.all_user_ids)

    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
            )
            sent += 1
        except Exception as exc:
            failed += 1
            logger.info("Broadcast failed for user %s: %s", user_id, exc)

        await asyncio.sleep(0.12)

    summary = texts.ADMIN_BROADCAST_DONE.format(sent=sent, failed=failed)

    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=summary)
        except Exception:
            pass


# ------------------------------------------------------------------
# Admin notification helpers
# ------------------------------------------------------------------

async def notify_admins_new_submission(context: ContextTypes.DEFAULT_TYPE, submission_id: str) -> None:
    """
    Notify admins when a user submits a link.
    """
    submission = await asyncio.to_thread(db.get_submission, submission_id)

    if not submission:
        return

    if submission.get("user_username"):
        user_label = f"@{submission['user_username']}"
    else:
        user_label = str(submission["user_id"])

    text = texts.NEW_SUBMISSION_ADMIN.format(
        sub_id=submission["id"],
        user=utils.esc(user_label),
        campaign=utils.esc(submission["campaign_name"]),
        link=submission["link"],
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception:
            logger.info("Could not notify admin %s", admin_id)


async def notify_admins_bulk_submission(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    campaign: dict,
    created: int,
) -> None:
    """
    Notify admins about bulk submission.
    """
    text = texts.NEW_BULK_SUBMISSION_ADMIN.format(
        user_id=user_id,
        campaign=utils.esc(campaign["name"]),
        created=created,
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception:
            logger.info("Could not notify admin %s", admin_id)# ------------------------------------------------------------------
# Admin commands
# ------------------------------------------------------------------

@utils.require_admin
async def newcampaign_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /newcampaign payout_per_view target_views Campaign Name
    """
    args = context.args or []

    if len(args) < 3:
        await update.effective_message.reply_text(
            "Usage: /newcampaign <payout_per_view> <target_views> <name>\n"
            "Example: /newcampaign 0.01 5000 September Reel Campaign"
        )
        return

    try:
        payout_per_view = float(args[0])
        target_views = int(args[1])
    except ValueError:
        await update.effective_message.reply_text(
            "payout_per_view must be a number and target_views must be an integer."
        )
        return

    name = " ".join(args[2:]).strip()

    if not name:
        await update.effective_message.reply_text("Campaign name is required.")
        return

    campaign_id = await asyncio.to_thread(
        db.create_campaign,
        name,
        payout_per_view,
        target_views,
        "",
        "",
    )

    await update.effective_message.reply_html(
        f"✅ Campaign created.\n\n"
        f"ID: <code>{campaign_id}</code>\n"
        f"Name: {utils.esc(name)}\n\n"
        f"Use:\n"
        f"<code>/setdesc {campaign_id} Description</code>\n"
        f"<code>/setrules {campaign_id} Rules</code>"
    )


@utils.require_admin
async def setdesc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if len(args) < 2:
        await update.effective_message.reply_text(
            "Usage: /setdesc <campaign_id> <description>"
        )
        return

    try:
        campaign_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("Campaign ID must be a number.")
        return

    description = " ".join(args[1:]).strip()

    ok = await asyncio.to_thread(db.set_campaign_description, campaign_id, description)

    if ok:
        await update.effective_message.reply_text("Campaign description updated.")
    else:
        await update.effective_message.reply_text("Campaign not found.")


@utils.require_admin
async def setrules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if len(args) < 2:
        await update.effective_message.reply_text(
            "Usage: /setrules <campaign_id> <rules>"
        )
        return

    try:
        campaign_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("Campaign ID must be a number.")
        return

    rules = " ".join(args[1:]).strip()

    ok = await asyncio.to_thread(db.set_campaign_rules, campaign_id, rules)

    if ok:
        await update.effective_message.reply_text("Campaign rules updated.")
    else:
        await update.effective_message.reply_text("Campaign not found.")


@utils.require_admin
async def togglecampaign_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if len(args) != 1:
        await update.effective_message.reply_text(
            "Usage: /togglecampaign <campaign_id>"
        )
        return

    try:
        campaign_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("Campaign ID must be a number.")
        return

    new_state = await asyncio.to_thread(db.toggle_campaign, campaign_id)

    if new_state is None:
        await update.effective_message.reply_text("Campaign not found.")
        return

    state_text = "enabled" if new_state else "disabled"
    await update.effective_message.reply_text(f"Campaign {campaign_id} is now {state_text}.")


@utils.require_admin
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if len(args) != 1:
        await update.effective_message.reply_text("Usage: /approve <submission_id>")
        return

    submission_id = args[0].strip()
    submission = await _approve_submission(context, submission_id)

    if submission:
        await update.effective_message.reply_html(f"✅ Approved <code>{submission_id}</code>")
    else:
        await update.effective_message.reply_text(texts.SUBMISSION_NOT_FOUND)


@utils.require_admin
async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if len(args) < 1:
        await update.effective_message.reply_text(
            "Usage: /reject <submission_id> [reason]"
        )
        return

    submission_id = args[0].strip()
    reason = " ".join(args[1:]).strip() or "Not accepted."

    submission = await _reject_submission(context, submission_id, reason)

    if submission:
        await update.effective_message.reply_html(f"❌ Rejected <code>{submission_id}</code>")
    else:
        await update.effective_message.reply_text(texts.SUBMISSION_NOT_FOUND)


@utils.require_admin
async def setviews_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if len(args) != 2:
        await update.effective_message.reply_text(
            "Usage: /setviews <submission_id> <views>"
        )
        return

    submission_id = args[0].strip()

    try:
        views = int(args[1])
    except ValueError:
        await update.effective_message.reply_text("Views must be an integer.")
        return

    submission = await asyncio.to_thread(db.update_submission_views, submission_id, views)

    if not submission:
        await update.effective_message.reply_text(texts.SUBMISSION_NOT_FOUND)
        return

    if submission["status"] == "approved":
        try:
            await context.bot.send_message(
                chat_id=submission["user_id"],
                text=texts.VIEWS_UPDATED_MSG.format(
                    sub_id=submission["id"],
                    views=submission["views"],
                    payout=utils.format_money(submission["payout"]),
                ),
                parse_mode="HTML",
            )
        except Exception:
            logger.info("Could not notify user %s about view update", submission["user_id"])

        await update.effective_message.reply_html(
            f"Updated <code>{submission_id}</code>.\n"
            f"Views: {submission['views']}\n"
            f"Payout: {utils.format_money(submission['payout'])}"
        )
    else:
        await update.effective_message.reply_html(
            f"Updated views for <code>{submission_id}</code>, "
            "but payout is calculated only for approved submissions."
        )


@utils.require_admin
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if not args:
        context.user_data["waiting_for"] = "admin_broadcast"
        await update.effective_message.reply_html(
            texts.ADMIN_BROADCAST_PROMPT,
            reply_markup=keyboards.admin_back_keyboard(),
        )
        return

    text = " ".join(args).strip()

    asyncio.create_task(_broadcast(context, text))

    await update.effective_message.reply_text(texts.ADMIN_BROADCAST_STARTED)
