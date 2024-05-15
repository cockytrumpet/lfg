# TODO: - add categories to !help
#       - migrating to slash commands and/or using 'ephemeral'

from typing import Callable

from discord import ApplicationContext

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
        print("DISCORD_TOKEN not set")
        exit(1)

    bot = discord.Bot()

    state = contextvars.ContextVar("state", default=State())

    # ------------------ helper functions ------------------ #

    async def get_info(
        ctx: discord.ApplicationContext,
    ) -> tuple[Group | None, str | None]:
        # if ctx.message.channel.type == discord.ChannelType.voice:
        if ctx.channel.type == discord.ChannelType.voice:
            text_channel = ctx.channel.name
        else:
            await ctx.respond("Looking for group? Join a voice channel!")
            return (None, None)

        s = state.get()
        group = s.get_group(text_channel)

        return (group, text_channel)

    # FIX: refactor this, oh my
    async def show_group(
        ctx: discord.ApplicationContext,
        title: str = "",
        color: discord.Color = discord.Color.blurple(),
        send: Callable | None = None,
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

        if send is None:
            send = ctx.channel.send
        await send(embed=embed)
        # await ctx.response.edit_message(embeds=[embed])
        # await ctx.channel.send(embed=embed)

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

    @bot.slash_command(name="vote", help="Vote for new group owner")
    async def vote(ctx: discord.ApplicationContext, name: str = ""):
        if name == "":
            await ctx.respond("Missing name: !vote <name>")
            return
        group, text_channel = await get_info(ctx)
        if not text_channel:
            return
        if not group:
            await ctx.respond(f"No group in {text_channel}. Start one with !lfg.")
            return
        s = state.get()
        user = s.get_user_by_name(name)
        if not user or user.nick == "lfg":
            await ctx.respond(f"User {name} not found")
            return
        if user == group.owner:
            await ctx.respond(f"{name} is already the owner")
            return
        group.add_vote(user)
        await ctx.respond(f"{name} has been voted for")

    @bot.slash_command(name="lfg", help="Form group/print status")
    async def lfg(ctx: discord.ApplicationContext):
        group, _ = await get_info(ctx)
        s = state.get()
        user = s.get_user(ctx)

        assert user

        if group:
            # msg = str(group)
            # await ctx.send(msg)
            await ctx.response.defer()
            await show_group(ctx, send=ctx.followup.send)
        else:
            s = state.get()
            s.add_group(ctx.channel.name, user)
            await ctx.respond(f"{user.name} formed group in {ctx.channel}")

    @bot.slash_command(name="yield", help="Transfer ownership")
    async def yieldgroup(ctx: discord.ApplicationContext, name: str = ""):
        if name == "":
            await ctx.respond("Missing name: !yield <name>")
            return

        group, text_channel = await get_info(ctx)

        if not text_channel:
            return
        if not group:
            await ctx.respond(f"No group in {text_channel}. Start one with !lfg.")
            return

        if not group.is_owner(ctx.author.id):
            await ctx.respond(
                f"Group {text_channel} is owned by {ctx.author.global_name}"
            )
            return

        s = state.get()
        user = s.get_user_by_name(name)

        if not user or user.nick == "lfg":

            await ctx.respond(f"User {name} not found")
            return

        group.set_owner(user)

        await ctx.respond(f"Ownership transferred to @{user.nick}")

    @bot.slash_command(name="bye", help="End group")
    async def endgroup(ctx: discord.ApplicationContext):
        group, text_channel = await get_info(ctx)

        if not text_channel:
            return
        if not group:
            await ctx.respond(f"No group in {text_channel}. Start one with !lfg.")
            return

        if not group.is_owner(ctx.author.id):
            user_id = ctx.author.id
            if user_id and group:
                removed = group.remove_user(user_id)
            await ctx.response.defer()
            await show_group(
                ctx,
                color=discord.Color.red() if removed else discord.Color.blurple(),
                send=ctx.followup.send,
            )

        s = state.get()
        s.remove_group(text_channel)

        await ctx.respond("Group ended!")

    @bot.slash_command(name="unjoin", help="Remove character from queues")
    async def unjoin(
        ctx: discord.ApplicationContext,
        name: str,
        roles_str: str,
    ):
        s = state.get()
        group, _ = await get_info(ctx)
        user = s.get_user(ctx)

        if not group:
            await ctx.respond("No group in this channel. Start one with !lfg.")
            return
        if group.owner != user:
            await ctx.respond("Only the group owner can remove characters.")
            return

        found_user = s.get_user_by_name(name)

        if found_user and found_user.id:
            removed = group.remove_user(found_user.id)
        else:
            user = s.get_user_by_character(name)
            if user:
                roles = user.str_to_roles(roles_str) or [
                    Role.DPS,
                    Role.HEALER,
                    Role.TANK,
                ]
                task = Task(user, name)
                removed = group.remove_character(task, roles)

        await ctx.response.defer()
        await show_group(
            ctx,
            color=(
                discord.Color.red() if not removed else discord.Color.blurple()
            ),  # why is this backward?
            send=ctx.followup.send,
        )

    @bot.slash_command(name="join", help="Join queues (<character> <roles>)")
    async def join(
        ctx: discord.ApplicationContext, character: str = "", role_str: str = ""
    ):
        s = state.get()
        s.reload_users()
        user = s.get_user(ctx)
        group, text_channel = await get_info(ctx)

        assert user

        if not group:
            await ctx.respond("No group in this channel. Start one with !lfg.")
            return

        if not character and not role_str:
            view = JoinView(user)
            view.update_options()

            await ctx.respond("Select character and roles", view=view, ephemeral=True)
            await view.wait()  # Wait for the user to click the button

            character = view.character
            role_str = view.roles

            if not character or not role_str:
                # delete the message if no character
                # await ctx.message.delete()
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

    # @bot.slash_command(name="leave", help="Leave queues (<character> <roles>)")
    # async def leave(
    #     ctx: discord.ApplicationContext, character: str = "", role_str: str = ""
    # ):
    #     if character == "":
    #         await ctx.respond("Missing character: !leave <character> <roles>")
    #         return
    #
    #     not_removed = True
    #     s = state.get()
    #     user = s.get_user(ctx)
    #     group, _ = await get_info(ctx)
    #     roles = (
    #         user.str_to_roles(role_str)
    #         if user
    #         else [
    #             Role.DPS,
    #             Role.HEALER,
    #             Role.TANK,
    #         ]
    #     )
    #     if group:
    #         user = User(ctx)
    #         task = Task(user, character)
    #         not_removed = group.remove_character(task, roles)
    #     await ctx.response.defer()
    #     await show_group(
    #         ctx,
    #         color=discord.Color.blurple() if not_removed else discord.Color.red(),
    #         send=ctx.followup.send,
    #     )

    @bot.slash_command(name="clear", help="Remove all user's characters")
    async def clear(ctx: discord.ApplicationContext):
        group, _ = await get_info(ctx)
        user_id = ctx.author.id
        if user_id and group:
            removed = group.remove_user(user_id)
        await ctx.response.defer()
        await show_group(
            ctx,
            color=discord.Color.red() if removed else discord.Color.blurple(),
            send=ctx.followup.send,
        )

    @bot.slash_command(name="tank", help="Get next tank")
    async def get_tank(ctx: discord.ApplicationContext):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel.name)

        if group:
            if s.get_user(ctx) == group.owner:
                await ctx.response.defer()

                if next := group.next_tank():
                    # await ctx.send(f"@{next.user.nick}")
                    await show_group(ctx, f"Next tank:  {next}", send=ctx.followup.send)
                else:
                    await show_group(
                        ctx,
                        "No tanks in queue!",
                        color=discord.Color.red(),
                        send=ctx.followup.send,
                    )
                    # await ctx.send("**No tanks in queue!**")
            else:
                await ctx.respond(f"Only {group.owner} can request next tank")

    @bot.slash_command(name="healer", help="Get next healer")
    async def get_healer(ctx: discord.ApplicationContext):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel.name)

        if group:
            if s.get_user(ctx) == group.owner:
                await ctx.response.defer()

                if next := group.next_healer():
                    await show_group(
                        ctx, f"Next healer: {next}", send=ctx.followup.send
                    )
                else:
                    await show_group(
                        ctx,
                        "No healers in queue!",
                        color=discord.Color.red(),
                        send=ctx.followup.send,
                    )
            else:
                await ctx.respond(f"Only {group.owner} can request next healer")

    @bot.slash_command(name="dps", help="Get next DPS")
    async def get_dps(ctx: discord.ApplicationContext):
        s: State = state.get()
        group: Group | None = s.get_group(ctx.channel.name)

        if group:
            if s.get_user(ctx) == group.owner:
                await ctx.response.defer()

                if next := group.next_dps():
                    await show_group(ctx, f"Next DPS: {next}", send=ctx.followup.send)
                else:
                    await show_group(
                        ctx,
                        "No DPS in queue!",
                        color=discord.Color.red(),
                        send=ctx.followup.send,
                    )
            else:
                await ctx.respond(f"Only {group.owner} can request next DPS")

    @bot.slash_command(name="debug", help="Print debug info", hidden=True)
    async def debug(ctx: discord.ApplicationContext):
        logger(
            ctx.channel.name,
            f"Forward 'debug' for {ctx.author.nick}",  # pyright: ignore
        )

        s = state.get()
        await ctx.respond(repr(s))

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
