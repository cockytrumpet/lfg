# pyright: reportUnusedFunction=false
# TODO: - add categories to !help
#       - migrating to slash commands and/or using 'ephemeral'

if __name__ == "__main__" and __package__ is None:
    __package__ = "lfg"


def main():
    import contextvars
    import os

    import discord
    from discord.ext import commands, tasks
    from discord.ext.commands import Context

    from lfg.group import Group
    from lfg.join_ui import JoinView
    from lfg.role import Role

    # from lfg.show_ui import ShowView
    from lfg.state import State
    from lfg.task import Task
    from lfg.user import User
    from lfg.utils import logger

    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("DISCORD_TOKEN not set in .env file")
        exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    state = contextvars.ContextVar("state", default=State())

    # ------------------ helper functions ------------------ #

    async def get_info(ctx: Context) -> tuple[Group | None, str | None]:
        if ctx.message.channel.type == discord.ChannelType.voice:
            text_channel = ctx.channel
        else:
            await ctx.send("Looking for group? Join a voice channel!")
            return (None, None)

        s = state.get()
        group = s.get_group(text_channel.name)

        return (group, text_channel.name)

    # FIX: refactor this, oh my
    async def show_group(
        ctx: Context, title: str = "", color: discord.Color = discord.Color.blurple()
    ) -> None:
        group, _ = await get_info(ctx)
        fields = []

        tank = list(group.tank_queue) if group else []
        healer = list(group.healer_queue) if group else []
        dps = list(group.dps_queue) if group else []

        fields.extend(
            [
                discord.EmbedField(
                    name="Tank",
                    value="\n".join(str(task) for task in tank),
                    inline=True,
                ),
                discord.EmbedField(
                    name="Healer",
                    value="\n".join(str(task) for task in healer),
                    inline=True,
                ),
                discord.EmbedField(
                    name="DPS",
                    value="\n".join(str(task) for task in dps),
                    inline=True,
                ),
            ]
        )

        embed = discord.Embed(
            title=title if title else None,
            fields=fields,
            color=color,
        )
        await ctx.send(embeds=[embed])

    # -------------------- bot commands -------------------- #

    @tasks.loop(seconds=10)
    async def on_timer():
        s = state.get()

        for group in s.groups:
            if new_owner := group.check_votes():
                group.set_owner(new_owner)

    @bot.event
    async def on_ready():
        print(f"* {bot.user.name} connected to Discord")  # pyright: ignore
        on_timer.start()

    @bot.event
    async def on_error(event, *args, _):
        with open("err.log", "a") as f:
            if event == "on_message":
                f.write(f"Unhandled message: {args[0]}\n")
            else:
                raise

    @bot.command(name="vote", help="Vote for new group owner")
    async def vote(ctx: Context, name: str = ""):
        if name == "":
            await ctx.send("Missing name: !vote <name>")
            return
        group, text_channel = await get_info(ctx)
        if not text_channel:
            return
        if not group:
            await ctx.send(f"No group in {text_channel}. Start one with !lfg.")
            return
        s = state.get()
        user = s.get_user_by_name(name)
        if not user or user.nick == "lfg":
            await ctx.send(f"User {name} not found")
            return
        if user == group.owner:
            await ctx.send(f"{name} is already the owner")
            return
        group.add_vote(user)
        await ctx.send(f"{name} has been voted for")

    @bot.command(name="lfg", help="Form group/print status")
    async def lfg(ctx: Context):
        group, _ = await get_info(ctx)
        s = state.get()
        user = s.get_user(ctx)

        assert user

        if group:
            # msg = str(group)
            # await ctx.send(msg)
            await show_group(ctx)
        else:
            s = state.get()
            s.add_group(ctx.channel.name, user)
            await ctx.send(f"{user.name} formed group in {ctx.channel}")

    @bot.command(name="yield", help="Transfer ownership")
    async def yieldgroup(ctx: Context, name: str = ""):
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
    async def endgroup(ctx: Context):
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
    async def remove(ctx: Context, name: str, roles_str: str = ""):
        s = state.get()
        group, _ = await get_info(ctx)
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
                roles = user.str_to_roles(roles_str) or [
                    Role.DPS,
                    Role.HEALER,
                    Role.TANK,
                ]
                task = Task(user, name)
                group.remove_character(task, roles)

    @bot.command(name="join", help="Join queues (<character> <roles>)")
    async def join(ctx: Context, character: str = "", role_str: str = ""):
        s = state.get()
        s.reload_users()
        user = s.get_user(ctx)
        group, text_channel = await get_info(ctx)

        assert user

        if not group:
            await ctx.send("No group in this channel. Start one with !lfg.")
            return

        if not character and not role_str:
            view = JoinView(user)
            view.update_options()

            await ctx.send("Select character and roles", view=view)
            await view.wait()  # Wait for the user to click the button

            character = view.character
            role_str = view.roles

            if not character or not role_str:
                # delete the message if no character
                await ctx.message.delete()
                return

            user.add_character(character, user.str_to_roles(view.roles))
            s.update_user(user)

            # view.stop()

        roles: list[Role] = user.str_to_roles(role_str)
        task = Task(
            user,
            character,
        )

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
            await show_group(ctx, color=discord.Color.green())
            # await ctx.message.delete()  # TODO: delete this UI stuff somehow

    @bot.command(name="leave", help="Leave queues (<character> <roles>)")
    async def leave(ctx: Context, character: str = "", role_str: str = ""):
        if character == "":
            await ctx.send("Missing character: !leave <character> <roles>")
            return

        s = state.get()
        user = s.get_user(ctx)
        group, _ = await get_info(ctx)
        roles = (
            user.str_to_roles(role_str)
            if user
            else [
                Role.DPS,
                Role.HEALER,
                Role.TANK,
            ]
        )
        if group:
            user = User(ctx)
            task = Task(user, character)
            group.remove_character(task, roles)

    @bot.command(name="clear", help="Remove all from queues")
    async def clear(ctx: Context):
        group, _ = await get_info(ctx)
        user_id = ctx.message.author.id
        if user_id and group:
            group.remove_user(user_id)

    @bot.command(name="tank", help="Get next tank")
    async def get_tank(ctx: Context):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel.name)

        if group:
            if s.get_user(ctx) == group.owner:
                if next := group.next_tank():
                    await ctx.send(f"@{next.user.nick}")
                    await show_group(ctx, f"Next tank: {next}")
                else:
                    await show_group(
                        ctx, "No tanks in queue!", color=discord.Color.red()
                    )
                    # await ctx.send("**No tanks in queue!**")
            else:
                await ctx.send(f"Only {group.owner} can request next tank")

    @bot.command(name="healer", help="Get next healer")
    async def get_healer(ctx: Context):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel.name)

        if group:
            if s.get_user(ctx) == group.owner:
                if next := group.next_healer():
                    await ctx.send(f"@{next.user.nick}")
                    await show_group(ctx, f"Next healer: {next}")
                else:
                    await show_group(
                        ctx, "No healers in queue!", color=discord.Color.red()
                    )
            else:
                await ctx.send(f"Only {group.owner} can request next healer")

    @bot.command(name="dps", help="Get next DPS")
    async def get_dps(ctx: Context):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel.name)

        if group:
            if s.get_user(ctx) == group.owner:
                if next := group.next_dps():
                    await ctx.send(f"@{next.user.nick}")
                    await show_group(ctx, f"Next DPS: {next}")
                else:
                    await show_group(ctx, "No DPS in queue!", color=discord.Color.red())
            else:
                await ctx.send(f"Only {group.owner} can request next DPS")

    @bot.command(name="debug", help="Print debug info", hidden=True)
    async def debug(ctx: Context):
        logger(
            ctx.channel.name,
            f"Forward 'debug' for {ctx.message.author.nick}",  # pyright: ignore
        )

        s = state.get()
        await ctx.send(repr(s))

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
