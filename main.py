from dataclasses import dataclass
from telethon import TelegramClient, events, types, functions
from telethon.tl.custom import Button
from config import api_id, api_hash, bot_token, my_id

import sqlite3  #to store schedule
import logging  #to print error messages
import random   #to select emoji
import asyncio  #to deal with loops in telethon
import enum     #to set state
import re       #to check input time
import datetime #to get current date

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING) #not sure if I need this, but API guide said I do

#DB INIT
schedule_db = con = sqlite3.connect('schedule.db') #This section is for connectiong to the db and creating table
cur = schedule_db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS SCHEDULE(
   DAYOFWEEK TEXT,
   TIME TEXT,
   EMOJI TEXT);
""")
schedule_db.commit()
#####################################################################

#TELEBOT INIT
acc = TelegramClient('acc', api_id, api_hash) #Telthon client for my account
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token) #Telthon client for control bot

async def bot_start(): #Starting

    print("Starting")
    await bot.send_message(my_id, 'Started')

with bot:
    bot.loop.run_until_complete(bot_start())
#####################################################################

#DIALOG_WITH_USERS_STATE

class action(enum.Enum):
    ADD = 1
    DELETE = 2
    SHOW = 3

class stage(enum.Enum):
    NOTHING_ASKED = 0
    ASKED_FOR_CONFIRMATION = 1
    ASKED_FOR_DATE = 2
    ASKED_FOR_TIME = 3
    ASKED_FOR_EMOJI = 4
    GOT_EVERYTHING = 5

class order(enum.Enum):
    EMOJI_FIRST = 1
    COMMAND_FIRST = 2

current_action = action.ADD
current_stage = stage.NOTHING_ASKED
current_order = order.EMOJI_FIRST

#####################################################################

#MSG_HANDLERS AND LOGIC TO WORK WITH SCHEDULE VIA BOT

emojies = []

@bot.on(events.NewMessage(from_users = my_id, pattern = '/add'))
async def add_reply(event):
    await ask_for_time()
    await event.reply("addTest")

@bot.on(events.NewMessage(from_users = my_id, pattern = '/show'))
async def show_reply(event):
    await event.reply("showTest")

bot.on(events.NewMessage(from_users = my_id, pattern = '/delete'))
async def delete_reply(event):
    await event.reply("deleteTest")

emojies = []

@bot.on(events.NewMessage(from_users = my_id))
async def emoji_reply(event):
    if event.message.entities is None:
        return

    message_emojies = [element for element in event.message.entities if isinstance(element, types.MessageEntityCustomEmoji)]
    print (message_emojies)

    if message_emojies is None:
        return

    if current_stage == stage.NOTHING_ASKED:
        if message_emojies.size == 1:
            await event.reply("What do you to do with this emoji?")
        else:
            await event.reply("What do you to do with these emojies?")

        await bot.send_message(my_id, buttons=[[Button.inline('Add to schedule'), Button.inline('Remove from schedule')], [Button.inline('Show in schedule')]])

        current_stage = stage.ASKED_FOR_CONFIRMATION
        current_order = order.EMOJI_FIRST
    elif current_stage == stage.ASKED_FOR_EMOJI:
        await event.reply("Imagine I did this") #Here will be db records insertion
    
    #result = await acc(functions.account.UpdateEmojiStatusRequest(emoji_status=types.EmojiStatus(document_id=message_emojies[0].document_id)))
    #print(result)
    await event.reply("emojitest")
    bot.remove_event_handler(emoji_reply, events.NewMessage)

@bot.on(events.CallbackQuery(from_users = my_id))
async def confirmation_reply(event):
    print (event)
    await ask_for_time()

async def ask_for_time():
    await bot.send_message(my_id, "Select time in which emoji should be set as status (or enter your own using format HH:MM, you can also enter multiple like HH:MM, HH:MM, HH:MM)", 
    buttons=[[Button.text('SET EVERYTIME')], 
    [Button.text('00:00'), Button.text('01:00'), Button.text('02:00')],
    [Button.text('03:00'), Button.text('04:00'), Button.text('05:00')],
    [Button.text('06:00'), Button.text('07:00'), Button.text('08:00')],
    [Button.text('09:00'), Button.text('10:00'), Button.text('11:00')],
    [Button.text('12:00'), Button.text('13:00'), Button.text('14:00')],
    [Button.text('15:00'), Button.text('16:00'), Button.text('17:00')],
    [Button.text('18:00'), Button.text('19:00'), Button.text('20:00')],
    [Button.text('21:00'), Button.text('22:00'), Button.text('23:00')]])

    bot.add_event_handler(time_reply, events.NewMessage(from_users = my_id))
    current_stage = stage.ASKED_FOR_TIME

times = []

async def time_reply(event):
    if current_stage != stage.ASKED_FOR_TIME:
        return

    if 'SET EVERYTIME' in event.raw_text:
        times = ['all']

    for time in re.finditer(r'\d[0-2]\d\:\d[0-5]\d', event.raw_text):
        print()
        if (time[0][0] == '2') and (time[0][1] < '3'):
            times.append(time)
    
    if times is None:
        bot.send_message(my_id, "You didn't enter any valid time, try again")
        ask_for_time()
        return

    await bot.send_message(my_id, "Select day of week in which emoji should be set as status", 
    buttons=[[Button.inline('Everyday')], 
    [Button.inline('Monday'), Button.inline('Tuesday'), Button.inline('Whednesday')],
    [Button.inline('Thursday'), Button.inline('Friday'), Button.inline('Saturday'), Button.inline('Sunday')]])

    current_stage = stage.ASKED_FOR_DATE

    ask_for_date(True)

    bot.remove_event_handler(time_reply, events.NewMessage)

    await event.reply("timeTest")

dates = 0
days = ['Everyday', 'Monday', 'Tuesday', 'Whednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

async def ask_for_date(first_time):

    if first_time:
        first_line =  [Button.inline(('Delete' if 1 & dates else 'Add') + 'Everyday', 0)]
    else:
        first_line =  [Button.inline('No, I\'m finished'), Button.inline(('Delete' if 1 & dates else 'Add') + 'Everyday', 0)]

    await bot.send_message(my_id, "Select day of week in which emoji should be set as status", 
    buttons=[first_line, 
    [Button.inline(('Delete' if 1 & dates else 'Add') + 'Monday', 1), Button.inline(('Delete' if 1 & dates else 'Add') + 'Tuesday', 2), Button.inline(('Delete' if 1 & dates else 'Add') + 'Whednesday', 3)],
    [Button.inline(('Delete' if 1 & dates else 'Add') + 'Thursday', 4), Button.inline(('Delete' if 1 & dates else 'Add') + 'Friday', 5), Button.inline(('Delete' if 1 & dates else 'Add') + 'Saturday', 6), Button.inline(('Delete' if 1 & dates else 'Add') + 'Sunday', 7)]])
    bot.add_event_handler(day_reply, events.CallbackQuery(from_users = my_id))

async def day_reply(event):

    if(event.raw_text == 'No, I\'m finished'):
        if current_order == order.EMOJI_FIRST:
            add_records_to_db()
        else:
            if dates[0]:
                daytimestring = 'Everyday'
            else:
                daytimestring = ''
                for day in range(0,7):
                    if dates & (1 << day):
                        daytimestring += days[day]
            for time in times:
                daytimestring += time + ' '
            await bot.send_message(my_id, "Now please send emojis you want to add to schedule at" + daytimestring)
            bot.add_event_handler(emoji_reply, events.NewMessage(from_users = my_id))
    else:
        dates = dates ^ (1 << event.data)
        await bot.send_message(my_id, "Would you like to make any changes or you finished?")
        ask_for_date(False)

    await event.reply("dayTest")

def add_records_to_db():
    for day in range(0,7):
        if dates & (1 << day):
            for time in times:
                for emoji in emojies:
                    cur.execute("INSERT INTO SCHEDULE(DAYOFWEEK, TIME, EMOJI) VALUES (?,?,?);", (day, time, emoji));
                    schedule_db.commit()
    print('add to db')

@acc.on(events.NewMessage(from_users = my_id))
async def acc_reply_on(event):
    author = await event.get_sender()

    if not isinstance(author, types.User): #So we don't get error when trying to access User attributes with Channels which doesn't have it
        return

    if author.is_self is True and event.raw_text == 'U ok?': #To check if the thing is running
            await event.reply("ACC is ok")
#####################################################################

#MAKING 2 LOOPS RUN SIMULTANIOUSLY AND DO THINGS (CHANGE STATUSES ACCORDING TO SCHEDULE) MEANWHILE
async def acc_task():
    while True:
        #print('ACC WORKING')
        cur.execute("SELECT EMOJI FROM SCHEDULE WHERE DAYOFWEEK IN (?, ?) AND TIME = ?;", (0, datetime.datetime.today().weekday() + 1, datetime.datetime.today().strftime('%H:%M')));
        result = cur.fetchall()
        if result:
            await acc(functions.account.UpdateEmojiStatusRequest(emoji_status=types.EmojiStatus(document_id=random.choice(result))));
        await asyncio.sleep(1)

async def acc_loop():
    async with acc:
        await acc.run_until_disconnected()

loop = asyncio.get_event_loop()
loop.create_task(acc_task())
loop.create_task(acc_loop())

with bot:
    bot.run_until_disconnected()
#####################################################################

schedule_db.close()