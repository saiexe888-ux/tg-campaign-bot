WELCOME = (
    "👋 Hello {name}!\n\n"
    "This is a campaign submission bot.\n\n"
    "You can:\n"
    "• View campaigns\n"
    "• Add your Instagram account\n"
    "• Submit reel/post links\n"
    "• Track approvals, views and payout\n\n"
    "Use the buttons below."
)

HELP = (
    "ℹ️ <b>Help</b>\n\n"
    "<b>User commands</b>\n"
    "/start - Start the bot\n"
    "/campaigns - View active campaigns\n"
    "/instagram - Manage Instagram accounts\n"
    "/history - View your submissions\n"
    "/earnings - View payout summary\n"
    "/cancel - Cancel current input\n"
    "/help - Show this help\n\n"
    "<b>How it works</b>\n"
    "1. Add your Instagram username.\n"
    "2. Choose a campaign.\n"
    "3. Submit your Instagram reel/post link.\n"
    "4. Wait for admin approval.\n"
    "5. Views and payout are tracked after approval.\n\n"
    "Support: {support}"
)

ERROR = "Sorry, something went wrong. Please try again later."

NO_CAMPAIGNS = "There are no active campaigns right now. Please check later."

CAMPAIGNS_TITLE = "📢 <b>Active Campaigns</b>\n\nChoose a campaign:"

CHOOSE_CAMPAIGN = "Choose a campaign:"

CAMPAIGN_DETAILS = (
    "📢 <b>{name}</b>\n\n"
    "{description}\n\n"
    "💵 Payout per view: {payout}\n"
    "🎯 Target views: {target}\n"
    "📌 Status: {status}\n\n"
    "Use the buttons below to submit."
)

CAMPAIGN_RULES = (
    "📋 <b>{name} Rules</b>\n\n"
    "{rules}"
)

DEFAULT_RULES = (
    "• Your Instagram account must be public.\n"
    "• The reel/post must remain available.\n"
    "• Do not submit fake or reused links.\n"
    "• Only submit links that match the campaign.\n"
    "• Admin decision is final."
)

CAMPAIGN_UNAVAILABLE = "This campaign is not available."

INSTAGRAM_TITLE = "📸 <b>Your Instagram Accounts</b>\n"

NO_INSTAGRAM = (
    "📸 <b>Your Instagram Accounts</b>\n\n"
    "You have not added an Instagram account yet.\n"
    "Add one before submitting links."
)

ASK_INSTAGRAM_USERNAME = (
    "Send your Instagram username.\n\n"
    "Example:\n"
    "<code>myusername</code>\n\n"
    "You can include @ or not."
)

ADD_INSTAGRAM_FIRST = (
    "Please add your Instagram account first.\n\n"
    "Use /instagram or press the button below."
)

ASK_SINGLE_LINK = (
    "🎬 Send one Instagram reel/post link for campaign:\n"
    "<b>{campaign}</b>\n\n"
    "Example:\n"
    "<code>https://www.instagram.com/reel/ABC123/</code>"
)

ASK_BULK_LINKS = (
    "🧾 Send Instagram links for campaign:\n"
    "<b>{campaign}</b>\n\n"
    "Send one link per line.\n"
    "Maximum 30 links per message.\n\n"
    "Example:\n"
    "<code>https://www.instagram.com/reel/AAA111/\n"
    "https://www.instagram.com/reel/BBB222/</code>"
)

INVALID_LINK = "Please send a valid Instagram reel/post link."

INVALID_INPUT = "Invalid input."

SESSION_EXPIRED = "Session expired. Please use the menu again."

BULK_TOO_MANY = "Please send at most 30 links in one bulk message."

SUBMISSION_CREATED = (
    "✅ Submission received.\n\n"
    "Submission ID: <code>{sub_id}</code>\n"
    "Campaign: {campaign}\n"
    "Status: pending\n\n"
    "You can check it later in My Submissions."
)

