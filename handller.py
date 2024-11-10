import logging
import telegram
from functools import wraps
from telegram import CallbackQuery,InputMediaPhoto
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode
from sqlalchemy import func
from database import Session, Category, Question, Exam, UserExam, ExamQuestion
from config import BOT_TOKEN, ZARINPAL_MERCHANT,ADMIN_IDS
# Conversation states
(CATEGORY_NAME, 
 QUESTION_TITLE, QUESTION_IMAGE, QUESTION_OPTION_A, QUESTION_OPTION_B, 
 QUESTION_OPTION_C, QUESTION_OPTION_D, QUESTION_CORRECT, QUESTION_CATEGORY,
 EXAM_TITLE, EXAM_PRICE, EXAM_QUESTION_COUNT, EXAM_CATEGORY) = range(13)



# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ کنترل کاربر ادمین  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("⛔️ شما دسترسی به این عملکرد را ندارید.")
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapped

@admin_only
async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ افزودن دسته‌بندی", callback_data='add_category')],
        [InlineKeyboardButton("➕ افزودن سؤال", callback_data='add_question')],
        [InlineKeyboardButton("➕ ایجاد آزمون", callback_data='create_exam')],
        [InlineKeyboardButton("👥 مدیریت دسترسی کاربران", callback_data='manage_user_access')],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "👨‍💼 پنل مدیریت\nلطفاً یک گزینه را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "👨‍💼 پنل مدیریت\nلطفاً یک گزینه را انتخاب کنید:",
            reply_markup=reply_markup
        )

@admin_only
async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await show_admin_menu(update, context)
        return ConversationHandler.END
    return ConversationHandler.END

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ ایجاد سوال  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# *************************************************************************************** Add Question Image *****************************************
async def add_question_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['question_image'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 لطفاً گزینه A را وارد کنید:",
        reply_markup=reply_markup
    )
    return QUESTION_OPTION_A
# *************************************************************************************** Add Question Option A *****************************************
async def add_question_option_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['option_a'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 لطفاً گزینه B را وارد کنید:",
        reply_markup=reply_markup
    )
    return QUESTION_OPTION_B
# *************************************************************************************** Add Question Option B *****************************************
async def add_question_option_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['option_b'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 لطفاً گزینه C را وارد کنید:",
        reply_markup=reply_markup
    )
    return QUESTION_OPTION_C
# *************************************************************************************** Add Question Option C *****************************************
async def add_question_option_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['option_c'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 لطفاً گزینه D را وارد کنید:",
        reply_markup=reply_markup
    )
    return QUESTION_OPTION_D
# *************************************************************************************** Add Question Option D *****************************************
async def add_question_option_d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['option_d'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 لطفاً گزینه صحیح را وارد کنید (A, B, C یا D):",
        reply_markup=reply_markup
    )
    return QUESTION_CORRECT

# *************************************************************************************** Add Question Currect *****************************************
async def add_question_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    correct_answer = update.message.text.upper()
    if correct_answer not in ['A', 'B', 'C', 'D']:
        await update.message.reply_text("❌ لطفاً یکی از گزینه‌های A، B، C یا D را وارد کنید.")
        return QUESTION_CORRECT
        
    context.user_data['correct_answer'] = correct_answer
    
    session = Session()
    categories = session.query(Category).all()
    session.close()
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            category.name, 
            callback_data=f'qcat_{category.id}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📂 لطفاً دسته‌بندی سؤال را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return QUESTION_CATEGORY

# *************************************************************************************** Add Question Category *****************************************
async def add_question_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    category_id = int(query.data.split('_')[1])
    
    session = Session()
    new_question = Question(
        title=context.user_data['question_title'],
        image_url=context.user_data['question_image'] if context.user_data['question_image'] != '0' else None,
        option_a=context.user_data['option_a'],
        option_b=context.user_data['option_b'],
        option_c=context.user_data['option_c'],
        option_d=context.user_data['option_d'],
        correct_answer=context.user_data['correct_answer'],
        category_id=category_id
    )
    session.add(new_question)
    session.commit()
    session.close()
    
    # پاک کردن داده‌های ذخیره شده
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ سؤال با موفقیت اضافه شد.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$