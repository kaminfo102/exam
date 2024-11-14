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




#**********************************************************************   ADMIN CONTROLLER ****************************************************

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

# *************************************************************************************** Back To Admin *****************************************
@admin_only
async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await show_admin_menu(update, context)
        return ConversationHandler.END
    return ConversationHandler.END

# *************************************************************************************** Admin Start *********************************************
@admin_only
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_admin_menu(update, context)

# *************************************************************************************** Add Question Category *****************************************
async def add_question_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'admin_menu':
        return await back_to_admin(update, context)
    
    try:
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
        
        context.user_data.clear()
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ سؤال با موفقیت اضافه شد.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
        
    except (ValueError, KeyError, AttributeError) as e:
        logging.error(f"Error in add_question_category: {e}")
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')
            ]])
        )
        return ConversationHandler.END

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

# *************************************************************************************** Add Question Start *****************************************
async def add_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 لطفاً متن سؤال را وارد کنید:",
        reply_markup=reply_markup
    )
    return QUESTION_TITLE
# *************************************************************************************** Add Question Title *****************************************
async def add_question_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['question_title'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🖼 لطفاً لینک تصویر سؤال را وارد کنید\n"
        "(اگر تصویر ندارد، عدد 0 را وارد کنید):",
        reply_markup=reply_markup
    )
    return QUESTION_IMAGE

# *************************************************************************************** Add Category Finish *****************************************
async def add_category_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    category_name = update.message.text
    session = Session()
    new_category = Category(name=category_name)
    session.add(new_category)
    session.commit()
    session.close()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ دسته‌بندی '{category_name}' با موفقیت اضافه شد.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# *************************************************************************************** Add Category Start *****************************************
async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 لطفاً نام دسته‌بندی جدید را وارد کنید:",
        reply_markup=reply_markup
    )
    return CATEGORY_NAME
# *************************************************************************************** Cancel ****************************************************
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات و برگشت به منوی اصلی"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "❌ عملیات لغو شد.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "❌ عملیات لغو شد.",
            reply_markup=reply_markup
        )
    return ConversationHandler.END
# *************************************************************************************** Create Exam Start *****************************************
async def create_exam_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 لطفاً عنوان آزمون را وارد کنید:",
        reply_markup=reply_markup
    )
    return EXAM_TITLE
# *************************************************************************************** Create Exam Title *****************************************
async def create_exam_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    context.user_data['exam_title'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💰 لطفاً قیمت آزمون را به تومان وارد کنید:\n"
        "(برای آزمون رایگان عدد 0 را وارد کنید)",
        reply_markup=reply_markup
    )
    return EXAM_PRICE
# *************************************************************************************** Create Exam Price *****************************************
async def create_exam_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    try:
        price = int(update.message.text)
        if price < 0:
            raise ValueError
        context.user_data['exam_price'] = price
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد صحیح مثبت وارد کنید.")
        return EXAM_PRICE
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔢 لطفاً تعداد سؤالات آزمون را وارد کنید:",
        reply_markup=reply_markup
    )
    return EXAM_QUESTION_COUNT
# *************************************************************************************** Create Exam Question Count *****************************************
async def create_exam_question_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    try:
        question_count = int(update.message.text)
        if question_count <= 0:
            raise ValueError
        context.user_data['question_count'] = question_count
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد صحیح مثبت وارد کنید.")
        return EXAM_QUESTION_COUNT
    
    session = Session()
    categories = session.query(Category).all()
    session.close()
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            category.name, 
            callback_data=f'ecat_{category.id}'
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📂 لطفاً دسته‌بندی آزمون را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return EXAM_CATEGORY
# *************************************************************************************** Create Exam Finish *****************************************
async def create_exam_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'admin_menu':
        return await back_to_admin(update, context)
        
    category_id = int(query.data.split('_')[1])
    
    session = Session()
    # بررسی تعداد سؤالات موجود در دسته‌بندی
    available_questions = session.query(func.count(Question.id))\
        .filter_by(category_id=category_id)\
        .scalar()
    
    if available_questions < context.user_data['question_count']:
        await query.edit_message_text(
            f"❌ تعداد سؤالات موجود در این دسته‌بندی ({available_questions} سؤال) "
            f"کمتر از تعداد درخواستی ({context.user_data['question_count']} سؤال) است.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')
            ]])
        )
        session.close()
        return ConversationHandler.END
    
    # ایجاد آزمون جدید
    new_exam = Exam(
        title=context.user_data['exam_title'],
        price=context.user_data['exam_price'],
        question_count=context.user_data['question_count'],
        category_id=category_id
    )
    session.add(new_exam)
    session.commit()
    
    # انتخاب تصادفی سؤالات
    questions = session.query(Question)\
        .filter_by(category_id=category_id)\
        .order_by(func.random())\
        .limit(context.user_data['question_count'])\
        .all()
    
    # اضافه کردن سؤالات به آزمون
    for question in questions:
        exam_question = ExamQuestion(
            exam_id=new_exam.id,
            question_id=question.id
        )
        session.add(exam_question)
    
    session.commit()
    session.close()
    
    # پاک کردن داده‌های ذخیره شده
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ آزمون با موفقیت ایجاد شد.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# *************************************************************************************** Show Categories *****************************************
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    session = Session()
    categories = session.query(Category).all()
    
    if not categories:
        await query.edit_message_text(
            "❌ هیچ دسته‌بندی موجود نیست.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='start')
            ]])
        )
        session.close()
        return
    
    keyboard = []
    # نمایش آزمون‌های هر دسته
    for category in categories:
        exams = session.query(Exam).filter_by(category_id=category.id).count()
        keyboard.append([InlineKeyboardButton(
            f"📚 {category.name} ({exams} آزمون)",
            callback_data=f'category_{category.id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='start')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 دسته‌بندی‌های موجود:",
        reply_markup=reply_markup
    )
    session.close()
# *************************************************************************************** Show Category Exam *****************************************
async def show_category_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split('_')[1])
    
    session = Session()
    category = session.query(Category).get(category_id)
    exams = session.query(Exam).filter_by(category_id=category_id).all()
    
    if not exams:
        await query.edit_message_text(
            f"❌ هیچ آزمونی در دسته‌بندی {category.name} موجود نیست.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data='show_categories')
            ]])
        )
        session.close()
        return
    
    keyboard = []
    for exam in exams:
        price_text = f"{exam.price:,} تومان" if exam.price > 0 else "رایگان"
        keyboard.append([InlineKeyboardButton(
            f"📝 {exam.title} ({price_text})",
            callback_data=f'exam_{exam.id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data='show_categories')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📚 آزمون‌های دسته‌بندی {category.name}:",
        reply_markup=reply_markup
    )
    session.close()

