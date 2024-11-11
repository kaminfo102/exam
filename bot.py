import traceback
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

from handller import (add_question_image,add_question_option_a,add_question_option_b,add_question_option_c,add_question_option_d,add_question_correct,add_question_category,admin_only,show_admin_menu,back_to_admin
      ,add_question_title,add_question_start,show_category_exams,show_categories,create_exam_finish,create_exam_question_count,create_exam_price,create_exam_title,
      create_exam_start,cancel,add_category_finish,add_category_start)


# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
(CATEGORY_NAME, 
 QUESTION_TITLE, QUESTION_IMAGE, QUESTION_OPTION_A, QUESTION_OPTION_B, 
 QUESTION_OPTION_C, QUESTION_OPTION_D, QUESTION_CORRECT, QUESTION_CATEGORY,
 EXAM_TITLE, EXAM_PRICE, EXAM_QUESTION_COUNT, EXAM_CATEGORY) = range(13)



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


# *************************************************************************************** Admin Start *****************************************
@admin_only
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_admin_menu(update, context)

# *************************************************************************************** Show My Exam *****************************************
async def show_my_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        with Session() as session:
            user_exams = session.query(UserExam).filter_by(user_id=user_id).all()
            
            if not user_exams:
                await query.edit_message_text(
                    "❌ شما هنوز در هیچ آزمونی شرکت نکرده‌اید.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data='start')
                    ]])
                )
                return
            
            keyboard = []
            for user_exam in user_exams:
                exam = session.query(Exam).get(user_exam.exam_id)
                if exam:
                    status = "✅ تکمیل شده" if user_exam.is_finished else "⏳ در حال انجام"
                    score_text = f" - نمره: {user_exam.score}" if user_exam.is_finished else ""
                    keyboard.append([InlineKeyboardButton(
                        f"📝 {exam.title} ({status}){score_text}",
                        callback_data=f'exam_{exam.id}'  # تغییر از user_exam.id به exam.id
                    )])
            
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='start')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🎯 آزمون‌های شما:",
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logging.error(f"Error in show_my_exams: {str(e)}")
        logging.error("Full traceback:", exc_info=True)
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='start')
            ]])
        )
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
# *************************************************************************************** Start Exam Again *****************************************
async def start_exam_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        exam_id = int(query.data.split('_')[2])
        user_id = update.effective_user.id
        
        with Session() as session:
            # ایجاد یک رکورد جدید در UserExam
            new_user_exam = UserExam(
                user_id=user_id,
                exam_id=exam_id,
                current_question=1,
                is_finished=False,
                score=0
            )
            session.add(new_user_exam)
            session.commit()
            
            # شروع آزمون جدید
            await show_question(update, context, new_user_exam.id, 1)
            
    except Exception as e:
        logging.error(f"Error in start_exam_again: {str(e)}")
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
            ]])
        ) 
# *************************************************************************************** Show Exam Detail *****************************************
# async def show_exam_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     exam_id = int(query.data.split('_')[1])
#     user_id = update.effective_user.id
    
#     session = Session()
#     exam = session.query(Exam).get(exam_id)
    
#     if not exam:
#         await query.edit_message_text(
#             "❌ آزمون مورد نظر یافت نشد.",
#             reply_markup=InlineKeyboardMarkup([[
#                 InlineKeyboardButton("🔙 بازگشت", callback_data='show_categories')
#             ]])
#         )
#         session.close()
#         return

#     # بررسی آزمون‌های قبلی کاربر
#     existing_exam = session.query(UserExam).filter_by(
#         user_id=user_id,
#         exam_id=exam_id
#     ).first()
    
#     keyboard = []
#     if existing_exam:
#         if existing_exam.is_finished:
#             score_text = f"\nنمره شما: {existing_exam.score}"
#             keyboard.append([InlineKeyboardButton("🔄 شرکت مجدد در آزمون", callback_data=f'start_exam_{exam_id}')])
#             keyboard.append([InlineKeyboardButton("📊 مشاهده جزئیات", callback_data=f'result_{existing_exam.id}')])
#         else:
#             score_text = "\n⏳ آزمون ناتمام"
#             keyboard.append([InlineKeyboardButton("▶️ ادامه آزمون", callback_data=f'continue_{existing_exam.id}')])
#     else:
#         score_text = ""
#         if exam.price > 0:
#             keyboard.append([InlineKeyboardButton("💳 پرداخت و شروع آزمون", callback_data=f'pay_{exam_id}')])
#         else:
#             keyboard.append([InlineKeyboardButton("▶️ شروع آزمون", callback_data=f'start_exam_{exam_id}')])

