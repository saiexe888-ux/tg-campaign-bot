from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ------------------------------------------------------------------
# User keyboards
# ------------------------------------------------------------------

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Campaigns", callback_data="menu_campaigns"),
                InlineKeyboardButton("📸 Instagram", callback_data="menu_instagram"),
            ],
            [
                InlineKeyboardButton("🎬 Submit Reel", callback_data="menu_submit"),
                InlineKeyboardButton("🧾 Bulk Submit", callback_data="menu_bulk"),
            ],
            [
                InlineKeyboardButton("📜 My Submissions", callback_data="menu_history"),
                InlineKeyboardButton("💰 Earnings", callback_data="menu_earnings"),
            ],
            [
                InlineKeyboardButton("📋 Campaign Rules", callback_data="menu_rules"),
                InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
            ],
        ]
    )


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main")
            ]
        ]
    )


def campaigns_keyboard(campaigns: list) -> InlineKeyboardMarkup:
    rows = []

    for campaign in campaigns:
        rows.append(
            [
                InlineKeyboardButton(
                    campaign["name"][:35],
                    callback_data=f"camp:{campaign['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(rows)


def submit_campaigns_keyboard(campaigns: list, bulk: bool = False) -> InlineKeyboardMarkup:
    prefix = "bulkcamp" if bulk else "subcamp"
    rows = []

    for campaign in campaigns:
        rows.append(
            [
                InlineKeyboardButton(
                    campaign["name"][:35],
                    callback_data=f"{prefix}:{campaign['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(rows)


def rules_keyboard(campaigns: list) -> InlineKeyboardMarkup:
    rows = []

    for campaign in campaigns:
        rows.append(
            [
                InlineKeyboardButton(
                    campaign["name"][:35],
                    callback_data=f"crules:{campaign['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(rows)


def campaign_detail_keyboard(campaign: dict) -> InlineKeyboardMarkup:
    campaign_id = campaign["id"]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 Submit one reel", callback_data=f"subcamp:{campaign_id}"),
                InlineKeyboardButton("🧾 Bulk submit", callback_data=f"bulkcamp:{campaign_id}"),
            ],
            [
                InlineKeyboardButton("📋 Rules", callback_data=f"crules:{campaign_id}"),
                InlineKeyboardButton("⬅️ Campaigns", callback_data="menu_campaigns"),
            ],
        ]
    )


def instagram_keyboard(accounts: list) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("➕ Add Instagram account", callback_data="ig_add")
        ]
    ]

    for account in accounts:
        rows.append(
            [
                InlineKeyboardButton(
                    f"❌ @{account['username']}",
                    callback_data=f"igdel:{account['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(rows)


def history_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_history"),
                InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main"),
            ]
        ]
    )


def submission_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_main")
            ]
        ]
    )


# ------------------------------------------------------------------
# Admin keyboards
# ------------------------------------------------------------------

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📥 Pending", callback_data="admin_pending"),
                InlineKeyboardButton("📢 Campaigns", callback_data="admin_campaigns"),
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
                InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton("🧰 Admin Commands", callback_data="admin_help")
            ],
        ]
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel")
            ]
        ]
    )


def admin_back_pending_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ Pending", callback_data="admin_pending"),
                InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel"),
            ]
        ]
    )


def admin_pending_keyboard(pending: list) -> InlineKeyboardMarkup:
    rows = []

    for submission in pending[:20]:
        label = f"{submission['id']} • {submission['campaign_name'][:20]}"
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"asub:{submission['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel")])

    return InlineKeyboardMarkup(rows)


def admin_submission_keyboard(submission_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"appr:{submission_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rej:{submission_id}"),
            ],
            [
                InlineKeyboardButton("⬅️ Pending", callback_data="admin_pending")
            ],
        ]
    )


def admin_campaigns_keyboard(campaigns: list) -> InlineKeyboardMarkup:
    rows = []

    for campaign in campaigns:
        icon = "✅" if campaign["active"] else "⛔"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {campaign['name'][:25]}",
                    callback_data=f"togcamp:{campaign['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_panel")])

    return InlineKeyboardMarkup(rows)
