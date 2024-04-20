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
    from lfg.task import Task

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
        if ctx.message.channel.type == discord.ChannelType.voice:
            text_channel = ctx.channel
        else:
            await ctx.send("Looking for group? Join a voice channel!")
            return (None, None)

        s = state.get()
        group = s.get_group(text_channel)

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
        print(f"* {bot.user.name} connected to Discord")  # pyright: ignore

    @bot.event
    async def on_error(event, *args, _):
        with open("err.log", "a") as f:
            if event == "on_message":
                f.write(f"Unhandled message: {args[0]}\n")
            else:
                raise

    @bot.command(name="lfg", help="Form group/print status")
    async def lfg(ctx):
        print(f"* Forwarded 'lfg' for {ctx.message.author.nick}")
        task = Task(
            ctx.message.author.id,
            ctx.message.author.global_name,
            ctx.message.author.nick,
            "",
            [],
        )
        group, text_channel = await get_info(ctx)

        if not task:
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
            s.add_group(ctx.channel, task)

        await ctx.send(f"{ctx.message.author.global_name} is LFG in {ctx.channel}!")

    @bot.command(name="bye", help="End group")
    async def endgroup(ctx):
        print(f"* Forwarded 'bye' for {ctx.message.author.nick}")

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

    @bot.command(name="clear", help="Remove all from queues")
    async def clear(ctx):
        print(f"* Forwarded 'clear' for {ctx.message.author.nick}")

        group, text_channel = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            group.remove_user(user_id)

    @bot.command(name="leave", help="Leave queues (<character> <roles>)")
    async def leave(ctx, character: str = "", role_str: str = ""):
        print(f"* Forwarded 'lfg' for {ctx.message.author.nick}")

        if character == "":
            await ctx.send("Missing character: !leave <character> <roles>")
            return

        roles: list[Role] = make_roles(role_str) or [Role.DPS, Role.HEALER, Role.TANK]
        group, text_channel = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            task = Task(ctx.message.author.id, "", "", character, roles)
            group.remove_character(task, roles)

    @bot.command(name="join", help="Join queues (<character> <roles>)")
    async def join(ctx, character: str = "", role_str: str = ""):
        print(f"* Forwarded 'join' for {ctx.message.author.nick}")

        if not character or not role_str:
            await ctx.send("Missing character or roles: !join <character> <roles>")
            return

        roles: list[Role] = make_roles(role_str)
        task = Task(
            ctx.message.author.id,
            ctx.message.author.global_name,
            ctx.message.author.nick,
            character,
            roles,
        )
        group, text_channel = await get_info(ctx)
        if group:
            for role in roles:
                match role:
                    case Role.TANK:
                        if task not in group.tank_queue:
                            group.tank_queue.append(task)
                    case Role.HEALER:
                        if task not in group.healer_queue:
                            group.healer_queue.append(task)
                    case Role.DPS:
                        if task not in group.dps_queue:
                            group.dps_queue.append(task)
            print(f"* Joined {task} to {text_channel}")
            await lfg(ctx)

    @bot.command(name="debug", help="Print debug info")
    async def debug(ctx):
        print(f"* Forwarded 'debug' for {ctx.message.author.nick}")

        s = state.get()
        await ctx.send(repr(s))

    @bot.command(name="tank", help="Get next tank")
    async def get_tank(ctx):
        print(f"* Forwarded 'tank' for {ctx.message.author.nick}")

        s: State = state.get()
        g: Group | None = s.get_group(ctx.channel)

        if g:
            if next := g.next_tank():
                await lfg(ctx)
                await ctx.send(f"**Next tank: {next} @{next.disc_name}**")
            else:
                await lfg(ctx)
                await ctx.send("**No tanks in queue**")

    @bot.command(name="healer", help="Get next healer")
    async def get_healer(ctx):
        print(f"* Forwarded 'healer' for {ctx.message.author.nick}")

        s: State = state.get()
        g: Group | None = s.get_group(ctx.channel)

        if g:
            if next := g.next_healer():
                await lfg(ctx)
                await ctx.send(f"**Next healer: {next} @{next.disc_name}**")
            else:
                await lfg(ctx)
                await ctx.send("**No healers in queue**")

    @bot.command(name="dps", help="Get next DPS")
    async def get_dps(ctx):
        print(f"* Forwarded 'dps' for {ctx.message.author.nick}")

        s: State = state.get()
        g: Group | None = s.get_group(ctx.channel)

        if g:
            if next := g.next_dps():
                await lfg(ctx)
                await ctx.send(f"**Next DPS: {next} @{next.disc_name}**")
            else:
                await lfg(ctx)
                await ctx.send("No DPS in queue")

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
