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

    from lfg.group import Group
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

    # -------------------- end setup -------------------- #

    async def get_info(ctx) -> tuple[User | None, Group | None, str | None]:
        user: User = User(ctx.message.author.id, ctx.message.author.name)

        if ctx.message.channel.type == discord.ChannelType.voice:
            text_channel = ctx.channel
        else:
            await ctx.send("Looking for group? Join a voice channel!")
            return (user, None, None)

        group = state.get().get_group(text_channel)

        return (user, group, text_channel)

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
        user, group, text_channel = await get_info(ctx)

        if not user:
            await ctx.send("Error: No user found!")
            return

        if not text_channel:
            return

        if group:
            if group.is_owner(user.user_id):
                await ctx.send("You are already looking for group in this channel!")
                return
            else:
                #  TODO: do something if owner has left voice channel
                #        transfer ownership to another member?
                await ctx.send(f"{...}'s group is active in this channel!")
                return
        else:
            state.get().add_group(ctx.channel, user)
            print(f"* Added group in {ctx.channel} with owner {user.user_name}")
            print(f"* Groups: {state.get().groups}")

        await ctx.send(f"{user.user_name} is LFG in {ctx.channel}!")

    @bot.command(name="end", help="End the group")
    async def endgroup(ctx):
        # check if active in this channel
        # check if user is owner
        #   false: say no and return
        # remove group
        user, group, text_channel = await get_info(ctx)

        if not text_channel:
            return

        if not user:
            await ctx.send("Error: No user found!")
            return

        if not group:
            await ctx.send("Error: No group found!")
            return

        if not group.is_owner(user.user_id):
            await ctx.send("Error: You are not the owner of this group!")
            return

        state.get().remove_group(ctx.channel)
        print(f"* Removed group in {ctx.channel} with owner {user.user_name}")
        print(f"* Groups: {state.get().groups}")

        await ctx.send("Group ended!")

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
