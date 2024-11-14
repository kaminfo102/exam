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
from handller_2 import (continue_exam,show_question,handle_answer,finish_exam,show_exam_result,show_bank_account,show_payment_options)
from handller import (add_question_image,add_question_option_a,add_question_option_b,add_question_option_c,add_question_option_d,add_question_correct,add_question_category,admin_only,show_admin_menu,back_to_admin
      ,add_question_title,add_question_start,show_category_exams,show_categories,create_exam_finish,create_exam_question_count,create_exam_price,create_exam_title,
      create_exam_start,cancel,add_category_finish,add_category_start,add_question_category,admin_start)

from datetime import datetime
import json
from sqlalchemy.exc import SQLAlchemyError
from database import UserExam, Exam, Question, Payment
from database import Session
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

# *************************************************************************************** Start Exam Again *****************************************
async def start_exam_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        exam_id = int(query.data.split('_')[2])
        user_id = update.effective_user.id
        
        with Session() as session:
            # چاپ برای دیباگ
            logging.info(f"Starting exam with ID: {exam_id} for user: {user_id}")
            
            exam = session.get(Exam, exam_id)
            if not exam:
                logging.error(f"Exam not found with ID: {exam_id}")
                await query.edit_message_text(
                    "❌ آزمون مورد نظر یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
                    ]])
                )
                return

            # بررسی تعداد سوالات موجود
            questions_count = session.query(Question).filter_by(exam_id=exam_id).count()
            logging.info(f"Found {questions_count} questions for exam {exam_id}")

            # دریافت تمام سوالات برای دیباگ
            all_questions = session.query(Question).filter_by(exam_id=exam_id).all()
            for q in all_questions:
                logging.info(f"Question ID: {q.id}, Exam ID: {q.exam_id}, Text: {q.text[:50]}...")

            if exam.price > 0:
                payment = session.query(Payment).filter_by(
                    user_id=user_id,
                    exam_id=exam_id,
                    status='completed'
                ).first()
                
                if not payment:
                    await query.edit_message_text(
                        "⚠️ برای شرکت در این آزمون باید هزینه آن را پرداخت کنید.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("💳 پرداخت", callback_data=f'pay_{exam_id}'),
                            InlineKeyboardButton("🔙 بازگشت", callback_data=f'exam_detail_{exam_id}')
                        ]])
                    )
                    return

            # تغییر در نحوه دریافت اولین سوال و اضافه کردن لاگ
            first_question = (
                session.query(Question)
                .filter(Question.exam_id == exam_id)
                .order_by(Question.id)
                .first()
            )
            
            logging.info(f"First question query result: {first_question}")

            if not first_question:
                logging.error(f"No questions found for exam {exam_id}")
                await query.edit_message_text(
                    "❌ سوالی برای این آزمون تعریف نشده است.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f'exam_detail_{exam_id}')
                    ]])
                )
                return

            new_user_exam = UserExam(
                user_id=user_id,
                exam_id=exam_id,
                start_time=datetime.now(),
                current_question=1,
                is_finished=False,
                score=0
            )
            session.add(new_user_exam)
            session.flush()
            
            keyboard = []
            options = json.loads(first_question.options)
            for idx, option in enumerate(options, 1):
                keyboard.append([
                    InlineKeyboardButton(
                        f"{idx}. {option}",
                        callback_data=f'answer_{new_user_exam.id}_{first_question.id}_{idx}'
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("🚫 انصراف", callback_data=f'cancel_exam_{new_user_exam.id}')
            ])

            session.commit()

            await query.edit_message_text(
                f"📝 سوال {1} از {exam.question_count}\n\n"
                f"{first_question.text}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except ValueError as ve:
        logging.error(f"Value Error in start_exam_again: {str(ve)}")
        await query.edit_message_text(
            "❌ داده‌های نامعتبر. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
            ]])
        )
    except SQLAlchemyError as se:
        logging.error(f"Database Error in start_exam_again: {str(se)}")
        await query.edit_message_text(
            "❌ خطای پایگاه داده. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
            ]])
        )
    except Exception as e:
        logging.error(f"Error in start_exam_again: {str(e)}")
        logging.error(traceback.format_exc())
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
            ]])
        )

