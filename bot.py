import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv
from file_manager import (
    load_accounts, add_account, delete_account,
    load_cards, add_card, delete_card
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID"))

# ═══ حالات المحادثة ═══
ADD_ACCOUNT, ADD_CARD = range(2)

# ═══════════════════════════════
#         دوال مساعدة
# ═══════════════════════════════

def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 الحسابات", callback_data="menu_accounts"),
            InlineKeyboardButton("💳 البطاقات", callback_data="menu_cards")
        ],
        [InlineKeyboardButton("⚡ ربط بطاقة بحساب", callback_data="menu_link")],
        [InlineKeyboardButton("🚀 ربط الكل دفعة وحدة", callback_data="link_all")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")]
    ])

# ═══════════════════════════════
#         القائمة الرئيسية
# ═══════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ غير مصرح لك")
        return
    context.user_data.clear()
    await update.message.reply_text(
        "🏠 *القائمة الرئيسية*\nاختر من القائمة:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(
        "🏠 *القائمة الرئيسية*\nاختر من القائمة:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# ═══════════════════════════════
#         إحصائيات
# ═══════════════════════════════

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_accounts()
    cards = load_cards()
    text = (
        f"📊 *الإحصائيات*\n\n"
        f"👥 عدد الحسابات: `{len(accounts)}`\n"
        f"💳 عدد البطاقات: `{len(cards)}`\n"
        f"🔗 إجمالي العمليات الممكنة: `{len(accounts) * len(cards)}`"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════════
#         قائمة الحسابات
# ═══════════════════════════════

async def menu_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
        [InlineKeyboardButton("📋 عرض الحسابات", callback_data="view_accounts")],
        [InlineKeyboardButton("🗑️ حذف حساب", callback_data="del_account_menu")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ])
    await query.edit_message_text(
        "👥 *إدارة الحسابات*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def view_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_accounts()
    if not accounts:
        text = (
            "📭 *لا يوجد حسابات*\n\n"
            "أضف حسابات عن طريق:\n"
            "• زر إضافة حساب\n"
            "• أو عدل ملف accounts.txt مباشرة\n\n"
            "الصيغة:\n`email@gmail.com:password`"
        )
    else:
        text = f"👥 *الحسابات المضافة ({len(accounts)}):*\n\n"
        for i, acc in enumerate(accounts, 1):
            text += f"`{i}.` `{acc['email']}`\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_accounts")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *إضافة حساب*\n\n"
        "أرسل بيانات الحساب بهذا الشكل:\n"
        "`email@gmail.com:password`\n\n"
        "مثال:\n"
        "`son@gmail.com:Pass1234`\n\n"
        "أو أرسل عدة حسابات دفعة وحدة:\n"
        "`email1@gmail.com:pass1`\n"
        "`email2@gmail.com:pass2`",
        parse_mode="Markdown"
    )
    return ADD_ACCOUNT

