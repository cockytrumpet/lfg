# pyright: basic
# pyright: ignore[reportUnusedFunction]

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
    from lfg.user import User
    from lfg.utils import logger

    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("DISCORD_TOKEN not set in .env file")
        exit(1)

    intents = discord.Intents.default()
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
        group, text_channel = await get_info(ctx)
        s = state.get()
        user = s.get_user(ctx)

        task = Task(
            user,
            "",
        )

        if not task:
            await ctx.send("Error: No user found!")
            return

        if not text_channel:
            print("Error: No text channel found!")
            return

        if group:
            if group.is_owner(user.id):
                msg = str(group)
                await ctx.send(msg)
                return
            else:
                await ctx.send(
                    f"{user.name}'s group is active in this channel. They can use !yield to transfer ownership."
                )
                return
        else:
            s = state.get()
            s.add_group(ctx.channel, user)

        await ctx.send(f"{user.name} formed group in {ctx.channel}")

    @bot.command(name="yield", help="Transfer ownership")
    async def yieldgroup(ctx, name: str = ""):
        if name == "":
            await ctx.send("Missing name: !yield <name>")
            return

        group, text_channel = await get_info(ctx)

        if not text_channel:
            return
        if not group:
            await ctx.send(f"No group in {text_channel}. Start one with !lfg.")
            return

        if not group.is_owner(ctx.message.author.id):
            await ctx.send(
                f"Group {text_channel} is owned by {ctx.message.author.global_name}"
            )
            return

        s = state.get()
        user = s.get_user_by_name(name)

        if not user or user.nick == "lfg":

            await ctx.send(f"User {name} not found")
            return

        group.set_owner(user)

        await ctx.send(f"Ownership transferred to @{user.nick}")

    @bot.command(name="bye", help="End group")
    async def endgroup(ctx):
        group, text_channel = await get_info(ctx)

        if not text_channel:
            return
        if not group:
            await ctx.send(f"No group in {text_channel}. Start one with !lfg.")
            return

        if not group.is_owner(ctx.message.author.id):
            await ctx.send(
                f"Group {text_channel} is owned by {ctx.message.author.global_name}"
            )
            return

        s = state.get()
        s.get_group(text_channel)
        s.remove_group(text_channel)

        await ctx.send("Group ended!")

    @bot.command(name="remove", help="Remove character or user from queues")
    async def remove(ctx, name: str, roles_str: str = ""):
        s = state.get()
        group, text_channel = await get_info(ctx)
        user = s.get_user(ctx)

        if not group:
            await ctx.send("No group in this channel. Start one with !lfg.")
            return
        if group.owner != user:
            await ctx.send("Only the group owner can remove characters.")
            return

        found_user = s.get_user_by_name(name)

        if found_user and found_user.id != 0:
            group.remove_user(found_user.id)
        else:
            user = s.get_user_by_character(name)
            if user:
                roles = make_roles(roles_str) or [Role.DPS, Role.HEALER, Role.TANK]
                task = Task(user, name)
                group.remove_character(task, roles)

    @bot.command(name="join", help="Join queues (<character> <roles>)")
    async def join(ctx, character: str = "", role_str: str = ""):
        if not character or not role_str:
            await ctx.send("Missing character or roles: !join <character> <roles>")
            return

        s = state.get()
        group, text_channel = await get_info(ctx)

        if not group:
            await ctx.send("No group in this channel. Start one with !lfg.")
            return

        roles: list[Role] = make_roles(role_str)

        user = s.get_user(ctx)
        user.add_character(character, roles)

        task = Task(
            user,
            character,
        )

        s.update_user(user)

        if group:
            q_str = ""
            for role in roles:
                match role:
                    case Role.TANK:
                        if task not in group.tank_queue:
                            group.tank_queue.append(task)
                            q_str += "T"
                    case Role.HEALER:
                        if task not in group.healer_queue:
                            group.healer_queue.append(task)
                            q_str += "H"
                    case Role.DPS:
                        if task not in group.dps_queue:
                            group.dps_queue.append(task)
                            q_str += "D"
            if q_str:
                q_str = f"[{','.join(q_str)}]"

            if not text_channel:
                text_channel = "FIXME"
            logger(text_channel, f"Queue {task} {q_str} in {text_channel}")
            await lfg(ctx)

    @bot.command(name="leave", help="Leave queues (<character> <roles>)")
    async def leave(ctx, character: str = "", role_str: str = ""):
        if character == "":
            await ctx.send("Missing character: !leave <character> <roles>")
            return

        roles: list[Role] = make_roles(role_str) or [Role.DPS, Role.HEALER, Role.TANK]
        group, text_channel = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            user = User(ctx)
            task = Task(user, character)
            group.remove_character(task, roles)

    @bot.command(name="clear", help="Remove all from queues")
    async def clear(ctx):
        group, text_channel = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            group.remove_user(user_id)

    @bot.command(name="tank", help="Get next tank")
    async def get_tank(ctx):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel)

        if group:
            if s.get_user(ctx).id == group.owner:
                if next := group.next_tank():
                    await lfg(ctx)
                    await ctx.send(f"**Next tank: {next} @{next.user.nick}**")
                else:
                    await lfg(ctx)
                    await ctx.send("**No tanks in queue**")
            else:
                await ctx.send(f"Only {group.owner} can request next tank")

    @bot.command(name="healer", help="Get next healer")
    async def get_healer(ctx):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel)

        if group:
            if s.get_user(ctx).id == group.owner:
                if next := group.next_healer():
                    await lfg(ctx)
                    await ctx.send(f"**Next healer: {next} @{next.user.nick}**")
                else:
                    await lfg(ctx)
                    await ctx.send("**No healers in queue**")
            else:
                await ctx.send(f"Only {group.owner} can request next healer")

    @bot.command(name="dps", help="Get next DPS")
    async def get_dps(ctx):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel)

        if group:
            if s.get_user(ctx).id == group.owner:
                if next := group.next_dps():
                    await lfg(ctx)
                    await ctx.send(f"**Next DPS: {next} @{next.user.nick}**")
                else:
                    await lfg(ctx)
                    await ctx.send("**No DPS in queue**")
            else:
                await ctx.send(f"Only {group.owner} can request next DPS")

    @bot.command(name="debug", help="Print debug info")
    async def debug(ctx):
        logger(ctx.channel.name, f"Forward 'debug' for {ctx.message.author.nick}")

        s = state.get()
        await ctx.send(repr(s))

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
