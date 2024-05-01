# pyright: basic
import os

import discord
from discord.components import SelectOption

TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()  # Create a bot object


class SelectView(
    discord.ui.View
):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, ctx: discord.Interaction):
        super().__init__()
        self.tank: bool = False
        self.healer: bool = False
        self.dps: bool = False
        self.character: str = "CHARACTER_UNSET"
        self.ctx: discord.Interaction = ctx
        self.options: list[SelectOption] = self.get_options()

    @property
    def roles(self) -> str:
        roles = []
        if self.tank:
            roles.append("t")
        if self.healer:
            roles.append("h")
        if self.dps:
            roles.append("d")
        return "".join(roles)

    @discord.ui.button(
        label="New character...", style=discord.ButtonStyle.secondary, row=0
    )
    async def new_character(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        modal = NewModal(parent=self)
        await interaction.response.send_modal(modal)
        await modal.wait()

        if self.character != "":
            self.children[1].add_option(label=self.character, default=True)
            await interaction.edit(view=self)

    def get_options(self) -> list[SelectOption]:
        options: list[SelectOption] = [
            discord.SelectOption(label="Reinhardt"),
            discord.SelectOption(label="Zarya"),
        ]
        if self.character != "":
            options.append(
                discord.SelectOption(
                    label=self.character,
                    value=self.character,  # default=True
                )
            )

        return options

    @discord.ui.string_select(
        placeholder="Recent characters",
        options=[discord.SelectOption(label=x) for x in ["Holysocks", "Maerah"]],
    )
    async def select_callback(self, select, interaction):
        select.placeholder = select.values[0]
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="🛡️", row=2)
    async def button_callback1(self, button, interaction):
        if button.style == discord.ButtonStyle.secondary:
            button.style = discord.ButtonStyle.success
            self.tank = True
        else:
            button.style = discord.ButtonStyle.secondary
            self.tank = False

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="⚕️", row=2)
    async def button_callback2(self, button, interaction):
        if button.style == discord.ButtonStyle.secondary:
            button.style = discord.ButtonStyle.success
            self.healer = True
        else:
            button.style = discord.ButtonStyle.secondary
            self.healer = False

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="🗡️", row=2)
    async def button_callback3(self, button, interaction):
        if button.style == discord.ButtonStyle.secondary:
            button.style = discord.ButtonStyle.success
            self.dps = True
        else:
            button.style = discord.ButtonStyle.secondary
            self.dps = False

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary, row=3)
    async def confirm_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("Confirming", ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`.
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=3)
    async def cancel_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message("Cancelling", ephemeral=True)
        self.stop()


class NewModal(discord.ui.Modal):
    def __init__(self, *args, parent: SelectView, **kwargs) -> None:
        super().__init__(
            discord.ui.InputText(
                label="Character",
            ),
            *args,
            title="New character",
            **kwargs,
        )
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        # self.character = self.children[0].value or "ERROR"
        self.parent.character = self.children[0].value or "ERROR"
        await interaction.response.defer(invisible=True)
        # await interaction.response.edit_message(view=self.parent)


@bot.slash_command()  # Create a slash command
async def join(ctx: discord.Interaction):
    view = SelectView(ctx)

    await ctx.respond("Select character and roles", view=view)
    await view.wait()  # Wait for the user to click the button
    # FIXME: just seeing what happens
    # if view.submitted is False:
    #     print("Timed out...")
    #     await ctx.respond("Cancelling", ephemeral=True)
    #     return
    #
    await ctx.respond(f"call !join {view.character} {view.roles}")


bot.run(TOKEN)  # Run the bot