#     category = session.query(Category).get(exam.category_id)
#     price_text = f"{exam.price:,} تومان" if exam.price > 0 else "رایگان"
    
#     keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'category_{exam.category_id}')])
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await query.edit_message_text(
#         f"📝 {exam.title}\n"
#         f"📚 دسته‌بندی: {category.name}\n"
#         f"💰 قیمت: {price_text}\n"
#         f"❓ تعداد سؤالات: {exam.question_count}{score_text}",
#         reply_markup=reply_markup
#     )
#     session.close()

async def show_exam_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    exam_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    session = Session()
    try:
        exam = session.query(Exam).get(exam_id)
        
        if not exam:
            await query.edit_message_text(
                "❌ آزمون مورد نظر یافت نشد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data='show_categories')
                ]])
            )
            return

        # دریافت آخرین تلاش کاربر با مرتب‌سازی بر اساس ID (به صورت نزولی)
        existing_exam = (
            session.query(UserExam)
            .filter_by(user_id=user_id, exam_id=exam_id)
            .order_by(UserExam.id.desc())
            .first()
        )
        
        # محاسبه تعداد دفعات شرکت در آزمون
        attempt_count = (
            session.query(UserExam)
            .filter_by(user_id=user_id, exam_id=exam_id)
            .count()
        )
        
        keyboard = []
        if existing_exam:
            if existing_exam.is_finished:
                score_text = f"\nنمره شما: {existing_exam.score}"
                keyboard.append([InlineKeyboardButton("🔄 شرکت مجدد در آزمون", callback_data=f'start_exam_{exam_id}')])
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
        attempts_text = f"\n🔄 تعداد دفعات شرکت: {attempt_count}" if attempt_count > 0 else ""
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'category_{exam.category_id}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📝 {exam.title}\n"
            f"📚 دسته‌بندی: {category.name}\n"
            f"💰 قیمت: {price_text}\n"
            f"❓ تعداد سؤالات: {exam.question_count}"
            f"{attempts_text}"
            f"{score_text}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logging.error(f"Error in show_exam_details: {str(e)}")
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='show_categories')
            ]])
        )
    finally:
        session.close()

# ***************************************************
async def create_exam_keyboard(exam, existing_exam=None):
    """ساخت کیبورد براساس وضعیت آزمون"""
    keyboard = []
    
    if existing_exam:
        if existing_exam.is_finished:
            keyboard.append([
                InlineKeyboardButton("📊 مشاهده جزئیات", 
                                   callback_data=f'result_{existing_exam.id}')
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("▶️ ادامه آزمون", 
                                   callback_data=f'continue_{existing_exam.id}')
            ])
    else:
        if exam.price > 0:
            keyboard.append([
                InlineKeyboardButton("💳 پرداخت و شروع آزمون", 
                                   callback_data=f'pay_{exam.id}')
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("▶️ شروع آزمون", 
                                   callback_data=f'start_exam_{exam.id}')
            ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", 
                           callback_data=f'category_{exam.category_id}')
    ])
    return keyboard

async def get_exam_status_text(existing_exam):
    """دریافت متن وضعیت آزمون"""
    if not existing_exam:
        return ""
    if existing_exam.is_finished:
        return f"\nنمره شما: {existing_exam.score}"
    return "\n⏳ آزمون ناتمام"

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
    # application.add_handler(CallbackQueryHandler(show_all_results, pattern='^all_results_'))
    
    application.add_handler(CallbackQueryHandler(show_payment_options, pattern='^pay_'))
    application.add_handler(CallbackQueryHandler(show_bank_account, pattern='^bank_transfer_'))
    
    
    application.add_handler(CallbackQueryHandler(show_category_exams, pattern=r'^category_'))
    application.add_handler(CallbackQueryHandler(show_exam_details, pattern=r'^exam_'))
    application.add_handler(CallbackQueryHandler(show_payment_options, pattern=r'^exam_payment_'))
    application.add_handler(CallbackQueryHandler(show_bank_account, pattern=r'^bank_transfer_'))
    application.add_handler(CallbackQueryHandler(start_exam_again, pattern='^start_exam_'))
    
 
    
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()