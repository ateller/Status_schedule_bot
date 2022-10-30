from telethon import TelegramClient, events, types, functions
from config import api_id, api_hash, bot_token, my_id

import sqlite3
import logging
import random
import asyncio

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

#MSG_HANDLERS
@bot.on(events.NewMessage)
async def reply_on(event):
    message_emojies = [element for element in event.message.entities if isinstance(element, types.MessageEntityCustomEmoji)]
    print (message_emojies)
    
    result = await acc(functions.account.UpdateEmojiStatusRequest(emoji_status=types.EmojiStatus(document_id=message_emojies[0].document_id)))
    print(result)
    await event.reply("bTest")

@acc.on(events.NewMessage)
async def acc_reply_on(event):
    author = await event.get_sender()

    if not isinstance(author, types.User): #So we don't get error when trying to access User attributes with Channels which doesn't have it
        return

    if author.is_self is True and event.raw_text == 'U ok?': #To check if the thing is running
            await event.reply("ACC is ok")
#####################################################################

#MAKING 2 LOOPS RUN SIMULTANIOUSLY AND DO THINGS MEANWHILE
async def acc_task():
    #while True:
        print('ACC WORKING')
        #await asyncio.sleep(1)

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