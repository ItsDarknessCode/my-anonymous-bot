# main.py — نسخه نهایی، تمیز و بدون دکمه اضافه
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "8282339421:AAF6FN0DLcVFrPemA-d3Qqsc0OFN_pUZVf4"
ADMIN_ID = 7356174425
CHANNEL_USERNAME = "@A_M_N_2025"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
logging.basicConfig(level=logging.INFO)

blocked_users = set()

class States(StatesGroup):
    chatting = State()
    admin_replying = State()

# دکمه پایین صفحه
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Send message")]], resize_keyboard=True)

# دکمه‌های عضویت
def join_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="My channle", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="I joined", callback_data="check_join")]
    ])

# دکمه پاسخ کاربر
def reply_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Reply", callback_data="user_reply")]])

# منوی ادمین — فقط ۲ دکمه (تمیز!)
def admin_kb(uid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Reply", callback_data=f"rep_{uid}")],
        [InlineKeyboardButton(text="Block user", callback_data=f"block_{uid}")]
    ])

# شروع
@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if uid == ADMIN_ID:
        await message.answer("Hello dear Amir,\n you are the admin of this bot. Please wait to receive messages . . .", reply_markup=main_kb())
        return
    if uid in blocked_users:
        await message.answer("You are blocked !")
        return

    await message.answer(
        f"Welcome to Amir's anonymous message box :)\n\n"
        f"To send me a message, you must first subscribe to my channle .\n",
        reply_markup=join_kb()
    )

# چک عضویت
@router.callback_query(F.data == "check_join")
async def check_join(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ("member", "administrator", "creator"):
            await callback.message.delete()
            await bot.send_message(
                chat_id=user_id,
                text="Great !\n\nNow you can click the «Send message» button anytime you want and send your message :)",
                reply_markup=main_kb()
            )
            await state.set_state(States.chatting)
            await callback.answer()
            return
    except Exception as e:
        logging.error(f"Check error: {e}")

    await callback.answer("You are not subscribed to the channle yet .", show_alert=True)

# دکمه ارسال پیام
@router.message(F.text == "Send message", States.chatting)
async def ask_message(message: types.Message):
    if message.from_user.id in blocked_users:
        await message.answer("You are blocked .")
        return
    await message.answer("Write your message here and send it :", reply_markup=main_kb())

# کاربر پیام فرستاد — مشخصات مستقیم ریپلای می‌خوره
@router.message(States.chatting)
async def user_sent(message: types.Message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        await message.answer("You are blocked")
        return

    user = message.from_user
    uname = f"@{user.username}" if user.username else "Without Username"

    fwd = await message.forward(ADMIN_ID)

    # مشخصات مستقیم روی پیام کاربر ریپلای می‌خوره
    info = f"**User profile :**\n• Name: {user.full_name}\n• Username: {uname}\n• UsernameID: `{user_id}`"
    await bot.send_message(
        ADMIN_ID, info,
        reply_to_message_id=fwd.message_id,
        parse_mode="Markdown"
    )

    # منوی ادمین (فقط ریپلای و بلاک)
    await bot.send_message(
        ADMIN_ID, "Options :",  # یه پیام خالی برای منو
        reply_to_message_id=fwd.message_id,
        reply_markup=admin_kb(user_id)
    )

    await message.answer("The message was sent .", reply_markup=main_kb())

# ادمین روی ریپلای زد
@router.callback_query(F.data.startswith("rep_"))
async def admin_start_reply(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split("_")[1])
    try:
        u = await bot.get_chat(uid)
        uname = f"@{u.username}" if u.username else "user"
    except:
        uname = "user"

    await state.update_data(target=uid, uname=uname, orig_id=callback.message.reply_to_message.message_id)
    await state.set_state(States.admin_replying)
    await callback.message.reply_to_message.reply(f"Replying to {uname}\n Write your text :")
    await callback.answer()

# ادمین پیام فرستاد
@router.message(F.from_user.id == ADMIN_ID, States.admin_replying)
async def admin_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data["target"]
    uname = data["uname"]
    orig_id = data["orig_id"]

    reply_id = message.reply_to_message.message_id if message.reply_to_message else None

    await message.copy_to(
        target,
        caption=f"{uname.replace('@','')} Reply this message\n",
        reply_to_message_id=reply_id,
        reply_markup=reply_kb()
    )
    await bot.send_message(ADMIN_ID, "The message was sent .", reply_to_message_id=orig_id)
    await state.clear()

# کاربر روی پاسخ زد
@router.callback_query(F.data == "user_reply")
async def user_reply(callback: types.CallbackQuery):
    if callback.from_user.id in blocked_users:
        await callback.answer("You are blocked", show_alert=True)
        return
    await callback.message.reply("Write your answer", reply_markup=main_kb())
    await callback.answer()

# بلاک کاربر
@router.callback_query(F.data.startswith("block_"))
async def block_user(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    blocked_users.add(uid)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply_to_message.reply(f"User ( {uid} ) Blocked")
    try:
        await bot.send_message(uid, "You are blocked .")
    except:
        pass
    await callback.answer("User is blocked now .")

# اجرا
async def main():
    dp.include_router(router)
    print("Your bot is on !")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
