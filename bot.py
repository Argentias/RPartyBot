import random
import asyncio
import aiohttp
import json
import discord
import bot.env
from discord import Game
from discord.ext.commands import Bot

BOT_PREFIX = "~"
OTHER_PREFIX = ">"
TOKEN = bot.env.TOKEN

botmode = "null"
maxpartysize = 0
# Party array has the format [name, current hp, max hp, DST fails, DST successes]
# DST stands for Death Saving Throw.
party = []

client = Bot(command_prefix=BOT_PREFIX)

def check_int(s):
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

def list_splice(target, start, delete_count=None, *items):
    """Remove existing elements and/or add new elements to a list.

    target        the target list (will be changed)
    start         index of starting position
    delete_count  number of items to remove (default: len(target) - start)
    *items        items to insert at start index

    Returns a new list of removed items (or an empty list)
    """
    if delete_count == None:
        delete_count = len(target) - start

    # store removed range in a separate list and replace with *items
    total = start + delete_count
    removed = target[start:total]
    target[start:total] = items

    return removed

@client.event
async def on_ready():
    await client.change_presence(activity=Game(name="managing parties"), status=None, afk=False)
    print("Logged in as " + client.user.name)

async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)

@client.command()
async def setup(ctx):
    global botmode
    global maxpartysize
    global party
    if (party != []):
        while True:
            await ctx.send("Performing this action will clear the current party. Is this okay? ("+OTHER_PREFIX+"clr, [y/n])")
            def check(msg):
                return msg.content.startswith(OTHER_PREFIX+'clr')
            message = await client.wait_for('message', check=check)
            clr = message.content[len(OTHER_PREFIX+'clr'):].strip()
            if (clr == "y" or clr == "yes"):
                break
                party = []
            elif (clr == "n" or clr == "no"):
                return
            else:
                await ctx.send("Please answer yes or no.")
                continue		
    await ctx.send("Hello! I'm RPartyBot, here to help with all your RP party needs!")
    await ctx.send("I'll walk you through the setup so you can get up and running ASAP!")
    while True:
        await ctx.send("First, should I be in general RP mode or D&D mode? ("+OTHER_PREFIX+"mode [rp or dd])")
        def check(msg):
            return msg.content.startswith(OTHER_PREFIX+'mode')
        message = await client.wait_for('message', check=check)
        mode = message.content[len(OTHER_PREFIX+'mode'):].strip()
        if mode == "rp":
            await ctx.send("Alright, I'll enter general RP mode.")
            await ctx.send("Just so you know, that means I will disable HP and death saving throw tracking.")
            botmode = "rp"
            break
        elif mode == "dd":
            await ctx.send("Alright, I'll enter D&D mode.")
            await ctx.send("Just so you know, that means party members will each have their own HP and death saving throw tracking.")
            botmode = "dd"
            break
        else:
            await ctx.send("Sorry, that input was invalid. Please enter either 'rp' or 'dd'.")
            continue
    while True:
        await ctx.send("Next I need you to enter the maximum party size. ("+OTHER_PREFIX+"size [integer, or 0 for any size])")
        def check(msg):
            return msg.content.startswith(OTHER_PREFIX+'size')
        message = await client.wait_for('message', check=check)
        size = message.content[len(OTHER_PREFIX+'size'):].strip()
        if check_int(size) == True:
            if int(size) == 0:
                await ctx.send("Great, I won't set a limit to party size.")
                maxpartysize = 0
                break
            else:
                await ctx.send("Alright, I'll set the maximum party size to "+size)
                maxpartysize = int(size)
                break
        else:
            await ctx.send("That doesn't seem to be an integer. Try again.")
            continue
    await ctx.send("That's all for now. To get playing, just type '"+BOT_PREFIX+"help' to see all the commands I can do.")
    await ctx.send("If you want to change any of these settings, just type '"+BOT_PREFIX+"setup' again and I'll be here to help!")

