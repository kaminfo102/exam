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

from handller import add_question_image,add_question_option_a,add_question_option_b,add_question_option_c,add_question_option_d,add_question_correct,add_question_category
# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
(CATEGORY_NAME, 
 QUESTION_TITLE, QUESTION_IMAGE, QUESTION_OPTION_A, QUESTION_OPTION_B, 
 QUESTION_OPTION_C, QUESTION_OPTION_D, QUESTION_CORRECT, QUESTION_CATEGORY,
 EXAM_TITLE, EXAM_PRICE, EXAM_QUESTION_COUNT, EXAM_CATEGORY) = range(13)

#****************************   ADMIN CONTROLLER ********************************************
def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("⛔️ شما دسترسی به این عملکرد را ندارید.")
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapped

# *************************************************************************************** Help Command *****************************************

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    دستورات موجود:
    /start - شروع کار با ربات
    /help - نمایش این پیام راهنما
    /exams - مشاهده لیست آزمون‌های موجود
    /profile - مشاهده پروفایل کاربری
    """
    await update.message.reply_text(help_text)



# ******************************************************  Start (Main Menu) *********************************************************************
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 مشاهده دسته‌بندی‌ها", callback_data='show_categories')],
        [InlineKeyboardButton("🎯 آزمون‌های من", callback_data='my_exams')],
        [InlineKeyboardButton("🎯 پنل مدیریت", callback_data='admin_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎓 به ربات آزمون آنلاین خوش آمدید!\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🎓 به ربات آزمون آنلاین خوش آمدید!\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )

    query = update.callback_query
    await query.answer()
    
    # همه دکمه‌ها به منوی اصلی برمی‌گردند
    await start(update, context)
    query = update.callback_query
    await query.answer()

    if query.data == 'show_categories':
        await show_categories(update, context)
    elif query.data == 'my_exams':
        await show_my_exams(update, context)
    elif query.data == 'admin_menu':
        await show_admin_menu(update, context)
    elif query.data == 'back':
        await start(update, context)
    query = update.callback_query
    await query.answer()

    if query.data == 'show_categories':
        await show_categories(update, context)
    elif query.data == 'my_exams':
        await show_my_exams(update, context)
    elif query.data == 'admin_menu':
        await show_admin_menu(update, context)
    elif query.data == 'back':
        await start(update, context)
    query = update.callback_query
    await query.answer()

    # حذف پیام قبلی
    await query.message.delete()

    if query.data == 'show_categories':
        await show_categories(update, context)
    elif query.data == 'my_exams':
        await show_my_exams(update, context)
    elif query.data == 'admin_menu':
        await show_admin_menu(update, context)
    elif query.data == 'back':
        await start(update, context)
    try:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    except:
        try:
            await update.callback_query.edit_message_caption(caption=text, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(text=text, reply_markup=reply_markup)
    query = update.callback_query
    await query.answer()

    if query.data == 'show_categories':
        await show_categories(update, context)
    elif query.data == 'my_exams':
        await show_my_exams(update, context)
    elif query.data == 'admin_menu':
        await show_admin_menu(update, context)
    elif query.data == 'back':
        await start(update, context)
    else:
        await query.edit_message_text("گزینه نامعتبر. لطفاً دوباره تلاش کنید.")
    query = update.callback_query
    await query.answer()

    if query.data == 'show_categories':
        keyboard = [
            [InlineKeyboardButton("ریاضی", callback_data='math')],
            [InlineKeyboardButton("فیزیک", callback_data='physics')],
            [InlineKeyboardButton("شیمی", callback_data='chemistry')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📚 لطفاً دسته‌بندی مورد نظر خود را انتخاب کنید:"
    
    elif query.data == 'my_exams':
        keyboard = [
            [InlineKeyboardButton("آزمون‌های فعال", callback_data='active_exams')],
            [InlineKeyboardButton("تاریخچه آزمون‌ها", callback_data='exam_history')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "🎯 بخش آزمون‌های من:\nلطفاً یک گزینه را انتخاب کنید:"
    
    elif query.data == 'admin_menu':
        keyboard = [
            [InlineKeyboardButton("افزودن آزمون", callback_data='add_exam')],
            [InlineKeyboardButton("مدیریت آزمون‌ها", callback_data='manage_exams')],
            [InlineKeyboardButton("گزارش‌ها", callback_data='reports')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "🎯 پنل مدیریت:\nلطفاً یک گزینه را انتخاب کنید:"
    
    elif query.data == 'back':
        return await start(update, context)
    
    else:
        message_text = "گزینه نامعتبر. لطفاً دوباره تلاش کنید."
        reply_markup = None

    try:
        # ابتدا سعی می‌کنیم متن را ویرایش کنیم
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)
    except telegram.error.BadRequest:
        try:
            # اگر نتوانستیم متن را ویرایش کنیم، سعی می‌کنیم کپشن تصویر را ویرایش کنیم
            await query.edit_message_caption(caption=message_text, reply_markup=reply_markup)
        except telegram.error.BadRequest:
            # اگر هیچ کدام کار نکرد، یک پیام جدید ارسال می‌کنیم
            await query.message.reply_text(text=message_text, reply_markup=reply_markup)
            await query.message.delete()

# *************************************************************************************** Show Admin Menu ***************************************** 
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

# *************************************************************************************** Admin Start *****************************************
@admin_only
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_admin_menu(update, context)

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
# *************************************************************************************** Back To Admin *****************************************
async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await show_admin_menu(update, context)
        return ConversationHandler.END
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
# *************************************************************************************** Cancel *****************************************
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

# *************************************************************************************** Add Question Image *****************************************
# async def add_question_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.callback_query and update.callback_query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     context.user_data['question_image'] = update.message.text
    
#     keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "📝 لطفاً گزینه A را وارد کنید:",
#         reply_markup=reply_markup
#     )
#     return QUESTION_OPTION_A
# # *************************************************************************************** Add Question Option A *****************************************
# async def add_question_option_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.callback_query and update.callback_query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     context.user_data['option_a'] = update.message.text
    
#     keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "📝 لطفاً گزینه B را وارد کنید:",
#         reply_markup=reply_markup
#     )
#     return QUESTION_OPTION_B
# # *************************************************************************************** Add Question Option B *****************************************
# async def add_question_option_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.callback_query and update.callback_query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     context.user_data['option_b'] = update.message.text
    
#     keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "📝 لطفاً گزینه C را وارد کنید:",
#         reply_markup=reply_markup
#     )
#     return QUESTION_OPTION_C
# # *************************************************************************************** Add Question Option C *****************************************
# async def add_question_option_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.callback_query and update.callback_query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     context.user_data['option_c'] = update.message.text
    
#     keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "📝 لطفاً گزینه D را وارد کنید:",
#         reply_markup=reply_markup
#     )
#     return QUESTION_OPTION_D
# # *************************************************************************************** Add Question Option D *****************************************
# async def add_question_option_d(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.callback_query and update.callback_query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     context.user_data['option_d'] = update.message.text
    
#     keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "📝 لطفاً گزینه صحیح را وارد کنید (A, B, C یا D):",
#         reply_markup=reply_markup
#     )
#     return QUESTION_CORRECT
# # *************************************************************************************** Add Question Currect *****************************************
# async def add_question_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.callback_query and update.callback_query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     correct_answer = update.message.text.upper()
#     if correct_answer not in ['A', 'B', 'C', 'D']:
#         await update.message.reply_text("❌ لطفاً یکی از گزینه‌های A، B، C یا D را وارد کنید.")
#         return QUESTION_CORRECT
        
#     context.user_data['correct_answer'] = correct_answer
    
#     session = Session()
#     categories = session.query(Category).all()
#     session.close()
    
#     keyboard = []
#     for category in categories:
#         keyboard.append([InlineKeyboardButton(
#             category.name, 
#             callback_data=f'qcat_{category.id}'
#         )])
#     keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')])
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "📂 لطفاً دسته‌بندی سؤال را انتخاب کنید:",
#         reply_markup=reply_markup
#     )
#     return QUESTION_CATEGORY
# # *************************************************************************************** Add Question Category *****************************************
# async def add_question_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     if query.data == 'admin_menu':
#         return await back_to_admin(update, context)
        
#     category_id = int(query.data.split('_')[1])
    
#     session = Session()
#     new_question = Question(
#         title=context.user_data['question_title'],
#         image_url=context.user_data['question_image'] if context.user_data['question_image'] != '0' else None,
#         option_a=context.user_data['option_a'],
#         option_b=context.user_data['option_b'],
#         option_c=context.user_data['option_c'],
#         option_d=context.user_data['option_d'],
#         correct_answer=context.user_data['correct_answer'],
#         category_id=category_id
#     )
#     session.add(new_question)
#     session.commit()
#     session.close()
    
#     # پاک کردن داده‌های ذخیره شده
#     context.user_data.clear()
    
#     keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data='admin_menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await query.edit_message_text(
#         "✅ سؤال با موفقیت اضافه شد.",
#         reply_markup=reply_markup
#     )
#     return ConversationHandler.END

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
# *************************************************************************************** Show My Exam *****************************************
async def show_my_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    session = Session()
    user_exams = session.query(UserExam).filter_by(user_id=user_id).all()
    
    if not user_exams:
        await query.edit_message_text(
            "❌ شما هنوز در هیچ آزمونی شرکت نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='start')
            ]])
        )
        session.close()
        return
    
    keyboard = []
    for user_exam in user_exams:
        exam = session.query(Exam).get(user_exam.exam_id)
        if exam:
            status = "✅ تکمیل شده" if user_exam.is_finished else "⏳ در حال انجام"
            score_text = f" - نمره: {user_exam.score}" if user_exam.is_finished else ""
            keyboard.append([InlineKeyboardButton(
                f"📝 {exam.title} ({status}){score_text}",
                callback_data=f'exam_{user_exam.id}'
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='start')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎯 آزمون‌های شما:",
        reply_markup=reply_markup
    )
    session.close()

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

# *************************************************************************************** Show Exam Detail *****************************************
# async def show_exam_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     parts = query.data.split('_')
#     if parts[0] == 'exam':
#         if len(parts) > 2 and parts[1] == 'payment':
#             exam_id = int(parts[2])
#             return await show_payment_options(update, context)
#         else:
#             exam_id = int(parts[1])
#     else:
#         await query.edit_message_text("خطا: داده‌ی نامعتبر")
#         return

#     session = Session()
#     exam = session.query(Exam).get(exam_id)
    
#     if not exam:
#         await query.edit_message_text("❌ آزمون مورد نظر یافت نشد.")
#         session.close()
#         return
    
#     price_text = f"{exam.price:,} تومان" if exam.price > 0 else "رایگان"
#     exam_info = (
#         f"📝 عنوان آزمون: {exam.title}\n"
#         f"💰 قیمت: {price_text}\n"
#     )
    
#     # اضافه کردن اطلاعات اضافی در صورت وجود
#     if hasattr(exam, 'duration'):
#         exam_info += f"⏱ مدت زمان: {exam.duration} دقیقه\n"
#     if hasattr(exam, 'question_count'):
#         exam_info += f"❓ تعداد سوالات: {exam.question_count}\n"
#     if hasattr(exam, 'description'):
#         exam_info += f"\n📜 توضیحات:\n{exam.description}"
    
#     keyboard = []
#     if exam.price > 0:
#         keyboard.append([InlineKeyboardButton("💳 پرداخت و شروع آزمون", callback_data=f'exam_payment_{exam_id}')])
#     else:
#         keyboard.append([InlineKeyboardButton("▶️ شروع آزمون", callback_data=f'start_exam_{exam_id}')])
    
#     keyboard.append([InlineKeyboardButton("🔙 بازگشت به لیست آزمون‌ها", callback_data=f'category_{exam.category_id}')])
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await query.edit_message_text(exam_info, reply_markup=reply_markup)
#     session.close()  
     

async def show_exam_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    exam_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    session = Session()
    exam = session.query(Exam).get(exam_id)
    
    if not exam:
        await query.edit_message_text(
            "❌ آزمون مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='show_categories')
            ]])
        )
        session.close()
        return

    # بررسی آزمون‌های قبلی کاربر
    existing_exam = session.query(UserExam).filter_by(
        user_id=user_id,
        exam_id=exam_id
    ).first()
    
    keyboard = []
    if existing_exam:
        if existing_exam.is_finished:
            score_text = f"\nنمره شما: {existing_exam.score}"
            keyboard.append([InlineKeyboardButton("📊 مشاهده جزئیات", callback_data=f'result_{existing_exam.id}')])
        else:
            score_text = "\n⏳ آزمون ناتمام"
            keyboard.append([InlineKeyboardButton("▶️ ادامه آزمون", callback_data=f'continue_{existing_exam.id}')])
    else:
        score_text = ""
        if exam.price > 0:
            keyboard.append([InlineKeyboardButton("💳 پرداخت و شروع آزمون", callback_data=f'pay_{exam_id}')])
        else:
            keyboard.append([InlineKeyboardButton("▶️ شروع آزمون", callback_data=f'start_exam_{exam_id}')])

    category = session.query(Category).get(exam.category_id)
    price_text = f"{exam.price:,} تومان" if exam.price > 0 else "رایگان"
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'category_{exam.category_id}')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📝 {exam.title}\n"
        f"📚 دسته‌بندی: {category.name}\n"
        f"💰 قیمت: {price_text}\n"
        f"❓ تعداد سؤالات: {exam.question_count}{score_text}",
        reply_markup=reply_markup
    )
    session.close()

# *************************************************************************************** Start Exam *****************************************
async def start_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    exam_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    session = Session()
    exam = session.query(Exam).get(exam_id)
    
    if not exam:
        await query.edit_message_text("❌ آزمون مورد نظر یافت نشد.")
        session.close()
        return
        
    # ایجاد رکورد جدید برای آزمون کاربر
    user_exam = UserExam(
        user_id=user_id,
        exam_id=exam_id,
        current_question=0,
        answers="",
        is_finished=False,
        score=0
    )
    session.add(user_exam)
    session.commit()
    
    # نمایش اولین سؤال
    await show_question(query, user_exam.id, session)
    session.close()
# *************************************************************************************** Continue Exam *****************************************
async def continue_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_exam_id = int(query.data.split('_')[1])
    
    session = Session()
    user_exam = session.query(UserExam).get(user_exam_id)
    
    if not user_exam or user_exam.is_finished:
        await query.edit_message_text("❌ آزمون مورد نظر یافت نشد یا به پایان رسیده است.")
        session.close()
        return
        
    # نمایش سؤال فعلی
    await show_question(query, user_exam_id, session)
    session.close()
# *************************************************************************************** Show Question *****************************************
async def show_question(query: CallbackQuery, user_exam_id: int, session: Session):
    user_exam = session.query(UserExam).get(user_exam_id)
    exam = session.query(Exam).get(user_exam.exam_id)
    
    # دریافت سؤالات آزمون
    exam_questions = session.query(ExamQuestion).filter_by(exam_id=exam.id).all()
    if user_exam.current_question >= len(exam_questions):
        await finish_exam(query, user_exam_id, session)
        return
        
    # دریافت سؤال فعلی
    current_exam_question = exam_questions[user_exam.current_question]
    question = session.query(Question).get(current_exam_question.question_id)
    
    # ساخت دکمه‌های گزینه‌ها
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f'ans_{user_exam_id}_A'),
         InlineKeyboardButton("B", callback_data=f'ans_{user_exam_id}_B'),
         InlineKeyboardButton("C", callback_data=f'ans_{user_exam_id}_C'),
         InlineKeyboardButton("D", callback_data=f'ans_{user_exam_id}_D')]
    ]
    
    # نمایش متن سؤال و گزینه‌ها
    question_text = (
        f"❓ سؤال {user_exam.current_question + 1} از {exam.question_count}:\n\n"
        f"{question.title}\n\n"
        f"🅱️{question.option_a}\n"
        f"🅱️ {question.option_b}\n"
        f"🅱️{question.option_c}\n"
        f"🆔 {question.option_d}"
    )
    
    # اگر سؤال تصویر دارد
    if question.image_url:
        question_text = f"{question_text}\n\n🖼 تصویر سؤال: {question.image_url}"
    
    await query.edit_message_text(
        question_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# *************************************************************************************** Handel Answer *****************************************
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_exam_id, answer = query.data.split('_')[1:]
    
    session = Session()
    user_exam = session.query(UserExam).get(int(user_exam_id))
    
    if not user_exam or user_exam.is_finished:
        await query.edit_message_text("❌ آزمون مورد نظر یافت نشد یا به پایان رسیده است.")
        session.close()
        return
    
    # ذخیره پاسخ
    user_exam.answers += answer
    user_exam.current_question += 1
    session.commit()
    
    # نمایش سؤال بعدی
    await show_question(query, int(user_exam_id), session)
    session.close()
# *************************************************************************************** Finish Exam *****************************************
async def finish_exam(query: CallbackQuery, user_exam_id: int, session: Session):
    user_exam = session.query(UserExam).get(user_exam_id)
    exam = session.query(Exam).get(user_exam.exam_id)
    
    # محاسبه نمره
    exam_questions = session.query(ExamQuestion).filter_by(exam_id=exam.id).all()
    correct_answers = 0
    
    for i, eq in enumerate(exam_questions):
        question = session.query(Question).get(eq.question_id)
        if i < len(user_exam.answers) and user_exam.answers[i] == question.correct_answer:
            correct_answers += 1
    
    score = (correct_answers / len(exam_questions)) * 100
    user_exam.score = round(score, 2)
    user_exam.is_finished = True
    session.commit()
    
    await query.edit_message_text(
        f"✅ آزمون به پایان رسید!\n\n"
        f"📊 نتیجه آزمون:\n"
        f"✓ پاسخ‌های صحیح: {correct_answers}\n"
        f"✗ پاسخ‌های غلط: {len(exam_questions) - correct_answers}\n"
        f"📈 نمره نهایی: {user_exam.score}%",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔍 مشاهده جزئیات", callback_data=f'result_{user_exam_id}'),
            InlineKeyboardButton("🏠 بازگشت به منو", callback_data='start')
        ]])
    )
# *************************************************************************************** Show Exam Result *****************************************
async def show_exam_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_exam_id = int(query.data.split('_')[1])
    
    session = Session()
    user_exam = session.query(UserExam).get(user_exam_id)
    
    if not user_exam or not user_exam.is_finished:
        await query.edit_message_text("❌ نتیجه آزمون یافت نشد.")
        session.close()
        return
    
    exam = session.query(Exam).get(user_exam.exam_id)
    exam_questions = session.query(ExamQuestion).filter_by(exam_id=exam.id).all()
    
    result_text = f"📊 نتایج تفصیلی آزمون {exam.title}\n\n"
    
    for i, eq in enumerate(exam_questions):
        question = session.query(Question).get(eq.question_id)
        user_answer = user_exam.answers[i] if i < len(user_exam.answers) else '-'
        is_correct = user_answer == question.correct_answer
        
        result_text += (
            f"سؤال {i+1}:\n"
            f"پاسخ شما: {user_answer}\n"
            f"پاسخ صحیح: {question.correct_answer}\n"
            f"{'✅ صحیح' if is_correct else '❌ غلط'}\n\n"
        )
    
    result_text += f"📈 نمره نهایی: {user_exam.score}%"
    
    # اگر متن نتیجه خیلی طولانی است، آن را تقسیم می‌کنیم
    if len(result_text) > 4096:
        parts = [result_text[i:i+4096] for i in range(0, len(result_text), 4096)]
        for i, part in enumerate(parts):
            if i == 0:
                await query.edit_message_text(
                    part,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data='start')
                    ]])
                )
            else:
                await query.message.reply_text(part)
    else:
        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='start')
            ]])
        )
    
    session.close()

# *************************************************************************************** Main *****************************************


   


async def show_bank_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    exam_id = int(query.data.split('_')[2])
    
    session = Session()
    exam = session.query(Exam).get(exam_id)
    
    bank_account = "شماره حساب: IR123456789012345678901234"  # جایگزین با شماره حساب واقعی
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به گزینه‌های پرداخت", callback_data=f'exam_payment_{exam_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"برای پرداخت هزینه آزمون «{exam.title}»، لطفاً مبلغ {exam.price:,} تومان را به حساب زیر واریز کنید:\n\n"
        f"{bank_account}\n\n"
        "پس از واریز، لطفاً تصویر فیش واریزی را به پشتیبانی ارسال کنید.",
        reply_markup=reply_markup
    )
    session.close()

  
async def show_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 3 or parts[0] != 'exam' or parts[1] != 'payment':
        await query.edit_message_text("خطا: داده‌ی نامعتبر")
        return
    
    exam_id = int(parts[2])
    
    session = Session()
    exam = session.query(Exam).get(exam_id)
    
    if not exam:
        await query.edit_message_text("❌ آزمون مورد نظر یافت نشد.")
        session.close()
        return
    
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data=f'online_payment_{exam_id}')],
        [InlineKeyboardButton("🏦 پرداخت واریز به حساب", callback_data=f'bank_transfer_{exam_id}')],
        [InlineKeyboardButton("🔙 بازگشت به جزئیات آزمون", callback_data=f'exam_{exam_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"لطفاً روش پرداخت برای آزمون «{exam.title}» را انتخاب کنید:\n"
        f"مبلغ قابل پرداخت: {exam.price:,} تومان",
        reply_markup=reply_markup
    )
    session.close()
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    
    # Add conversation handlers for admin operations
    add_category_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_category_start, pattern='^add_category$')],
        states={
            CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_finish),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
        ]
    )
    
    add_question_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_question_start, pattern='^add_question$')],
        states={
            QUESTION_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_title),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_IMAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_image),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_OPTION_A: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_option_a),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_OPTION_B: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_option_b),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_OPTION_C: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_option_c),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_OPTION_D: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_option_d),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_CORRECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_correct),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            QUESTION_CATEGORY: [
                CallbackQueryHandler(add_question_category, pattern='^qcat_'),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
        ]
    )
    
       
    create_exam_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_exam_start, pattern='^create_exam$')],
        states={
            EXAM_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_exam_title),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            EXAM_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_exam_price),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            EXAM_QUESTION_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_exam_question_count),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ],
            EXAM_CATEGORY: [
                CallbackQueryHandler(create_exam_finish, pattern='^ecat_'),
                CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_admin, pattern='^admin_menu$')
        ]
    )
    

    
  

    
   

 
      
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_start))
    application.add_handler(CallbackQueryHandler(start, pattern='^start$'))
    application.add_handler(CallbackQueryHandler(show_admin_menu, pattern='^admin_menu$'))
    application.add_handler(add_category_handler)
    application.add_handler(add_question_handler)
    application.add_handler(create_exam_handler)
    
    application.add_handler(CallbackQueryHandler(show_categories, pattern='^show_categories$'))
    application.add_handler(CallbackQueryHandler(show_category_exams, pattern='^category_'))
    application.add_handler(CallbackQueryHandler(show_my_exams, pattern='^my_exams$'))
    
    application.add_handler(CallbackQueryHandler(show_exam_details, pattern='^exam_'))
    application.add_handler(CallbackQueryHandler(start_exam, pattern='^start_exam_'))
    application.add_handler(CallbackQueryHandler(continue_exam, pattern='^continue_'))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern='^ans_'))
    application.add_handler(CallbackQueryHandler(show_exam_result, pattern='^result_'))
    application.add_handler(CommandHandler("help", help_command))
    
    application.add_handler(CallbackQueryHandler(show_payment_options, pattern='^pay_'))
    application.add_handler(CallbackQueryHandler(show_bank_account, pattern='^bank_transfer_'))
    
    
    application.add_handler(CallbackQueryHandler(show_category_exams, pattern=r'^category_'))
    application.add_handler(CallbackQueryHandler(show_exam_details, pattern=r'^exam_'))
    application.add_handler(CallbackQueryHandler(show_payment_options, pattern=r'^exam_payment_'))
    application.add_handler(CallbackQueryHandler(show_bank_account, pattern=r'^bank_transfer_'))
    
 
    
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()