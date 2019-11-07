import botogram
import redis
import random
from datetime import datetime as dt, timedelta

# bot information
bot = botogram.create("542350726:AAHtyLqFRz2rnkjLofdtOEweLTpjC2kgdGI")
bot.about = "This bot is used to block a flooder with a captcha"
bot.owner = "@sonomichelequellostrano"


# redis
r = redis.Redis()


# antiflood config
antiflood_config = {
    "messaggi": 3,
    "secondi": 4
}


# emoji list for captcha
emojis = {
    "grinning_face": {
        "emoji": "😀",
        "description": "faccia sorridente"
    },
    "face_with_tears_of_joy": {
        "emoji": "😂",
        "description": "faccia con lacrime di gioia"
    },
    "upside_down_face": {
        "emoji": "🙃",
        "description": "faccia sotto sopra"
    }
}


# bot commands
# @bot.command("hello")
# def hello_command(chat, message, args):
#     btns = generate_captcha_buttons()
#     emoji = random.choice(list(emojis))
#     r.hset(message.sender.id, "bloccato", "1")
#     r.hset(message.sender.id, "emoji", emoji)
#     r.hset(message.sender.id, "errori", 0)
#     chat.send("@" + message.sender.username + " clicca *" + emojis[emoji]["description"] +
#     "* per risolvere il captcha",
#               attach=btns)


# antiflood
@bot.process_message
def antiflood(chat, message):
    starttime = dt.now()  # Time when first message was sent
    # Allows only groups
    if chat.type not in ("group", "supergroup"):
        return

    # Activate antiflood only for normal users
    if message.sender not in chat.admins:
        if r.exists(message.sender.id):
            rmessages = int(r.hget(message.sender.id, "messages"))
            rstarttime = int(dt.fromisoformat(r.hget(message.sender.id, "starttime").decode("utf-8")).timestamp())
            if rmessages <= antiflood_config["messaggi"] and \
                    (int(dt.now().timestamp()) - rstarttime) <= antiflood_config["secondi"]:
                r.hset(message.sender.id, "messages", rmessages + 1)
            elif rmessages > antiflood_config["messaggi"] and \
                    (int(dt.now().timestamp()) - rstarttime) < antiflood_config["secondi"]:
                # mute the user
                with chat.permissions(message.sender.id) as perms:
                    perms.send_messages = False
                    perms.until_date = dt.now() + timedelta(seconds=1)  # Restrict user forever
                # this is the captcha
                btns = generate_captcha_buttons()
                emoji = random.choice(list(emojis))
                r.hset(message.sender.id, "bloccato", "1")
                r.hset(message.sender.id, "emoji", emoji)
                r.hset(message.sender.id, "errori", 0)
                chat.send("@" + message.sender.username + " clicca *" + emojis[emoji][
                    "description"] + "* per risolvere il captcha. *Errori*: " +
                          r.hget(message.sender.id, "errori").decode("utf-8"), attach=btns)
            else:
                r.hset(message.sender.id, "messages", 1)
                r.hset(message.sender.id, "starttime", starttime.isoformat())
        else:
            r.hset(message.sender.id, "messages", 1)
            r.hset(message.sender.id, "starttime", starttime.isoformat())


# captcha callback
@bot.callback("captcha")
def captcha_callback(query, data, chat, message):
    if r.hget(query.sender.id, "bloccato").decode("utf-8") == "0":
        return
    if r.hget(query.sender.id, "emoji").decode("utf-8") == data:
        r.hset(query.sender.id, "bloccato", "0")
        r.hset(query.sender.id, "errori", 0)
        query.notify("Captcha risolto con successo")
        message.delete()
        with chat.permissions(query.sender.id) as perms:
            perms.send_messages = True
    else:
        r.hset(query.sender.id, "errori", int(r.hget(query.sender.id, "errori").decode("utf-8")) + 1)
        if int(r.hget(query.sender.id, "errori").decode("utf-8")) >= 2:
            message.edit("@" + query.sender.username +
                         " ha sbagliato due volte il captcha ed è stato bloccato per sempre")


# generate captcha buttons
def generate_captcha_buttons():
    btns = botogram.Buttons()
    rkey = random.choice(list(emojis))
    btns[0].callback(emojis[rkey]["emoji"], "captcha", rkey)
    tempemojis = removekey(emojis, rkey)
    rkey = random.choice(list(tempemojis))
    btns[1].callback(tempemojis[rkey]["emoji"], "captcha", rkey)
    tempemojis = removekey(tempemojis, rkey)
    rkey = random.choice(list(tempemojis))
    btns[2].callback(tempemojis[rkey]["emoji"], "captcha", rkey)
    return btns


# remove key from dictionary without really changing it (used to select 3 different random emojis)
def removekey(d, key):
    newdict = dict(d)
    del newdict[key]
    return newdict


if __name__ == "__main__":
    bot.run()
