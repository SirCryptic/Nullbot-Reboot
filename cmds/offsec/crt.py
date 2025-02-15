import discord
import requests
from discord.ext import commands
import config

class CertificateTransparencyViewer(commands.Cog):
    """Views Certificate Transparency logs to find subdomains for a given domain."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)  # Ensure user has the required role to use the command
    @commands.command(name="ctv")
    async def ctv(self, ctx, domain: str = None):
        """
        Fetches Certificate Transparency logs for a given domain and displays the related subdomains in a paginated format.
        If no domain is provided, shows help.
        """
        if domain is None:
            # Display help message if no domain is provided
            embed = discord.Embed(
                title="🌐 Certificate Transparency Viewer Help",
                description="**Certificate Transparency Viewer** - Retrieve subdomains for a given domain using crt.sh (Certificate Transparency logs).",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}ctv <domain>` to view Certificate Transparency logs.\nExample: `{config.BOT_PREFIX}ctv example.com`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command finds subdomains listed on **crt.sh**, a public certificate transparency log. This can reveal subdomains associated with a domain.",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Example Subdomains",
                value="Subdomains found may include:\n- **www.example.com**\n- **mail.example.com**\n- **api.example.com**",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            # Fetch data from crt.sh
            url = f"https://crt.sh/?q={domain}&output=json"
            response = requests.get(url, timeout=10)

            # Handle HTTP status code 429 (Rate Limiting)
            if response.status_code == 429:
                error_msg = "⚠️ **Rate Limiting Error (HTTP 429)**: Too many requests made in a short period. Please try again later."
                error_message = await ctx.send(error_msg)
                await error_message.delete(delay=5)  # Delete after 5 seconds
                return

            if response.status_code != 200:
                await ctx.send(f"❌ Failed to fetch Certificate Transparency logs. HTTP Status: {response.status_code}")
                return

            subdomains_data = []
            results = response.json()

            # Extract relevant information from the response
            for entry in results:
                subdomains_data.append({
                    "crt_id": entry.get("id"),
                    "logged_at": entry.get("issued_at"),
                    "not_before": entry.get("not_before"),
                    "not_after": entry.get("not_after"),
                    "common_name": entry.get("common_name"),
                    "matching_identities": entry.get("identities"),
                    "issuer": entry.get("issuer_name")
                })

            # Paginate results if there are multiple subdomains
            if subdomains_data:
                pages = [subdomains_data[i:i + 2] for i in range(0, len(subdomains_data), 2)]  # Limit to 2 fields per page
                current_page = 0
                view = CertificateTransparencyView(pages, current_page, domain, self.bot)  # Pass bot to view
                await view.send(ctx)
            else:
                await ctx.send(f"No subdomains found for {domain}.")

        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")

class CertificateTransparencyView(discord.ui.View):
    """View to handle button interactions for paginated certificate transparency logs."""

    def __init__(self, pages, current_page, domain, bot):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = current_page
        self.domain = domain
        self.bot = bot  # Now we store the bot in the view
        self.message = None

    async def send(self, ctx):
        """Send the initial message and store it for updates."""
        embed = await self.create_embed()
        self.message = await ctx.send(embed=embed, view=self)

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
        """Update the current page of the results."""
        self.children[0].disabled = self.current_page == 0  # Disable Back button on the first page
        self.children[1].disabled = self.current_page == len(self.pages) - 1  # Disable Next button on the last page

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        """Create the embed with certificate transparency log data."""
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"🌐 Certificate Transparency Logs for {self.domain}",
            description="Here are the discovered subdomains in the certificate transparency logs:",
            color=discord.Color.blue()
        )

        # Add only a limited number of fields to avoid hitting the 25-field limit
        for data in page:
            embed.add_field(name="🔑 CRT ID", value=data["crt_id"], inline=False)
            embed.add_field(name="📅 Logged At", value=data["logged_at"], inline=False)
            embed.add_field(name="📅 Not Before", value=data["not_before"], inline=False)
            embed.add_field(name="📅 Not After", value=data["not_after"], inline=False)
            embed.add_field(name="🌐 Common Name", value=data["common_name"], inline=False)
            embed.add_field(name="🏢 Issuer", value=data["issuer"], inline=False)

            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )

        embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.pages)}")
        return embed

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(CertificateTransparencyViewer(bot))