SUBMISSION_DUPLICATE = (
    "⚠️ You already submitted this link.\n\n"
    "Submission ID: <code>{sub_id}</code>\n"
    "Current status: {status}"
)

BULK_RESULT = (
    "🧾 Bulk submission finished.\n\n"
    "Created: {created}\n"
    "Duplicates: {duplicates}\n"
    "Invalid links: {invalid}"
)

HISTORY_TITLE = "📜 <b>Your Recent Submissions</b>\n"

NO_HISTORY = "You have no submissions yet."

SUBMISSION_NOT_FOUND = "Submission not found."

EARNINGS = (
    "💰 <b>Your Earnings</b>\n\n"
    "Total submissions: {total}\n"
    "Pending: {pending}\n"
    "Approved: {approved}\n"
    "Rejected: {rejected}\n\n"
    "Approved views: {views}\n"
    "Approved payout: {payout}"
)

ADMIN_PANEL = (
    "🛠 <b>Admin Panel</b>\n\n"
    "Use the buttons below.\n\n"
    "For commands, press Admin Commands."
)

ADMIN_PENDING_TITLE = "📥 <b>Pending Submissions</b>\n\nChoose a submission:"

ADMIN_PENDING_EMPTY = "No pending submissions."

ADMIN_CAMPAIGNS_TITLE = (
    "📢 <b>Campaigns</b>\n\n"
    "Tap a campaign to enable/disable it."
)

ADMIN_STATS = (
    "📊 <b>Stats</b>\n\n"
    "Users: {users}\n"
    "Active campaigns: {active_campaigns}\n"
    "Pending submissions: {pending}\n"
    "Approved submissions: {approved}\n"
    "Rejected submissions: {rejected}\n"
    "Total approved payout: {payout}"
)

ADMIN_BROADCAST_PROMPT = (
    "Send the message you want to broadcast to all users.\n\n"
    "Use /cancel to abort."
)

ADMIN_BROADCAST_STARTED = "Broadcast started. It may take some time."

ADMIN_BROADCAST_DONE = (
    "Broadcast finished.\n\n"
    "Sent: {sent}\n"
    "Failed: {failed}"
)

ADMIN_COMMANDS_HELP = (
    "🧰 <b>Admin Commands</b>\n\n"
    "<code>/admin</code> - Open admin panel\n"
    "<code>/newcampaign 0.01 5000 Campaign Name</code> - Create campaign\n"
    "<code>/setdesc 1 Description text</code> - Set campaign description\n"
    "<code>/setrules 1 Rules text</code> - Set campaign rules\n"
    "<code>/togglecampaign 1</code> - Enable/disable campaign\n"
    "<code>/approve SUBMISSION_ID</code> - Approve submission\n"
    "<code>/reject SUBMISSION_ID reason</code> - Reject submission\n"
    "<code>/setviews SUBMISSION_ID 1000</code> - Update views/payout\n"
    "<code>/broadcast message</code> - Broadcast message\n"
)

APPROVED_MSG = (
    "✅ Your submission <code>{sub_id}</code> for {campaign} was approved.\n\n"
    "Views and payout will be tracked for this submission."
)

REJECTED_MSG = (
    "❌ Your submission <code>{sub_id}</code> was rejected.\n\n"
    "Reason: {reason}"
)

VIEWS_UPDATED_MSG = (
    "📊 Your submission <code>{sub_id}</code> was updated.\n\n"
    "Views: {views}\n"
    "Payout: {payout}"
)

NEW_SUBMISSION_ADMIN = (
    "🆕 New submission\n\n"
    "ID: <code>{sub_id}</code>\n"
    "User: {user}\n"
    "Campaign: {campaign}\n"
    "Link: {link}"
)

NEW_BULK_SUBMISSION_ADMIN = (
    "📦 Bulk submission\n\n"
    "User: {user_id}\n"
    "Campaign: {campaign}\n"
    "Created submissions: {created}"
)
