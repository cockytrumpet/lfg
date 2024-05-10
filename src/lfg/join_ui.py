import discord
from discord.components import SelectOption

from lfg.user import User


class NewModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            discord.ui.InputText(
                label="Character",
            ),
            *args,
            title="New character",
            **kwargs,
        )

    async def callback(self, interaction: discord.Interaction):
        self.character = self.children[0].value or "ERROR"
        await interaction.response.defer(invisible=True)


class JoinView(discord.ui.View):
    def __init__(self, user: User):
        super().__init__()
        self.tank: bool = False
        self.healer: bool = False
        self.dps: bool = False
        self.character: str = "CHARACTER_UNSET"
        self.options: list[SelectOption] = user.get_select_options() or []

    # TODO: refactor
    def update_options(self):
        if self.options:
            self.children[1].options = []
            for option in self.options:
                self.children[1].append_option(option)
            self.children[1].disabled = False

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
        modal = NewModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.children[0].value != "":
            if self.children[1].disabled:
                self.children[1].disabled = False
            self.character = modal.children[0].value  # pyright: ignore
            self.children[1].add_option(
                label=self.character, value=self.character + "." + self.roles
            )  # pyright: ignore
            await interaction.edit(view=self)

    @discord.ui.string_select(
        placeholder="Recent characters",
        options=[SelectOption(label="deleteme")],
        disabled=True,
    )
    async def select_callback(self, select, interaction):
        self.character, roles = select.values[0].split(".")

        for i in range(2, 5):
            self.children[i].style = discord.ButtonStyle.secondary
        self.tank = self.healer = self.dps = False

        for role in roles:
            match role:
                case "t":
                    self.tank = True
                    self.children[2].style = discord.ButtonStyle.success
                case "h":
                    self.healer = True
                    self.children[3].style = discord.ButtonStyle.success
                case "d":
                    self.dps = True
                    self.children[4].style = discord.ButtonStyle.success

        select.placeholder = self.character
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="🛡️", row=2)
    async def button_callback1(self, button, interaction):
        if self.tank:
            button.style = discord.ButtonStyle.secondary
            self.tank = False
        else:
            button.style = discord.ButtonStyle.success
            self.tank = True

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="⚕️", row=2)
    async def button_callback2(self, button, interaction):
        if self.healer:
            button.style = discord.ButtonStyle.secondary
            self.healer = False
        else:
            button.style = discord.ButtonStyle.success
            self.healer = True

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="🗡️", row=2)
    async def button_callback3(self, button, interaction):
        if self.dps:
            button.style = discord.ButtonStyle.secondary
            self.dps = False
        else:
            button.style = discord.ButtonStyle.success
            self.dps = True

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary, row=3)
    async def confirm_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        # await interaction.response.send_message("Confirming")
        await interaction.response.edit_message(view=self)
        # do stuff
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=3)
    async def cancel_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.edit_message(view=self)
        # await interaction.response.send_message("Cancelling")
        # do stuff
        self.stop()
