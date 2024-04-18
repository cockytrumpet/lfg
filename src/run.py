# pyright: basic
# pyright: ignore[reportUnusedVariable]

if __name__ == "__main__" and __package__ is None:
    __package__ = "lfg"


def main():
    import contextvars
    import os

    import discord
    from discord.ext import commands
    from dotenv import load_dotenv

    from lfg.group import Group
    from lfg.role import Role
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

    # ------------------ helper functions ------------------ #

    async def get_info(ctx) -> tuple[Group | None, str | None]:
        # user: User = User(ctx.message.author.id, ctx.message.author.name, roles)

        if ctx.message.channel.type == discord.ChannelType.voice:
            text_channel = ctx.channel
        else:
            await ctx.send("Looking for group? Join a voice channel!")
            return (None, None)

        group = state.get().get_group(text_channel)

        return (group, text_channel)

    def make_roles(role_str: str) -> list[Role]:
        role_str = role_str.upper()
        roles: list[Role] = []

        if role_str:
            if "T" in role_str:
                roles.append(Role.TANK)
            if "H" in role_str:
                roles.append(Role.HEALER)
            if "D" in role_str:
                roles.append(Role.DPS)

        return roles

    # -------------------- bot commands -------------------- #

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

    @bot.command(name="lfg", help="Start group. e.g. !lfg <character> <THD>")
    async def lfg(ctx):
        user = User(ctx.message.author.id, ctx.message.author.global_name, "", [])
        group, text_channel = await get_info(ctx)

        if not user:
            await ctx.send("Error: No user found!")
            return

        if not text_channel:
            print("Error: No text channel found!")
            return

        if group:
            if group.is_owner(ctx.message.author.id):
                msg = group.__str__()  # BUG: why is this empty?
                await ctx.send(msg)
                return
            else:
                #  TODO: do something if owner has left voice channel
                #        transfer ownership to another member?
                await ctx.send(f"{...}'s group is active in this channel!")
                return
        else:
            s = state.get()
            s.add_group(ctx.channel, user)

        await ctx.send(f"{ctx.message.author.global_name} is LFG in {ctx.channel}!")

    @bot.command(name="bye", help="End the group")
    async def endgroup(ctx):
        group, text_channel = await get_info(ctx)

        if not text_channel:
            return
        if not group:
            await ctx.send(f"No group in {text_channel}. Start one with !lfg.")
            return

        user = group.owner

        if not group.is_owner(ctx.message.author.id):
            await ctx.send(
                f"Group {text_channel} is owned by {ctx.message.author.global_name}"
            )
            return

        s = state.get()
        s.remove_group(ctx.channel)
        print(
            f"* Removed group in {ctx.channel} with owner {ctx.message.author.global_name}"
        )

        await ctx.send("Group ended!")

    @bot.command(name="clear", help="Clear user from queues")
    async def clear(ctx):
        group, text_channel = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            group.remove_user(user_id)

    @bot.command(name="leave", help="Leave queue (!leave <character> <roles>)")
    async def leave(ctx, character: str, role_str: str = ""):
        roles: list[Role] = make_roles(role_str)
        group, text_channel = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            group.remove_character(user_id, character, roles)

    @bot.command(
        name="join",
        help="Set your roles. e.g. !join character THD(for Tank, Healer, DPS)",
    )
    async def join(ctx, character: str, role_str: str):
        roles: list[Role] = make_roles(role_str)
        user = User(
            ctx.message.author.id, ctx.message.author.global_name, character, roles
        )
        group, text_channel = await get_info(ctx)
        if group:
            for role in roles:
                match role:
                    case Role.TANK:
                        if user not in group.tank_queue:
                            group.tank_queue.append(user)
                    case Role.HEALER:
                        if user not in group.healer_queue:
                            group.healer_queue.append(user)
                    case Role.DPS:
                        if user not in group.dps_queue:
                            group.dps_queue.append(user)

    @bot.command(name="debug", help="Print debug info")
    async def debug(ctx):
        s = state.get()
        await ctx.send(repr(s))

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