@client.command()
async def add(ctx, name):
    global botmode
    global maxpartysize
    global party
    if (maxpartysize == 0 or len(party) < maxpartysize):
        if botmode == "dd":
            await ctx.send("Adding "+name+" to the party. What is this character's current HP? ("+OTHER_PREFIX+"chp [current hp])")
            def check(msg):
                return msg.content.startswith(OTHER_PREFIX+'chp')
            message = await client.wait_for('message', check=check)
            chp = message.content[len(OTHER_PREFIX+'chp'):].strip()
            await ctx.send("And this character's max HP? ("+OTHER_PREFIX+"mhp [maximum hp])")
            def check(msg):
                return msg.content.startswith(OTHER_PREFIX+'mhp')
            message = await client.wait_for('message', check=check)
            mhp = message.content[len(OTHER_PREFIX+'mhp'):].strip()
            party.append([name, int(chp), int(mhp), 0, 0])
            await ctx.send("Added character "+name+" with "+chp+" HP out of "+mhp+" to the party. This character's ID is "+str(len(party)-1)+". Remember that for later!")
        elif botmode == "rp":
            party.append([name])
            await ctx.send("Added character "+name+" to the party. This character's ID is "+len(party)+". Remember that for later!")
    else:
        await ctx.send("The maximum party size has been reached. Please remove a character from the party before adding a new one.")

@client.command()
async def remove(ctx, id):
    global botmode
    global maxpartysize
    global party
    id = int(id)
    if party != []:
        if id <= (len(party)-1):
            while True:
                await ctx.send("The character with id "+str(id)+", "+party[id][0]+", will be removed from the party. Is this okay? ("+OTHER_PREFIX+"rem [y/n])")
                def check(msg):
                    return msg.content.startswith(OTHER_PREFIX+'rem')
                message = await client.wait_for('message', check=check)
                rem = message.content[len(OTHER_PREFIX+'rem'):].strip()
                if (rem == "y" or rem == "yes"):
                    break
                elif (rem == "n" or rem == "no"):
                    return
                else:
                    await ctx.send("Please answer yes or no.")
                    continue
            list_splice(party, id, 1)
            await ctx.send("This character has been removed from the party. All characters who had an ID greater than "+str(id)+" now have their IDs reduced by 1. (For example, an ID of 4 becomes 3)")
        else:
            await ctx.send("There is no character with this ID.")
    else:
        await ctx.send("There's no one in the party to remove!")

@client.command()
async def status(ctx):
    global botmode
    global maxpartysize
    global party
    await ctx.send("Sending you the status of the party now.")
    embed = discord.Embed(title="Party Status", description = "The current status of the party", color=0xff3333)
    if botmode == "dd":
        for p in range(0, len(party)):
            embed.add_field(name=party[p][0]+" (ID "+str(p)+")", value=str(party[p][1])+"/"+str(party[p][2])+" HP \n"+str(party[p][3])+" death saving throw fails \n"+str(party[p][4])+" death saving throw successes", inline=False)
    elif botmode == "rp":
        for p in range(0, len(party)):
            embed.add_field(name=party[p][0], value="ID "+str(p), inline=False)
    await ctx.send(embed=embed)

@client.command(name='damage', aliases=['dmg'])
async def damage(ctx, id, amount):
    global botmode
    global maxpartysize
    global party
    id = int(id)
    amount = int(amount)
    if botmode == "dd":
        party[id][1] -= amount
        if party[id][1] <= 0:
            party[id][1] = 0
            await ctx.send(str(amount)+" damage done to the character with ID "+str(id)+", "+party[id][0]+". Current HP is now "+str(party[id][1])+".")
    else:
        await ctx.send("You must be in D&D mode to use this command.")
		
@client.command()
async def heal(ctx, id, amount):
    global botmode
    global maxpartysize
    global party
    id = int(id)
    amount = int(amount)
    if botmode == "dd":
        party[id][1] += amount
        if party[id][1] >= party[id][2]:
            party[id][1] = party[id][2]
        await ctx.send(str(amount)+" damage healed from the character with ID "+str(id)+", "+party[id][0]+". Current HP is now "+str(party[id][1])+".")
    else:
        await ctx.send("You must be in D&D mode to use this command.")

