# pyright: basic
import os

import discord

from lfg.join_ui import JoinView

TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()  # Create a bot object


@bot.slash_command()  # Create a slash command
async def join(ctx: discord.Interaction):
    view = JoinView()

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