# *************************************************************************************** Show My Exam *****************************************
async def show_my_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = Session()
    
    try:
        user_exams = (
            session.query(
                UserExam.exam_id,
                func.max(UserExam.id).label('latest_attempt'),
                func.count(UserExam.id).label('attempt_count')
            )
            .filter(UserExam.user_id == user_id)
            .group_by(UserExam.exam_id)
            .all()
        )

        if not user_exams:
            await query.edit_message_text(
                "❌ شما هنوز در هیچ آزمونی شرکت نکرده‌اید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data='start')
                ]])
            )
            return

        keyboard = []
        for exam_info in user_exams:
            latest_attempt = (
                session.query(UserExam)
                .filter(UserExam.id == exam_info.latest_attempt)
                .first()
            )
            
            exam = session.query(Exam).get(exam_info.exam_id)
            
            if not exam or not latest_attempt:
                continue

            status = "✅ تکمیل شده" if latest_attempt.is_finished else "⏳ ناتمام"
            score_text = f" - نمره: {latest_attempt.score}%" if latest_attempt.is_finished else ""
            
            exam_text = (
                f"📝 {exam.title} | {status}{score_text}\n"
                f"🔄 تعداد تلاش: {exam_info.attempt_count}"
            )
            
            # ساده‌سازی callback_data
            keyboard.append([
                InlineKeyboardButton(
                    exam_text,
                    callback_data=f'exam_detail_{exam.id}'  # تغییر فرمت به ساده‌تر
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='start')])
        
        await query.edit_message_text(
            "🎯 لیست آزمون‌های شما:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(f"Error in show_my_exams for user {user_id}: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='start')
            ]])
        )
    finally:
        session.close()

# *************************************************************************************** Show Exam Detail *****************************************
async def show_exam_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        # اصلاح پردازش callback_data
        callback_data = query.data
        logging.info(f"Received callback_data: {callback_data}")  # برای دیباگ
        
        # روش جدید و امن‌تر برای استخراج exam_id
        if '_detail_' in callback_data:
            exam_id = int(callback_data.split('_detail_')[1])
        else:
            raise ValueError("Invalid callback data format")
            
        logging.info(f"Extracted exam_id: {exam_id}")  # برای دیباگ
        
        user_id = update.effective_user.id
        
        session = Session()
        try:
            exam = session.query(Exam).get(exam_id)
            
            if not exam:
                await query.edit_message_text(
                    "❌ آزمون مورد نظر یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
                    ]])
                )
                return

            existing_exam = (
                session.query(UserExam)
                .filter_by(user_id=user_id, exam_id=exam_id)
                .order_by(UserExam.id.desc())
                .first()
            )
            
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
            
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')])
            
            await query.edit_message_text(
                f"📝 {exam.title}\n"
                f"📚 دسته‌بندی: {category.name}\n"
                f"💰 قیمت: {price_text}\n"
                f"❓ تعداد سؤالات: {exam.question_count}"
                f"{attempts_text}"
                f"{score_text}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        finally:
            session.close()
            
    except ValueError as ve:
        logging.error(f"ValueError in show_exam_details: {str(ve)}")
        await query.edit_message_text(
            "❌ داده‌های نامعتبر. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
            ]])
        )
    except Exception as e:
        logging.error(f"Error in show_exam_details: {str(e)}")
        logging.error(f"Full callback_data: {query.data}")  # اضافه کردن لاگ بیشتر
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data='my_exams')
            ]])
        )

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
    # application.add_handler(CallbackQueryHandler(show_my_exams, pattern='^my_exams$'))
    
    # application.add_handler(CallbackQueryHandler(show_exam_details, pattern='^exam_'))
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
    
    application.add_handler(CallbackQueryHandler(show_my_exams, pattern='^my_exams$'))
    application.add_handler(CallbackQueryHandler(show_exam_details, pattern='^exam_detail_'))
    
 
    
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()