@client.command()
async def throw(ctx, id, number):
    global botmode
    global maxpartysize
    global party
    id = int(id)
    number = float(number)
    if botmode == "dd":
        if party[id][1] <= 0:
            if number == 20:
                party[id][1] = 1
                party[id][3] = 0
                party[id][4] = 0
                await ctx.send("A 20! The character with ID "+str(id)+", "+party[id][0]+", is revived with 1 HP!")
            elif number >= 10:
                party[id][4] += 1
                if party[id][4] >= 3:
                    party[id][1] = 1
                    party[id][3] = 0
                    party[id][4] = 0
                    await ctx.send("Three successes! The character with ID "+str(id)+", "+party[id][0]+", is revived with 1 HP.")
                else:
                    await ctx.send("One success. The character with ID "+str(id)+", "+party[id][0]+", now has "+str(party[id][4])+" out of 3 successes.")
            elif number == 1:
                party[id][3] += 2
                if party[id][3] >= 3:
                    list_splice(party, id, 1)
                    await ctx.send("A 1... The character with ID "+str(id)+", "+party[id][0]+", has at least 3 failures, and is removed from the party.")
                    await ctx.send("All characters who had an ID greater than "+str(id)+" now have their IDs reduced by 1. (For example, an ID of 4 becomes 3)")
                else:
                    await ctx.send("A 1... The character with ID "+str(id)+", "+party[id][0]+", gains two additional failures, and has "+str(party[id][3])+" out of 3 failures.")
            elif number < 10:
                party[id][3] += 1
                if party[id][3] >= 3:
                    list_splice(party, id, 1)
                    await ctx.send("One failure The character with ID "+str(id)+", "+party[id][0]+", has at least 3 failures, and is removed from the party.")
                    await ctx.send("All characters who had an ID greater than "+str(id)+" now have their IDs reduced by 1. (For example, an ID of 4 becomes 3)")
                else:
                    await ctx.send("One failure. The character with ID "+str(id)+", "+party[id][0]+", now has "+str(party[id][3])+" out of 3 failures.")
        else:
            await ctx.send("This character does not have 0 HP, and therefore does not need to make a death saving throw.")
    else:
        await ctx.send("You must be in D&D mode to use this command.")

@client.command()
async def rthrow(ctx, id):
    global botmode
    global maxpartysize
    global party
    id = int(id)
    if botmode == "dd":
        if party[id][1] <= 0:
            number = random.randint(1, 20)
            await ctx.send("The number is "+str(number)+".")
            if number == 20:
                party[id][4] += 2
                if party[id][3] >= 3:
                    party[id][1] = 1
                    party[id][3] = 0
                    party[id][4] = 0
                    await ctx.send("A 20! The character with ID "+str(id)+", "+party[id][0]+", has at least three successes, and is revived with 1 HP!")
                else:
                    await ctx.send("A 20! The character with ID "+str(id)+", "+party[id][0]+", gains two additional successes, and has "+str(party[id][4])+" out of 3 successes")
            elif number >= 10:
                party[id][4] += 1
                if party[id][4] >= 3:
                    party[id][1] = 1
                    party[id][3] = 0
                    party[id][4] = 0
                    await ctx.send("Three successes! The character with ID "+str(id)+", "+party[id][0]+", is revived with 1 HP.")
                else:
                    await ctx.send("One success. The character with ID "+str(id)+", "+party[id][0]+", now has "+str(party[id][4])+" out of 3 successes.")
            elif number == 1:
                party[id][3] += 2
                if party[id][3] >= 3:
                    list_splice(party, id, 1)
                    await ctx.send("A 1... The character with ID "+str(id)+", "+party[id][0]+", has at least 3 failures, and is removed from the party.")
                    await ctx.send("All characters who had an ID greater than "+str(id)+" now have their IDs reduced by 1. (For example, an ID of 4 becomes 3)")
                else:
                    await ctx.send("A 1... The character with ID "+str(id)+", "+party[id][0]+", gains two additional failures, and has "+str(party[id][3])+" out of 3 failures.")
            elif number < 10:
                party[id][3] += 1
                if party[id][3] >= 3:
                    list_splice(party, id, 1)
                    await ctx.send("Three failures... The character with ID "+str(id)+", "+party[id][0]+", is removed from the party.")
                    await ctx.send("All characters who had an ID greater than "+str(id)+" now have their IDs reduced by 1. (For example, an ID of 4 becomes 3)")
                else:
                    await ctx.send("One failure. The character with ID "+str(id)+", "+party[id][0]+", now has "+str(party[id][3])+" out of 3 failures.")
        else:
            await ctx.send("This character does not have 0 HP, and therefore does not need to make a death saving throw.")
    else:
        await ctx.send("You must be in D&D mode to use this command.")

