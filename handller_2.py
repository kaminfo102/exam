# *************************************************************************************** Continue Exam *****************************************
from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes
from database import Session
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
