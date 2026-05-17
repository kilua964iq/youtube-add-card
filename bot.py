import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv
from file_manager import *

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID"))

# ═══ حالات المحادثة ═══
(
    ADD_ACCOUNT_NAME, ADD_ACCOUNT_EMAIL, ADD_ACCOUNT_PASS,
    ADD_CARD_NAME, ADD_CARD_NUMBER, ADD_CARD_EXPIRY, ADD_CARD_CVV
) = range(7)

# ═══════════════════════════
#      القائمة الرئيسية
# ═══════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ غير مصرح لك")
        return

    keyboard = [
        [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="menu_accounts")],
        [InlineKeyboardButton("💳 إدارة البطاقات", callback_data="menu_cards")],
        [InlineKeyboardButton("⚡ ربط بطاقة بحساب", callback_data="menu_link")],
    ]
    await update.message.reply_text(
        "🏠 *القائمة الرئيسية*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      قائمة الحسابات
# ═══════════════════════════

async def menu_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
        [InlineKeyboardButton("📋 عرض الحسابات", callback_data="view_accounts")],
        [InlineKeyboardButton("🗑️ حذف حساب", callback_data="del_account")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ]
    await query.edit_message_text(
        "👥 *إدارة الحسابات*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      قائمة البطاقات
# ═══════════════════════════

async def menu_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ إضافة بطاقة", callback_data="add_card")],
        [InlineKeyboardButton("📋 عرض البطاقات", callback_data="view_cards")],
        [InlineKeyboardButton("🗑️ حذف بطاقة", callback_data="del_card")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ]
    await query.edit_message_text(
        "💳 *إدارة البطاقات*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      عرض الحسابات
# ═══════════════════════════

async def view_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = get_all_accounts()
    if not accounts:
        text = "📭 لا يوجد حسابات مضافة"
    else:
        text = "👥 *الحسابات المضافة:*\n\n"
        for name, data in accounts.items():
            text += f"• *{name}*: `{data['email']}`\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_accounts")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      عرض البطاقات
# ═══════════════════════════

async def view_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cards = get_all_cards()
    if not cards:
        text = "📭 لا يوجد بطاقات مضافة"
    else:
        text = "💳 *البطاقات المضافة:*\n\n"
        for name, data in cards.items():
            masked = f"****{data['number'][-4:]}"
            text += f"• *{name}*: `{masked}` - {data['expiry']}\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_cards")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#    إضافة حساب - محادثة
# ═══════════════════════════

async def add_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✏️ أرسل *اسم الحساب* (مثال: ابني):", parse_mode="Markdown")
    return ADD_ACCOUNT_NAME

async def add_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["acc_name"] = update.message.text
    await update.message.reply_text("📧 أرسل *الإيميل*:", parse_mode="Markdown")
    return ADD_ACCOUNT_EMAIL

async def add_account_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["acc_email"] = update.message.text
    await update.message.reply_text("🔑 أرسل *الباسورد*:", parse_mode="Markdown")
    return ADD_ACCOUNT_PASS

async def add_account_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data["acc_name"]
    email = context.user_data["acc_email"]
    password = update.message.text
    save_account(name, email, password)
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]]
    await update.message.reply_text(
        f"✅ تم حفظ حساب *{name}* بنجاح!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ═══════════════════════════
#    إضافة بطاقة - محادثة
# ═══════════════════════════

async def add_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✏️ أرسل *اسم البطاقة* (مثال: فيزا الراجحي):", parse_mode="Markdown")
    return ADD_CARD_NAME

async def add_card_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["card_name"] = update.message.text
    await update.message.reply_text("💳 أرسل *رقم البطاقة*:", parse_mode="Markdown")
    return ADD_CARD_NUMBER

async def add_card_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["card_number"] = update.message.text
    await update.message.reply_text("📅 أرسل *تاريخ الانتهاء* (مثال: 12/26):", parse_mode="Markdown")
    return ADD_CARD_EXPIRY

async def add_card_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["card_expiry"] = update.message.text
    await update.message.reply_text("🔒 أرسل *CVV*:", parse_mode="Markdown")
    return ADD_CARD_CVV

async def add_card_cvv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data["card_name"]
    number = context.user_data["card_number"]
    expiry = context.user_data["card_expiry"]
    cvv = update.message.text
    save_card(name, number, expiry, cvv)
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]]
    await update.message.reply_text(
        f"✅ تم حفظ بطاقة *{name}* بنجاح!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ═══════════════════════════
#      حذف حساب
# ═══════════════════════════

async def del_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = get_all_accounts()
    if not accounts:
        await query.edit_message_text("📭 لا يوجد حسابات للحذف")
        return
    keyboard = []
    for name in accounts:
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f"delaccount_{name}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_accounts")])
    await query.edit_message_text(
        "اختر الحساب للحذف:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def del_account_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace("delaccount_", "")
    delete_account(name)
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]]
    await query.edit_message_text(
        f"✅ تم حذف حساب *{name}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      حذف بطاقة
# ═══════════════════════════

async def del_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cards = get_all_cards()
    if not cards:
        await query.edit_message_text("📭 لا يوجد بطاقات للحذف")
        return
    keyboard = []
    for name in cards:
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f"delcard_{name}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_cards")])
    await query.edit_message_text(
        "اختر البطاقة للحذف:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def del_card_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace("delcard_", "")
    delete_card(name)
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]]
    await query.edit_message_text(
        f"✅ تم حذف بطاقة *{name}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      ربط بطاقة بحساب
# ═══════════════════════════

async def menu_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    accounts = get_all_accounts()
    if not accounts:
        await query.edit_message_text("📭 أضف حسابات أولاً")
        return
    keyboard = []
    for name in accounts:
        keyboard.append([InlineKeyboardButton(f"👤 {name}", callback_data=f"linkaccount_{name}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    await query.edit_message_text(
        "اختر الحساب:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def link_choose_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    account_name = query.data.replace("linkaccount_", "")
    context.user_data["link_account"] = account_name
    cards = get_all_cards()
    if not cards:
        await query.edit_message_text("📭 أضف بطاقات أولاً")
        return
    keyboard = []
    for name in cards:
        keyboard.append([InlineKeyboardButton(f"💳 {name}", callback_data=f"linkcard_{name}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_link")])
    await query.edit_message_text(
        f"اختر البطاقة للحساب *{account_name}*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def link_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_name = query.data.replace("linkcard_", "")
    account_name = context.user_data["link_account"]
    accounts = get_all_accounts()
    cards = get_all_cards()
    account = accounts[account_name]
    card = cards[card_name]
    await query.edit_message_text(
        f"⏳ جاري ربط بطاقة *{card_name}* بحساب *{account_name}*...",
        parse_mode="Markdown"
    )
    # هنا نستدعي الأتمتة
    from automation import link_card
    result = await link_card(account, card)
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")]]
    await query.edit_message_text(
        result,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      رجوع للرئيسية
# ═══════════════════════════

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="menu_accounts")],
        [InlineKeyboardButton("💳 إدارة البطاقات", callback_data="menu_cards")],
        [InlineKeyboardButton("⚡ ربط بطاقة بحساب", callback_data="menu_link")],
    ]
    await query.edit_message_text(
        "🏠 *القائمة الرئيسية*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════
#      تشغيل البوت
# ═══════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler للحسابات
    acc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_account_start, pattern="add_account")],
        states={
            ADD_ACCOUNT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_name)],
            ADD_ACCOUNT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_email)],
            ADD_ACCOUNT_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_pass)],
        },
        fallbacks=[]
    )

    # ConversationHandler للبطاقات
    card_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_card_start, pattern="add_card")],
        states={
            ADD_CARD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_name)],
            ADD_CARD_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_number)],
            ADD_CARD_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_expiry)],
            ADD_CARD_CVV: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_cvv)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(acc_conv)
    app.add_handler(card_conv)
    app.add_handler(CallbackQueryHandler(menu_accounts, pattern="menu_accounts"))
    app.add_handler(CallbackQueryHandler(menu_cards, pattern="menu_cards"))
    app.add_handler(CallbackQueryHandler(menu_link, pattern="menu_link"))
    app.add_handler(CallbackQueryHandler(view_accounts, pattern="view_accounts"))
    app.add_handler(CallbackQueryHandler(view_cards, pattern="view_cards"))
    app.add_handler(CallbackQueryHandler(del_account, pattern="del_account"))
    app.add_handler(CallbackQueryHandler(del_card, pattern="del_card"))
    app.add_handler(CallbackQueryHandler(del_account_confirm, pattern="delaccount_"))
    app.add_handler(CallbackQueryHandler(del_card_confirm, pattern="delcard_"))
    app.add_handler(CallbackQueryHandler(link_choose_card, pattern="linkaccount_"))
    app.add_handler(CallbackQueryHandler(link_execute, pattern="linkcard_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="back_main"))

    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
