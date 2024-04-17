# pyright: basic

if __name__ == "__main__" and __package__ is None:
    __package__ = "lfg"


def main():
    import contextvars
    import os
    import random

    import discord
    from discord.ext import commands
    from dotenv import load_dotenv

    from lfg.state import State
    from lfg.user import User

    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("DISCORD_TOKEN not set in .env file")
        exit(1)

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
        user: User = User(ctx.message.author.id, ctx.message.author.name)

        if group:
            if group.is_owner(user.user_id):
                await ctx.send("You are already looking for group in this channel!")
                return
            else:
                #  TODO: do something if owner has left voice channel
                #        transfer ownership to another member?
                await ctx.send(f"{...}'s group already exists in this channel!")
                return
        else:
            state.get().add_group(text_channel, user)
            print(f"* Added group in {text_channel} with owner {user.user_name}")
            print(f"* Groups: {state.get().groups}")

        await ctx.send(f"{user.user_name} is LFG in {text_channel}!")

    @bot.command(name="roll_dice", help="Simulates rolling dice.")
    async def roll(ctx, number_of_dice: int, number_of_sides: int):
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send(", ".join(dice))

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
