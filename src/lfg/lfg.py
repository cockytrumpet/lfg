__package__ = "lfg"
# pyright: basic
import contextvars
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
from state import *  # pyright: ignore

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("DISCORD_TOKEN not set in .env file")
    exit(1)

# 17910013627392
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

state = contextvars.ContextVar("state", default=State())


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")  # pyright: ignore


@bot.event
async def on_error(event, *args, _):
    with open("err.log", "a") as f:
        if event == "on_message":
            f.write(f"Unhandled message: {args[0]}\n")
        else:
            raise


@bot.command(name="lfg", help="Look for group")
async def lfg(ctx):
    if ctx.message.channel.type == discord.ChannelType.voice:
        text_channel = ctx.channel
    else:
        await ctx.send("Looking for group? Join a voice channel!")
        return

    group = state.get().get_group(text_channel)
    user_id = ctx.message.author.id
    if group:
        if group.is_owner(user_id):
            await ctx.send("You are already looking for group in this channel!")
            return
        #  TODO: do something if group exists for this channel, but user is not owner
    else:
        state.get().add_group(text_channel, user_id)
        print(f"* Added group in {text_channel} with owner {user_id}")
        print(f"* Groups: {state.get().groups}")

    await ctx.send(f"Looking for group in {text_channel}!")


@bot.command(name="roll_dice", help="Simulates rolling dice.")
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1))) for _ in range(number_of_dice)
    ]
    await ctx.send(", ".join(dice))


bot.run(TOKEN)