@client.command()
async def othrow(ctx, id, sf):
    global botmode
    global maxpartysize
    global party
    id = int(id)
    if botmode == "dd":
        if party[id][1] <= 0:
            if sf == "s" or sf == "success" or sf == "succeed":
                party[id][4] += 1
                if party[id][4] >= 3:
                    party[id][1] = 1
                    party[id][3] = 0
                    party[id][4] = 0
                    await ctx.send("Three successes! The character with ID "+str(id)+", "+party[id][0]+", is revived with 1 HP.")
                else:
                    await ctx.send("One success. The character with ID "+str(id)+", "+party[id][0]+", now has "+str(party[id][4])+" out of 3 successes.")
            elif sf == "f" or sf == "fail" or sf == "failure":
                party[id][3] += 1
                if party[id][3] >= 3:
                    list_splice(party, id, 1)
                    await ctx.send("Three failures... The character with ID "+str(id)+", "+party[id][0]+", is removed from the party.")
                    await ctx.send("All characters who had an ID greater than "+str(id)+" now have their IDs reduced by 1. (For example, an ID of 4 becomes 3)")
                else:
                    await ctx.send("One failure. The character with ID "+str(id)+", "+party[id][0]+", now has "+str(party[id][3])+" out of 3 failures.")
            else:
                await ctx.send("Sorry, that isn't a valid input. Acceptable inputs include 's', 'success', 'f', and 'fail'.")
        else:
            await ctx.send("This character does not have 0 HP, and therefore does not need to make a death saving throw.")
    else:
        await ctx.send("You must be in D&D mode to use this command.")

client.remove_command('help')

@client.command()
async def help(ctx):
    embed = discord.Embed(title="RPartyBot", description="A bot to help manage roleplaying parties. Commands:", color=0x13a102)

    embed.add_field(name=BOT_PREFIX+"setup", value="Sets bot mode, max party size, and other general settings.", inline=False)
    embed.add_field(name=BOT_PREFIX+"add name", value="Adds a character named **name** to the party. If in D&D mode, also asks for current and maximum HP of that character. Outputs the ID of that character.", inline=False)
    embed.add_field(name=BOT_PREFIX+"remove id", value="Removes the character with the ID **id** from the party.", inline=False)
    embed.add_field(name=BOT_PREFIX+"status", value="Shows the current party members. In D&D mode, also shows HP and death saving throw status of each character.", inline=False)
    embed.add_field(name=BOT_PREFIX+"damage id amount", value="Deals **amount** damage to the character with the ID **id**. Can only be used in D&D mode.", inline=False)
    embed.add_field(name=BOT_PREFIX+"heal id amount", value="Heals **amount** damage from the character with the ID **id**. Can only be used in D&D mode.", inline=False)
    embed.add_field(name=BOT_PREFIX+"throw id number", value="Gives the character with ID **id** one death saving throw success if **number** is greater than or equal to 10, or a failure if **number** is less than 10. For the purposes of this bot, a 1 counts as two failures, and a 20 counts as 2 successes. Can only be used in D&D mode.", inline = False)
    embed.add_field(name=BOT_PREFIX+"rthrow id", value="Generates a random integer between 1 and 20, and uses it to perform a death saving throw for the character with ID **id**. Can only be used in D&D mode.", inline=False)
    embed.add_field(name=BOT_PREFIX+"othrow id s/f", value="Overrides the number system and adds a success(for **s**) or failure(for **f**) to the character with ID **id**. Can only be used in D&D mode.", inline=False)
    
    await ctx.send(embed=embed)

client.loop.create_task(list_servers())
client.run(TOKEN)
