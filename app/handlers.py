import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from . import admin as admin_module
from . import config
from . import database as db
from . import keyboards
from . import texts
from . import utils


logger = logging.getLogger(__name__)


async def _save_user(update: Update) -> None:
    user = update.effective_user
    if not user:
        return

    await asyncio.to_thread(
        db.upsert_user,
        user.id,
        user.username,
        user.first_name,
        user.last_name,
    )


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

            logger.exception("Failed to edit callback message")

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


def _clear_waiting(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in (
        "waiting_for",
        "single_campaign_id",
        "bulk_campaign_id",
        "reject_sub_id",
    ):
        context.user_data.pop(key, None)


def _int_from_data(data: str):
    try:
        return int(data.split(":", 1)[1])
    except (IndexError, ValueError):
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save_user(update)

    user = update.effective_user
    name = user.first_name or user.username or "there"

    await update.message.reply_html(
        texts.WELCOME.format(name=utils.esc(name)),
        reply_markup=keyboards.main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save_user(update)
    await show_help(update)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_waiting(context)

    if update.effective_message:
        await update.effective_message.reply_html(
            "Action cancelled.",
            reply_markup=keyboards.main_menu(),
        )


async def campaigns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save_user(update)
    await show_campaigns(update)


async def instagram_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save_user(update)
    await show_instagram(update)


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save_user(update)
    await show_history(update)


async def earnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save_user(update)
    await show_earnings(update)


async def show_main_menu(update: Update) -> None:
    user = update.effective_user
    name = (user.first_name or user.username or "there") if user else "there"

    await _respond(
        update,
        texts.WELCOME.format(name=utils.esc(name)),
        keyboards.main_menu(),
    )


async def show_help(update: Update) -> None:
    text = texts.HELP.format(support=utils.esc(config.SUPPORT_USERNAME))
    await _respond(update, text, keyboards.back_main())


async def show_campaigns(update: Update) -> None:
    campaigns = await asyncio.to_thread(db.get_active_campaigns)

    if not campaigns:
        await _respond(update, texts.NO_CAMPAIGNS, keyboards.back_main())
        return

    await _respond(
        update,
        texts.CAMPAIGNS_TITLE,
        keyboards.campaigns_keyboard(campaigns),
    )


async def show_submit_campaigns(update: Update, bulk: bool) -> None:
    campaigns = await asyncio.to_thread(db.get_active_campaigns)

    if not campaigns:
        await _respond(update, texts.NO_CAMPAIGNS, keyboards.back_main())
        return

    await _respond(
        update,
        texts.CHOOSE_CAMPAIGN,
        keyboards.submit_campaigns_keyboard(campaigns, bulk=bulk),
    )


async def show_rules_list(update: Update) -> None:
    campaigns = await asyncio.to_thread(db.get_active_campaigns)

    if not campaigns:
        await _respond(update, texts.NO_CAMPAIGNS, keyboards.back_main())
        return

    await _respond(
        update,
        texts.CHOOSE_CAMPAIGN,
        keyboards.rules_keyboard(campaigns),
    )


async def show_campaign_detail(update: Update, campaign_id: int) -> None:
    campaign = await asyncio.to_thread(db.get_campaign, campaign_id)

    if not campaign or not campaign["active"]:
        await _respond(update, texts.CAMPAIGN_UNAVAILABLE, keyboards.back_main())
        return

    description = campaign["description"] or "No description."
    target = "Unlimited" if not campaign["target_views"] else str(campaign["target_views"])
    status = "Active" if campaign["active"] else "Inactive"

    text = texts.CAMPAIGN_DETAILS.format(
        name=utils.esc(campaign["name"]),
        description=utils.esc(description),
        payout=utils.format_money(campaign["payout_per_view"]),
        target=utils.esc(target),
        status=utils.esc(status),
    )

    await _respond(
        update,
        text,
        keyboards.campaign_detail_keyboard(campaign),
    )


async def show_campaign_rules(update: Update, campaign_id: int) -> None:
    campaign = await asyncio.to_thread(db.get_campaign, campaign_id)

    if not campaign:
        await _respond(update, texts.CAMPAIGN_UNAVAILABLE, keyboards.back_main())
        return

    rules = campaign["rules"] or texts.DEFAULT_RULES

    text = texts.CAMPAIGN_RULES.format(
        name=utils.esc(campaign["name"]),
        rules=utils.esc(rules),
    )

    await _respond(update, text, keyboards.back_main())


async def show_instagram(update: Update) -> None:
    user = update.effective_user
    if not user:
        return

    accounts = await asyncio.to_thread(db.list_instagram, user.id)

    if not accounts:
        text = texts.NO_INSTAGRAM
    else:
        lines = [f"• @{utils.esc(account['username'])}" for account in accounts]
        text = texts.INSTAGRAM_TITLE + "\n" + "\n".join(lines)

    await _respond(
        update,
        text,
        keyboards.instagram_keyboard(accounts),
    )


async def show_history(update: Update) -> None:
    user = update.effective_user
    if not user:
        return

    submissions = await asyncio.to_thread(db.list_user_submissions, user.id, 10)

    if not submissions:
        await _respond(update, texts.NO_HISTORY, keyboards.history_keyboard())
        return

    lines = []

    for submission in submissions:
        lines.append(
            f"{utils.status_emoji(submission['status'])} <code>{submission['id']}</code> "
            f"• {utils.esc(submission['campaign_name'])}\n"
            f"   Status: {submission['status']} | "
            f"Views: {submission['views']} | "
            f"Payout: {utils.format_money(submission['payout'])}"
        )

    text = texts.HISTORY_TITLE + "\n\n" + "\n".join(lines)

    await _respond(update, text, keyboards.history_keyboard())


async def show_earnings(update: Update) -> None:
    user = update.effective_user
    if not user:
        return

    earnings = await asyncio.to_thread(db.user_earnings, user.id)

    text = texts.EARNINGS.format(
        total=earnings["total"],
        pending=earnings["pending"],
        approved=earnings["approved"],
        rejected=earnings["rejected"],
        views=earnings["views"],
        payout=utils.format_money(earnings["payout"]),
    )

    await _respond(update, text, keyboards.back_main())


async def show_submission(update: Update, submission_id: str) -> None:
    user = update.effective_user
    if not user:
        return

    submission = await asyncio.to_thread(db.get_submission, submission_id)

    if not submission:
        await _respond(update, texts.SUBMISSION_NOT_FOUND, keyboards.back_main())
        return

    if submission["user_id"] != user.id and user.id not in config.ADMIN_IDS:
        await _respond(update, texts.SUBMISSION_NOT_FOUND, keyboards.back_main())
        return

    text = (
        f"🧾 <code>{submission['id']}</code>\n"
        f"Campaign: {utils.esc(submission['campaign_name'])}\n"
        f"Status: {submission['status']}\n"
        f"Views: {submission['views']}\n"
        f"Payout: {utils.format_money(submission['payout'])}\n"
        f"Link: {submission['link']}\n"
    )

    if submission["admin_note"]:
        text += f"\nAdmin note: {utils.esc(submission['admin_note'])}\n"

    await _respond(update, text, keyboards.submission_keyboard())# ------------------------------------------------------------------
# Input flows
# ------------------------------------------------------------------

async def start_add_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["waiting_for"] = "instagram_username"
    await _respond(update, texts.ASK_INSTAGRAM_USERNAME, keyboards.back_main())


async def start_submission(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    campaign_id: int,
    bulk: bool,
) -> None:
    user = update.effective_user
    if not user:
        return

    campaign = await asyncio.to_thread(db.get_campaign, campaign_id)

    if not campaign or not campaign["active"]:
        await _respond(update, texts.CAMPAIGN_UNAVAILABLE, keyboards.back_main())
        return

    has_instagram = await asyncio.to_thread(db.has_instagram_account, user.id)

    if not has_instagram:
        context.user_data["waiting_for"] = "instagram_username"
        await _respond(
            update,
            texts.ADD_INSTAGRAM_FIRST,
            keyboards.instagram_keyboard([]),
        )
        return

    if bulk:
        context.user_data["waiting_for"] = "bulk_links"
        context.user_data["bulk_campaign_id"] = campaign_id

        text = texts.ASK_BULK_LINKS.format(
            campaign=utils.esc(campaign["name"])
        )
    else:
        context.user_data["waiting_for"] = "single_link"
        context.user_data["single_campaign_id"] = campaign_id

        text = texts.ASK_SINGLE_LINK.format(
            campaign=utils.esc(campaign["name"])
        )

    await _respond(update, text, keyboards.back_main())


async def handle_add_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    username = utils.clean_instagram_username(message.text or "")

    if not username:
        await message.reply_html(
            "Invalid Instagram username.\n\nExample: <code>myusername</code>",
            reply_markup=keyboards.back_main(),
        )
        return

    added = await asyncio.to_thread(db.add_instagram, user.id, username)

    _clear_waiting(context)

    if added:
        await message.reply_html(f"✅ Instagram account @{utils.esc(username)} added.")
    else:
        await message.reply_html("This Instagram account is already saved.")

    await show_instagram(update)


async def handle_single_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    campaign_id = context.user_data.get("single_campaign_id")

    if not campaign_id:
        _clear_waiting(context)
        await message.reply_text(texts.SESSION_EXPIRED)
        return

    campaign = await asyncio.to_thread(db.get_campaign, campaign_id)

    if not campaign or not campaign["active"]:
        _clear_waiting(context)
        await message.reply_text(texts.CAMPAIGN_UNAVAILABLE)
        return

    has_instagram = await asyncio.to_thread(db.has_instagram_account, user.id)

    if not has_instagram:
        context.user_data["waiting_for"] = "instagram_username"
        await message.reply_html(
            texts.ADD_INSTAGRAM_FIRST,
            reply_markup=keyboards.instagram_keyboard([]),
        )
        return

    raw = message.text or ""
    link = utils.normalize_link(raw)

    if not utils.is_instagram_link(raw):
        await message.reply_html(
            texts.INVALID_LINK,
            reply_markup=keyboards.back_main(),
        )
        return

    result = await asyncio.to_thread(
        db.create_submission,
        user.id,
        campaign_id,
        link,
    )

    _clear_waiting(context)

    if result["duplicate"]:
        text = texts.SUBMISSION_DUPLICATE.format(
            sub_id=result["id"],
            status=result["status"],
        )
    else:
        text = texts.SUBMISSION_CREATED.format(
            sub_id=result["id"],
            campaign=utils.esc(campaign["name"]),
        )

        try:
            await admin_module.notify_admins_new_submission(context, result["id"])
        except Exception:
            logger.exception("Failed to notify admins about new submission")

    await message.reply_html(text, reply_markup=keyboards.back_main())


async def handle_bulk_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    campaign_id = context.user_data.get("bulk_campaign_id")

    if not campaign_id:
        _clear_waiting(context)
        await message.reply_text(texts.SESSION_EXPIRED)
        return

    campaign = await asyncio.to_thread(db.get_campaign, campaign_id)

    if not campaign or not campaign["active"]:
        _clear_waiting(context)
        await message.reply_text(texts.CAMPAIGN_UNAVAILABLE)
        return

    has_instagram = await asyncio.to_thread(db.has_instagram_account, user.id)

    if not has_instagram:
        context.user_data["waiting_for"] = "instagram_username"
        await message.reply_html(
            texts.ADD_INSTAGRAM_FIRST,
            reply_markup=keyboards.instagram_keyboard([]),
        )
        return

    raw_lines = [line.strip() for line in (message.text or "").splitlines() if line.strip()]

    if not raw_lines:
        await message.reply_html(texts.INVALID_LINK)
        return

    if len(raw_lines) > 30:
        await message.reply_html(texts.BULK_TOO_MANY)
        return

    created = 0
    duplicates = 0
    invalid = 0

    for raw in raw_lines:
        link = utils.normalize_link(raw)

        if not utils.is_instagram_link(raw):
            invalid += 1
            continue

        result = await asyncio.to_thread(
            db.create_submission,
            user.id,
            campaign_id,
            link,
        )

        if result["duplicate"]:
            duplicates += 1
        else:
            created += 1

    if created + duplicates == 0:
        await message.reply_html(texts.INVALID_LINK)
        return

    _clear_waiting(context)

    text = texts.BULK_RESULT.format(
        created=created,
        duplicates=duplicates,
        invalid=invalid,
    )

    await message.reply_html(text, reply_markup=keyboards.back_main())

    if created > 0:
        try:
            await admin_module.notify_admins_bulk_submission(
                context,
                user.id,
                campaign,
                created,
            )
        except Exception:
            logger.exception("Failed to notify admins about bulk submission")# ------------------------------------------------------------------
# Callback query router
# ------------------------------------------------------------------

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not update.effective_user:
        return

    user = update.effective_user
    data = query.data or ""

    if not utils.allow(user.id, "callback", 50, 60):
        await query.answer("Too many actions. Please slow down.", show_alert=True)
        return

    await _save_user(update)

    try:
        if data.startswith(
            (
                "admin_",
                "appr:",
                "rej:",
                "asub:",
                "togcamp:",
            )
        ):
            await admin_module.handle_callback(update, context)
            return

        await query.answer()

        if data == "menu_main":
            await show_main_menu(update)

        elif data == "menu_campaigns":
            await show_campaigns(update)

        elif data == "menu_submit":
            await show_submit_campaigns(update, bulk=False)

        elif data == "menu_bulk":
            await show_submit_campaigns(update, bulk=True)

        elif data == "menu_instagram":
            await show_instagram(update)

        elif data == "menu_history":
            await show_history(update)

        elif data == "menu_earnings":
            await show_earnings(update)

        elif data == "menu_rules":
            await show_rules_list(update)

        elif data == "menu_help":
            await show_help(update)

        elif data.startswith("camp:"):
            campaign_id = _int_from_data(data)
            if campaign_id is not None:
                await show_campaign_detail(update, campaign_id)

        elif data.startswith("crules:"):
            campaign_id = _int_from_data(data)
            if campaign_id is not None:
                await show_campaign_rules(update, campaign_id)

        elif data.startswith("subcamp:"):
            campaign_id = _int_from_data(data)
            if campaign_id is not None:
                await start_submission(update, context, campaign_id, bulk=False)

        elif data.startswith("bulkcamp:"):
            campaign_id = _int_from_data(data)
            if campaign_id is not None:
                await start_submission(update, context, campaign_id, bulk=True)

        elif data == "ig_add":
            await start_add_instagram(update, context)

        elif data.startswith("igdel:"):
            try:
                account_id = int(data.split(":", 1)[1])
            except (IndexError, ValueError):
                account_id = None

            if account_id is not None:
                await asyncio.to_thread(db.delete_instagram, account_id, user.id)

            await show_instagram(update)

        elif data.startswith("sub:"):
            submission_id = data.split(":", 1)[1] if ":" in data else ""
            await show_submission(update, submission_id)

        elif data == "refresh_history":
            await show_history(update)

        else:
            await show_main_menu(update)

    except Exception:
        logger.exception("Callback error for data: %s", data)

        try:
            await query.answer("An error occurred.", show_alert=True)
        except Exception:
            pass


# ------------------------------------------------------------------
# Text router
# ------------------------------------------------------------------

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not utils.allow(user.id, "text", 30, 60):
        await message.reply_text("Please slow down and try again.")
        return

    await _save_user(update)

    waiting = context.user_data.get("waiting_for")

    if waiting == "instagram_username":
        await handle_add_instagram(update, context)

    elif waiting == "single_link":
        await handle_single_link(update, context)

    elif waiting == "bulk_links":
        await handle_bulk_links(update, context)

    elif waiting == "admin_broadcast" and user.id in config.ADMIN_IDS:
        await admin_module.handle_broadcast_text(update, context)

    elif waiting == "admin_reject_reason" and user.id in config.ADMIN_IDS:
        await admin_module.handle_reject_reason(update, context)

    else:
        await message.reply_html(
            texts.HELP.format(support=utils.esc(config.SUPPORT_USERNAME)),
            reply_markup=keyboards.main_menu(),
        )


# ------------------------------------------------------------------
# Error handler
# ------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled error while processing update", exc_info=context.error)

    try:
        if isinstance(update, Update):
            if update.callback_query:
                await update.callback_query.answer(
                    "An error occurred.",
                    show_alert=True,
                )
            elif update.effective_message:
                await update.effective_message.reply_text(texts.ERROR)
    except Exception:
        logger.exception("Failed to notify user about error")
