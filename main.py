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
schedule_db = con = sqlite3.connect('schedule.db') #This section is for connection to the db and creating table
cur = schedule_db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS SCHEDULE(
   DAYOFWEEK TEXT,
   TIME TEXT,
   EMOJI TEXT,
   PRIMARY KEY (DAYOFWEEK, TIME, EMOJI));
""")    #IN DB WE HAVE ONE RELATION => ONE TABLE AND ALL THE COLUMNS IS PK
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

""" class action(enum.Enum): #WHAT USER CURRENTLY DOES (NOT SURE IF I WILL NEED THIS ONE EVENTUALLY)
    ADD = 1 #ADD SOME SCHEDULE RECORDS WITH SOME EMOJIS
    DELETE = 2 #REMOVE SOME
    SHOW = 3 #SHOW SOME"""

#####################################################################

#MSG_HANDLERS AND LOGIC TO WORK WITH SCHEDULE VIA BOT

""" handlers list:
    add_reply               should be registered always. user can interrupt current thing and start frome the beginning
    show_reply              should be registered always. user can interrupt current thing and start frome the beginning
    delete_reply            should be registered always. user can interrupt current thing and start frome the beginning
    emoji_reply             should be registered when there is no interaction
    confirmation_reply      registered when asked for conf
    time_reply              registered when asked for time
    day_reply               registered when asked for day
    emoji_collect           registered when asked for emojies
"""

emojies = []    #global variable. list of emojies related to current interaction
times = []      #global variable. list of time in HH:MM format related to current interaction
days_map = 0       #global variable. bitmap to store days of week related to current interaction
days = ['Everyday', 'Monday', 'Tuesday', 'Whednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']  #To make button work easier

@bot.on(events.NewMessage(from_users = my_id, pattern = '/add')) #WHEN USER USES COMMAND ADD
async def add_reply(event):
    clear_interaction()
    await ask_for_time()
    bot.add_event_handler(time_reply, events.NewMessage(from_users = my_id))
    await event.reply("addTest")
    raise events.StopPropagation

@bot.on(events.NewMessage(from_users = my_id, pattern = '/show')) #WHEN USER USES COMMAND SHOW
async def show_reply(event):
    clear_interaction()
    await event.reply("showTest")
    raise events.StopPropagation

@bot.on(events.NewMessage(from_users = my_id, pattern = '/delete')) #WHEN USER USES COMMAND DELETE
async def delete_reply(event):
    clear_interaction()
    await event.reply("deleteTest")
    raise events.StopPropagation

def clear_interaction(): #At the beginning of the interaction setupt everything properly
    #current_order = order.COMMAND_FIRST   
    bot.remove_event_handler(emoji_reply, events.NewMessage(from_users = my_id))
    bot.remove_event_handler(confirmation_reply, events.CallbackQuery(chats = my_id))
    bot.remove_event_handler(time_reply, events.NewMessage(from_users = my_id))
    bot.remove_event_handler(day_reply, events.CallbackQuery(chats = my_id))
    bot.remove_event_handler(emoji_collect, events.NewMessage(from_users = my_id))

    global emojies, times, days_map

    emojies = []
    times = []
    days_map = 0

@bot.on(events.NewMessage(from_users = my_id))  #User can start interacation with emojy - then set will be asked for days and times to schedule this emoji set
async def emoji_reply(event):

    global emojies

    emojies = retrieve_emojies(event.message.entities)
    print (emojies)
    if emojies is None:
        return

    if len(emojies) == 1:
        mes_text = "What do you want to do with this emoji?"
    else:
        mes_text = "What do you want to do with these emojies?"

    await bot.send_message(my_id, mes_text, buttons=[[Button.inline('Add to schedule'), Button.inline('Remove from schedule')], [Button.inline('Show in schedule')]])

    bot.add_event_handler(confirmation_reply, events.CallbackQuery(chats = my_id))
    
    #result = await acc(functions.account.UpdateEmojiStatusRequest(emoji_status=types.EmojiStatus(document_id=message_emojies[0].document_id)))
    #print(result)
    bot.remove_event_handler(emoji_reply, events.NewMessage(from_users = my_id))

def retrieve_emojies(entities): #Check is there are emojies in message and return list of them
    if entities is None:
        return None

    return [element.document_id for element in entities if isinstance(element, types.MessageEntityCustomEmoji)]