async def add_account_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lines = text.split("\n")
    added = []
    failed = []
    exists = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            failed.append(line)
            continue
        parts = line.split(":", 1)
        if len(parts) != 2:
            failed.append(line)
            continue
        email, password = parts[0].strip(), parts[1].strip()
        if not email or not password:
            failed.append(line)
            continue
        result = add_account(email, password)
        if result:
            added.append(email)
        else:
            exists.append(email)

    response = ""
    if added:
        response += f"✅ *تم إضافة {len(added)} حساب:*\n"
        for e in added:
            response += f"• `{e}`\n"
        response += "\n"
    if exists:
        response += f"⚠️ *موجود مسبقاً {len(exists)}:*\n"
        for e in exists:
            response += f"• `{e}`\n"
        response += "\n"
    if failed:
        response += f"❌ *فشل {len(failed)} - صيغة خاطئة:*\n"
        for e in failed:
            response += f"• `{e}`\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_account")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]
    ])
    await update.message.reply_text(
        response or "❌ لم يتم إضافة أي حساب",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def del_account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_accounts()
    if not accounts:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_accounts")]]
        await query.edit_message_text(
            "📭 لا يوجد حسابات للحذف",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    buttons = []
    for acc in accounts:
        email = acc["email"]
        short = email[:25] + "..." if len(email) > 25 else email
        buttons.append([InlineKeyboardButton(
            f"🗑️ {short}",
            callback_data=f"delacc_{email}"
        )])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_accounts")])
    await query.edit_message_text(
        "🗑️ *اختر الحساب للحذف:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def del_account_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    email = query.data.replace("delacc_", "")
    delete_account(email)
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_accounts")]]
    await query.edit_message_text(
        f"✅ تم حذف الحساب:\n`{email}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════════
#         قائمة البطاقات
# ═══════════════════════════════

async def menu_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة بطاقة", callback_data="add_card")],
        [InlineKeyboardButton("📋 عرض البطاقات", callback_data="view_cards")],
        [InlineKeyboardButton("🗑️ حذف بطاقة", callback_data="del_card_menu")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ])
    await query.edit_message_text(
        "💳 *إدارة البطاقات*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def view_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cards = load_cards()
    if not cards:
        text = (
            "📭 *لا يوجد بطاقات*\n\n"
            "أضف بطاقات عن طريق:\n"
            "• زر إضافة بطاقة\n"
            "• أو عدل ملف cards.txt مباشرة\n\n"
            "الصيغة:\n`رقم|شهر|سنة|cvv`\n"
            "مثال:\n`5488093706666666|09|27|000`"
        )
    else:
        text = f"💳 *البطاقات المضافة ({len(cards)}):*\n\n"
        for i, card in enumerate(cards, 1):
            masked = f"****{card['number'][-4:]}"
            text += f"`{i}.` `{masked}` | {card['month']}/{card['year']}\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_cards")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *إضافة بطاقة*\n\n"
        "أرسل بيانات البطاقة بهذا الشكل:\n"
        "`رقم|شهر|سنة|cvv`\n\n"
        "مثال:\n"
        "`5488093706666666|09|27|000`\n\n"
        "أو أرسل عدة بطاقات دفعة وحدة:\n"
        "`5488093706666666|09|27|000`\n"
        "`4111111111111111|12|26|123`",
        parse_mode="Markdown"
    )
    return ADD_CARD

async def add_card_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lines = text.split("\n")
    added = []
    failed = []
    exists = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "|" not in line:
            failed.append(line)
            continue
        parts = line.split("|")
        if len(parts) != 4:
            failed.append(line)
            continue
        number, month, year, cvv = [p.strip() for p in parts]
        if not all([number, month, year, cvv]):
            failed.append(line)
            continue
        if not number.isdigit() or len(number) < 15:
            failed.append(f"{line} ← رقم خاطئ")
            continue
        result = add_card(number, month, year, cvv)
        if result:
            added.append(f"****{number[-4:]}")
        else:
            exists.append(f"****{number[-4:]}")

    response = ""
    if added:
        response += f"✅ *تم إضافة {len(added)} بطاقة:*\n"
        for c in added:
            response += f"• `{c}`\n"
        response += "\n"
    if exists:
        response += f"⚠️ *موجودة مسبقاً {len(exists)}:*\n"
        for c in exists:
            response += f"• `{c}`\n"
        response += "\n"
    if failed:
        response += f"❌ *فشل {len(failed)} - صيغة خاطئة:*\n"
        for c in failed:
            response += f"• `{c}`\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_card")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]
    ])
    await update.message.reply_text(
        response or "❌ لم يتم إضافة أي بطاقة",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def del_card_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cards = load_cards()
    if not cards:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_cards")]]
        await query.edit_message_text(
            "📭 لا يوجد بطاقات للحذف",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    buttons = []
    for card in cards:
        masked = f"****{card['number'][-4:]}"
        buttons.append([InlineKeyboardButton(
            f"🗑️ {masked} | {card['month']}/{card['year']}",
            callback_data=f"delcard_{card['number']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_cards")])
    await query.edit_message_text(
        "🗑️ *اختر البطاقة للحذف:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def del_card_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    number = query.data.replace("delcard_", "")
    delete_card(number)
    masked = f"****{number[-4:]}"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_cards")]]
    await query.edit_message_text(
        f"✅ تم حذف البطاقة: `{masked}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════════
#         ربط بطاقة بحساب
# ═══════════════════════════════

async def menu_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_accounts()
    if not accounts:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
        await query.edit_message_text(
            "📭 أضف حسابات أولاً",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    buttons = []
    for i, acc in enumerate(accounts):
        email = acc["email"]
        short = email[:28] + "..." if len(email) > 28 else email
        buttons.append([InlineKeyboardButton(
            f"👤 {short}",
            callback_data=f"linkaccount_{i}"
        )])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    await query.edit_message_text(
        "⚡ *اختر الحساب:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def link_choose_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    acc_index = int(query.data.replace("linkaccount_", ""))
    accounts = load_accounts()
    context.user_data["link_account_index"] = acc_index
    context.user_data["link_account"] = accounts[acc_index]
    cards = load_cards()
    if not cards:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_link")]]
        await query.edit_message_text(
            "📭 أضف بطاقات أولاً",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    buttons = []
    for i, card in enumerate(cards):
        masked = f"****{card['number'][-4:]}"
        buttons.append([InlineKeyboardButton(
            f"💳 {masked} | {card['month']}/{card['year']}",
            callback_data=f"linkcard_{i}"
        )])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_link")])
    email = accounts[acc_index]["email"]
    await query.edit_message_text(
        f"💳 *اختر البطاقة للحساب:*\n`{email}`",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def link_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_index = int(query.data.replace("linkcard_", ""))
    cards = load_cards()
    account = context.user_data.get("link_account")
    if not account:
        await query.edit_message_text("❌ حدث خطأ، ابدأ من جديد")
        return
    card = cards[card_index]
    masked = f"****{card['number'][-4:]}"
    await query.edit_message_text(
        f"⏳ *جاري ربط البطاقة...*\n\n"
        f"👤 الحساب: `{account['email']}`\n"
        f"💳 البطاقة: `{masked}`\n\n"
        f"انتظر...",
        parse_mode="Markdown"
    )
    from automation import link_card
    result = await link_card(account, card)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ربط بطاقة أخرى", callback_data="menu_link")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]
    ])
    await query.edit_message_text(
        result,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ═══════════════════════════════
#      ربط الكل دفعة وحدة
# ═══════════════════════════════

async def link_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = load_accounts()
    cards = load_cards()
    if not accounts:
        await query.edit_message_text("📭 أضف حسابات أولاً")
        return
    if not cards:
        await query.edit_message_text("📭 أضف بطاقات أولاً")
        return

    # اختيار البطاقة أولاً
    buttons = []
    for i, card in enumerate(cards):
        masked = f"****{card['number'][-4:]}"
        buttons.append([InlineKeyboardButton(
            f"💳 {masked} | {card['month']}/{card['year']}",
            callback_data=f"linkallcard_{i}"
        )])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    await query.edit_message_text(
        f"🚀 *ربط الكل دفعة وحدة*\n\n"
        f"👥 عدد الحسابات: `{len(accounts)}`\n\n"
        f"اختر البطاقة:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def link_all_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_index = int(query.data.replace("linkallcard_", ""))
    accounts = load_accounts()
    cards = load_cards()
    card = cards[card_index]
    masked = f"****{card['number'][-4:]}"

    await query.edit_message_text(
        f"🚀 *بدأت العملية...*\n\n"
        f"💳 البطاقة: `{masked}`\n"
        f"👥 الحسابات: `{len(accounts)}`\n\n"
        f"⏳ جاري الربط...",
        parse_mode="Markdown"
    )

    from automation import link_card

    success = []
    failed = []
    otp_needed = []

    for acc in accounts:
        result = await link_card(acc, card)
        if "✅" in result:
            success.append(acc["email"])
        elif "⚠️" in result:
            otp_needed.append(acc["email"])
        else:
            failed.append(f"{acc['email']}")

    report = f"📊 *تقرير الربط - {masked}*\n\n"

    if success:
        report += f"✅ *نجح ({len(success)}):*\n"
        for e in success:
            report += f"• `{e}`\n"
        report += "\n"

    if otp_needed:
        report += f"⚠️ *يحتاج OTP ({len(otp_needed)}):*\n"
        for e in otp_needed:
            report += f"• `{e}`\n"
        report += "\n"

    if failed:
        report += f"❌ *فشل ({len(failed)}):*\n"
        for e in failed:
            report += f"• `{e}`\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 ربط الكل مجدداً", callback_data="link_all")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]
    ])
    await query.edit_message_text(
        report,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ═══════════════════════════════
#         تشغيل البوت
# ═══════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    acc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_account_start, pattern="^add_account$")],
        states={
            ADD_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_receive)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
        per_chat=True,
    )

    card_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_card_start, pattern="^add_card$")],
        states={
            ADD_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_receive)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
        per_chat=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(acc_conv)
    app.add_handler(card_conv)
    app.add_handler(CallbackQueryHandler(back_main,          pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(stats,              pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(menu_accounts,      pattern="^menu_accounts$"))
    app.add_handler(CallbackQueryHandler(menu_cards,         pattern="^menu_cards$"))
    app.add_handler(CallbackQueryHandler(menu_link,          pattern="^menu_link$"))
    app.add_handler(CallbackQueryHandler(link_all,           pattern="^link_all$"))
    app.add_handler(CallbackQueryHandler(view_accounts,      pattern="^view_accounts$"))
    app.add_handler(CallbackQueryHandler(view_cards,         pattern="^view_cards$"))
    app.add_handler(CallbackQueryHandler(del_account_menu,   pattern="^del_account_menu$"))
    app.add_handler(CallbackQueryHandler(del_card_menu,      pattern="^del_card_menu$"))
    app.add_handler(CallbackQueryHandler(del_account_confirm,pattern="^delacc_"))
    app.add_handler(CallbackQueryHandler(del_card_confirm,   pattern="^delcard_"))
    app.add_handler(CallbackQueryHandler(link_choose_card,   pattern="^linkaccount_"))
    app.add_handler(CallbackQueryHandler(link_execute,       pattern="^linkcard_"))
    app.add_handler(CallbackQueryHandler(link_all_execute,   pattern="^linkallcard_"))

    print("✅ البوت شغال...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
