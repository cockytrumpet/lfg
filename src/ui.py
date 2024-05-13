import os

import discord

from lfg.join_ui import JoinView
from lfg.user import User

TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()  # Create a bot object


@bot.slash_command()  # Create a slash command
async def join(ctx: discord.Interaction):
    user = User()
    user.name = ctx.author.name
    user.nick = ctx.author.nick
    user.id = ctx.author.id
    view = JoinView(user)

    await ctx.respond("Select character and roles", view=view, ephemeral=True)
    await view.wait()  # Wait for the user to click the button

    # WARN: Is this needed?
    # if view.submitted is False:
    #     print("Timed out...")
    #     await ctx.respond("Cancelling", ephemeral=True)
    #     return

    await ctx.respond(f"call !join {view.character} {view.roles}")
    view.stop()


bot.run(TOKEN)  # Run the bot
