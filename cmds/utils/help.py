# File: help_cog.py
import discord
from discord.ext import commands
import config

class Help(commands.Cog):
    """Custom help command with organized sections for General, Mod, Dev, and OSINT commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def custom_help(self, ctx):
        """Display the help menu with organized sections and buttons for pagination."""
        
        owner = await self.bot.fetch_user(config.OWNER_ID)  # Fetch bot owner dynamically
        footer_text = f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {owner.name}"

        # General Help Page (Visible to everyone)
        general_embed = discord.Embed(
            title="Help Menu - General Commands",
            description="The following commands are available for everyone:",
            color=discord.Color.blue(),
        )
        general_embed.add_field(name=f"```{config.BOT_PREFIX}encode  <FORMAT> <TEXT>```", value="Encode Your Text.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}decode <FORMAT> <TEXT>```", value="Decode Your Text.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}translate <LANGUAGE_CODE> <TEXT>```", value="Translate a message into another language using google translate.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}convert <AMOUNT> <FROM_CURRENCY> <TO_CURRENCY>```", value="Get the latest converstion rates for money.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}weather <CITY/COUNTRY>```", value="Get the weather for a specific country / city using openweathermap.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}cowsay <CHARACTER> <TEXT>```", value="Generate a cowsay message with a character of your choosing.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}figlet <FONT> <TEXT>```", value="Generate text ASCII ART Using figlet fonts.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}meme```", value="Generate a random meme.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}inspect <TYPE> <INVITE/URL>```", value="Inspect a Discord Invite Or a Domains reputation on VirusTotal.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}info```", value="Displays information about the bot.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}serverinfo```", value="Displays information about the server.", inline=False)
        general_embed.add_field(name=f"```{config.BOT_PREFIX}profile <@/ID>```", value="Fetch OSINT profile information of a Discord user.", inline=False)
        general_embed.set_footer(text=footer_text,
             icon_url=self.bot.user.avatar.url
        )


        # OSINT Commands Page (Visible to everyone)
        osint_embed = discord.Embed(
            title="Help Menu - OSINT Commands",
            description="The following OSINT-related commands are available:",
            color=discord.Color.blue(),
        )
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}shodan <IP_ADDRESS>```", value="Get information based on the provided IP address using Shodan.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}pwned <EMAIL_ADDRESS>```", value="Get breach information using HaveIBeenPwned.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}metadata <FILE_URL>```", value="Extract metadata from files.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}geoip <IP_ADDRESS>```", value="Get GeoIP information.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}whois <IP_ADDRESS/DOMAIN>```", value="Get WHOIS information.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}whatweb <DOMAIN>```", value="Identify technologies used by a website.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}headers <URL>```", value="Fetch and analyze HTTP headers.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}cwvscan <IP_ADDRESS/DOMAIN>```", value="Run a vulnerability scan on a URL or IP address.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}whois <IP_ADDRESS/DOMAIN>```", value="Get WHOIS information for the provided IP address or domain.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}dnslookup <DOMAIN>```", value="Perform a DNS lookup for the given domain and fetch records (A, MX, TXT).", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}opencams <Country_Code>```", value="Search The Web For Open Cameras.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}cmsdetect <DOMAIN>```", value="Detect the CMS of a website and attempt user enumeration.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}acpf <DOMAIN>```", value="Scan a domain for admin panels.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}links <DOMAIN>```", value="Fetches all the links found on the given host's HTML content. This includes internal and external links.", inline=False)
        osint_embed.add_field(name=f"```{config.BOT_PREFIX}vuln_test <DOMAIN> <TEST_TYPE>```", value="Test specific vulnerabilities on a target URL.", inline=False)
        osint_embed.set_footer(text=footer_text,
             icon_url=self.bot.user.avatar.url
        )


        # Help pages initialization
        help_pages = [general_embed, osint_embed]

        # Handle permissions and role-based embeds
        if isinstance(ctx.channel, discord.DMChannel):
            # In DMs
            if ctx.author.id == config.OWNER_ID or ctx.author.id in config.DEV_IDS:
                # Dev Page (Accessible to DEV_IDS and OWNER_ID only)
                dev_embed = discord.Embed(
                    title="Help Menu - Dev Commands",
                    description="The following commands are available for developers only:",
                    color=discord.Color.blue(),
                )
                dev_embed.add_field(name=f"```{config.BOT_PREFIX}lock```", value="Lock the bot to dev users only.", inline=False)
                dev_embed.add_field(name=f"```{config.BOT_PREFIX}unlock```", value="Unlock the bot to all users.", inline=False)
                dev_embed.add_field(name=f"```{config.BOT_PREFIX}adminhelp```", value="List full available commands. [Owner Only]", inline=False)
                dev_embed.set_footer(text=footer_text,
             icon_url=self.bot.user.avatar.url
        )

                help_pages.append(dev_embed)
            # Mod page is excluded in DMs
        else:
            # In servers
            user_roles = [role.name.lower() for role in ctx.author.roles]

            # Mod Page (Accessible to MOD_ROLE, OWNER_ID, or DEV_IDS only)
            if config.MOD_ROLE.lower() in user_roles or ctx.author.guild_permissions.manage_messages or ctx.author.id == config.OWNER_ID or ctx.author.id in config.DEV_IDS:
                mod_embed = discord.Embed(
                    title="Help Menu - Mod Commands",
                    description="The following commands are available for moderators:",
                    color=discord.Color.blue(),
                )
                mod_embed.add_field(name=f"```{config.BOT_PREFIX}modhelp```", value="Lists available moderation commands. [Mod Only]", inline=False)
                mod_embed.set_footer(text=footer_text,
             icon_url=self.bot.user.avatar.url
        )
                help_pages.append(mod_embed)

            # Dev Page (Accessible to DEV_IDS and OWNER_ID only)
            if ctx.author.id == config.OWNER_ID or ctx.author.id in config.DEV_IDS:
                dev_embed = discord.Embed(
                    title="Help Menu - Dev Commands",
                    description="The following commands are available for developers only:",
                    color=discord.Color.blue(),
                )
                dev_embed.add_field(name=f"```{config.BOT_PREFIX}lock```", value="Lock the bot to dev users only.", inline=False)
                dev_embed.add_field(name=f"```{config.BOT_PREFIX}unlock```", value="Unlock the bot to all users.", inline=False)
                dev_embed.add_field(name=f"```{config.BOT_PREFIX}adminhelp```", value="List full available commands. [Owner Only]", inline=False)
                dev_embed.set_footer(text=footer_text,
             icon_url=self.bot.user.avatar.url
        )

                help_pages.append(dev_embed)

        # Send help menu with pagination
        view = HelpView(help_pages)
        await view.send(ctx)

class HelpView(discord.ui.View):
    """View to handle button interactions for pagination."""
    
    def __init__(self, help_pages):
        super().__init__(timeout=120)
        self.embeds = help_pages
        self.current_page = 0
        self.message = None

    async def send(self, ctx):
        """Send the message and store it for pagination."""
        self.message = await ctx.send(embed=self.embeds[0], view=self)

    @discord.ui.button(label="◀️ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous page."""
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next page."""
        self.current_page += 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        """Update the displayed embed based on the current page."""
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.embeds) - 1
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def on_timeout(self):
        """Disable buttons when interaction times out."""
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

# Setup function
async def setup(bot):
    await bot.add_cog(Help(bot))
