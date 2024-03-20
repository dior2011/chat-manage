from aiogram import Bot, Dispatcher

from aiogram.enums import ParseMode
from aiogram.filters import CommandStart,Command,and_f
from aiogram import F
from aiogram.types import Message,CallbackQuery,BufferedInputFile
from data import config
import asyncio
import logging
import sys
from time import time
from menucommands.set_bot_commands  import set_default_commands
from baza.sqlite import Database
from filters.admin import IsBotAdminFilter
from filters.check_sub_channel import IsCheckSubChannels
from keyboard_buttons import admin_keyboard
from aiogram.fsm.context import FSMContext 
from states.reklama import Adverts
from aiogram.types import InlineKeyboardButton,ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
import time 
from middlewares.throttling import ThrottlingMiddleware
from time import time
ADMINS = config.ADMINS
TOKEN = config.BOT_TOKEN
CHANNELS = config.CHANNELS

dp = Dispatcher()

@dp.message(and_f(F.reply_to_message,F.text=="/ban"))
async def ban_user(message:Message):
    user_id =  message.reply_to_message.from_user.id
    await message.chat.ban_sender_chat(user_id)
    await message.answer(f"{message.reply_to_message.from_user.first_name} guruhdan chiqarib yuborilasiz.")

@dp.message(and_f(F.reply_to_message,F.text=="/unban"))
async def unban_user(message:Message):
    user_id =  message.reply_to_message.from_user.id
    await message.chat.unban_sender_chat(user_id)
    await message.answer(f"{message.reply_to_message.from_user.first_name} guruhga qaytishingiz mumkin.")

@dp.message(and_f(F.reply_to_message,F.text=="/mute"))
async def ban_user(message:Message):
    user_id = message.reply_to_message.from_user.id
    permission = ChatPermissions(can_send_messages=False)
    until_date = int(time) + 180
    await message.chat.restrict(user_id=user_id, permissions=permission, until_date=until_date)
    await message.answer(f"{message.reply_to_message.from_user.first_name} guruhga 3 daqiqa yoza olmaysiz!")
    await message.reply_to_message.delete()



@dp.message(and_f(F.reply_to_message,F.text=="/unmute"))
async def unban_user(message:Message):
    user_id =  message.reply_to_message.from_user.id
    permission = ChatPermissions(can_send_messages=True)
    await message.chat.restrict(user_id=user_id, permissions=permission)
    await message.answer(f"{message.reply_to_message.from_user.first_name} endi yoza olasiz!")


@dp.message(CommandStart())
async def start_command(message:Message):
    
    
    full_name = message.from_user.full_name
    telegram_id = message.from_user.id
    try:
        db.add_user(full_name=full_name,telegram_id=telegram_id)
        await message.answer(text="Assalomu alaykum, botimizga hush kelibsiz")
    except:
        await message.answer(text="Assalomu alaykum")

@dp.message(and_f(F.reply_to_message,F.text=="/setphoto"))
async def setphoto_group(message:Message):
    photo = message.reply_to_message.photo[-1].file_id
    file = await bot.get_file(photo)
    file_path = file.file_path
    file = await bot.download_file(file_path)
    file = file.read()
    await message.chat.set_photo(photo=BufferedInputFile(file=file,filename="asd.jpg"))
    await message.answer("Guruh rasmi uzgardi")
    

@dp.message(F.text.startswith('/setname'))
async def set_name(message: Message):
    text = message.text.split("/setname")[1]
    if text:
        await message.chat.set_title(text)


@dp.message(F.new_chat_member)
async def new_member(message:Message):
    user = message.new_chat_member.get("first_name")
    await message.answer(f"{user} Guruhga xush kelibsiz!")


@dp.message(F.left_chat_member)
async def new_member(message:Message):
    # print(message.new_chat_member)
    user = message.left_chat_member.full_name
    await message.answer(f"{user} Xayr!")
    await message.delete()





@dp.message(F.chat.func(lambda chat: chat.type == "supergroup"))
async def test(message:Message):
    text = f"""
chat type: {message.chat.type}\n
chat id: {message.chat.id}\n
chat name: {message.chat.full_name}
"""
    await message.answer(text=text)

@dp.message(Command('count'))
async def users_count(message:Message):
    counts = db.count_users()
    text = f"Botimizda {counts[0]} ta foydalanuvchi bor"
    await message.answer(text=text)


@dp.message(IsCheckSubChannels())
async def kanalga_obuna(message:Message):
    text = ""
    inline_channel = InlineKeyboardBuilder()
    for index,channel in enumerate(CHANNELS):
        ChatInviteLink = await bot.create_chat_invite_link(channel)
        inline_channel.add(InlineKeyboardButton(text=f"{index+1}-kanal",url=ChatInviteLink.invite_link))
    inline_channel.adjust(1,repeat=True)
    button = inline_channel.as_markup()
    await message.answer(f"{text} kanallarga azo bo'ling",reply_markup=button)



@dp.message(Command("admin"),IsBotAdminFilter(ADMINS))
async def is_admin(message:Message):
    await message.answer(text="Admin menu",reply_markup=admin_keyboard.admin_button)


@dp.message(F.text=="Foydalanuvchilar soni",IsBotAdminFilter(ADMINS))
async def users_count(message:Message):
    counts = db.count_users()
    text = f"Botimizda {counts[0]} ta foydalanuvchi bor"
    await message.answer(text=text)

@dp.message(F.text=="Reklama yuborish",IsBotAdminFilter(ADMINS))
async def advert_dp(message:Message,state:FSMContext):
    await state.set_state(Adverts.adverts)
    await message.answer(text="Reklama yuborishingiz mumkin !")

@dp.message(Adverts.adverts)
async def send_advert(message:Message,state:FSMContext):
    
    message_id = message.message_id
    from_chat_id = message.from_user.id
    users = db.all_users_id()
    count = 0
    for user in users:
        try:
            await bot.copy_message(chat_id=user[0],from_chat_id=from_chat_id,message_id=message_id)
            count += 1
        except:
            pass
        time.sleep(0.5)
    
    await message.answer(f"Reklama {count}ta foydalanuvchiga yuborildi")
    await state.clear()
        
@dp.message(F.reply_to_message,F.text.startswith('/mute'))
async def mute_people(message:Message):
    try:
        son = int(message.text.split("/mute")[1]) * 60
    

    except TypeError:
        son = 60
    permission = ChatPermissions(can_send_messages=False)
    if son:
        await message.chat.restrict(user_id=message.reply_to_message.from_user.id,until_date=son,permissions=permission)
        await message.answer(text=f"@{message.reply_to_message.from_user.username} - siz {int(son/60)} daqiqa guruhga yoza olmaysiz!")

@dp.message(F.reply_to_message,F.text.startswith('/unmute'))
async def unmute_people(message:Message):
    
    user_id =  message.reply_to_message.from_user.id
    permission = ChatPermissions(can_send_messages=True)
    await message.chat.restrict(user_id=user_id, permissions=permission)
    await message.answer(f"{message.reply_to_message.from_user.first_name} endi yoza olasiz!")


@dp.startup()
async def on_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=int(admin),text="Bot ishga tushdi")
        except Exception as err:
            logging.exception(err)

@dp.shutdown()
async def off_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=int(admin),text="Bot ishdan to'xtadi!")
        except Exception as err:
            logging.exception(err)








async def main() -> None:
    global bot,db
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    db = Database(path_to_db="main.db")
    db.create_table_users()
    await set_default_commands(bot)
    dp.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))
    await dp.start_polling(bot)
    



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())