async def confirmation_reply(event): #Process user's choise of action
    print (event)
    await ask_for_time()
    bot.add_event_handler(time_reply, events.NewMessage(from_users = my_id))
    bot.remove_event_handler(confirmation_reply, events.CallbackQuery(chats = my_id))

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

async def time_reply(event): #Process user's input of times
    print(event.message)
    global times

    if 'SET EVERYTIME' in event.raw_text:
        times = ['all']


    for time in re.finditer(r'([01]\d|2[0-3]):[0-5]\d', event.raw_text):
        if time[0] not in times:
            times.append(time[0])
        print (times)
    
    if not times:
        await bot.send_message(my_id, "You didn't enter any valid time, try again")
        return

    await bot.send_message(my_id, 'Times saved', buttons=Button.clear())

    await ask_for_date(True)

    bot.add_event_handler(day_reply, events.CallbackQuery(chats = my_id))
    bot.remove_event_handler(time_reply, events.NewMessage(from_users = my_id))

async def ask_for_date(first_time):

    if first_time:
        first_line =  [Button.inline(('Delete ' if 1 & days_map else 'Add ') + 'Everyday', '1')]
    else:
        first_line =  [Button.inline('No, I\'m finished'), Button.inline(('Delete ' if 1 & days_map else 'Add ') + 'Everyday', 1)]

    await bot.send_message(my_id, "Select day of week in which emoji should be set as status", 
    buttons=[first_line, 
    [Button.inline(('Delete ' if 2 & days_map else 'Add ') + 'Monday', 2), Button.inline(('Delete ' if 4 & days_map else 'Add ') + 'Tuesday ', 3), Button.inline(('Delete ' if 8 & days_map else 'Add ') + 'Whednesday ', 4)],
    [Button.inline(('Delete ' if 16 & days_map else 'Add ') + 'Thursday', 5), Button.inline(('Delete ' if 32 & days_map else 'Add ') + 'Friday ', 6), Button.inline(('Delete ' if 64 & days_map else 'Add ') + 'Saturday ', 7), Button.inline(('Delete ' if 128 & days_map else 'Add ') + 'Sunday', 8)]])

async def day_reply(event): #Process user's input of days

    global days_map
    print (event)

    if(event.data == b"No, I'm finished"):
        if days_map & 1:
            daytimestring = 'Everyday'
        else:
            daytimestring = ''
            for day in range(1,8):
                if days_map & (1 << day):
                    daytimestring += days[day]
        for time in times:
            daytimestring += time + ' '

        if emojies:
            await bot.send_message(my_id, "Emojies are scheduled at" + daytimestring)
            add_records_to_db()
            bot.add_event_handler(emoji_reply, events.NewMessage(from_users = my_id))
        else:
            await bot.send_message(my_id, "Now please send emojis you want to add to schedule at" + daytimestring)
            bot.add_event_handler(emoji_collect, events.NewMessage(from_users = my_id))

        bot.remove_event_handler(day_reply, events.CallbackQuery(chats = my_id))
    else:
        if (event.data == b'1'):
            days_map = 1
        else:
            days_map = (days_map & ~1) ^ (1 << (ord(event.data) - 49))
        
        await bot.send_message(my_id, "Would you like to make any changes or you finished?")
        await ask_for_date(False)

async def emoji_collect(event): #After user asked for emojies, add things to db and finish interaction
    global emojies

    emojies = retrieve_emojies(event.message.entities)
    print (emojies)

    if emojies is None:
        await bot.send_message(my_id, "No emojies in this message, try again")
    else:
        add_records_to_db()
        await bot.send_message(my_id, "Emojies added to schedule")
        bot.add_event_handler(emoji_reply, events.NewMessage(from_users = my_id))
        bot.remove_event_handler(emoji_collect, events.NewMessage(from_users = my_id))

def add_records_to_db():
    for day in range(0,7):
        if days_map & (1 << day):
            for time in times:
                for emoji in emojies:
                    cur.execute("INSERT OR IGNORE INTO SCHEDULE(DAYOFWEEK, TIME, EMOJI) VALUES (?,?,?);", (day, time, emoji));
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
        cur.execute("SELECT EMOJI FROM SCHEDULE WHERE DAYOFWEEK IN (0, ?) AND TIME IN ('all', ?);", (datetime.datetime.today().weekday() + 1, datetime.datetime.today().strftime('%H:%M')));
        result = cur.fetchall()
        if result:
            await acc(functions.account.UpdateEmojiStatusRequest(emoji_status=types.EmojiStatus(document_id=random.choice(set(result)))));
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