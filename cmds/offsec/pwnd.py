import discord
from discord.ext import commands
import requests
import urllib
import config
import asyncio
import config

class Pwned(commands.Cog):
    """Have I Been Pwned related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pwned')
    @commands.has_role(config.BOT_USER_ROLE)
    async def pwned(self, ctx, email: str = None):
        """Check if an email has been pwned and paginate the results."""

        if not email:
            # Send fancy help message when no email is provided
            embed = discord.Embed(
                title="🛡️ Pwned Help",
                description=f"**Have I Been Pwned** - Check if an email has been compromised in known data breaches.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔍 Command Usage",
                value=f"Use `{config.BOT_PREFIX}pwned <email>` to check if an email has been pwned.\nExample: `{config.BOT_PREFIX}pwned example@example.com`",
                inline=False
            )
            embed.add_field(
                name="⚠️ Supported Data",
                value="The results will show details of any breaches the email is involved in, including breach date, data types, and affected domains.",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Additional Info",
                value="You must have the appropriate role to use this command.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # URL encode the email to handle special characters
        encoded_email = urllib.parse.quote(email.strip())
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{encoded_email}?truncateResponse=false"
        headers = {
            "User-Agent": "Discord HIBP Bot",
            "hibp-api-key": config.HIBP_API_KEY  # Use the API key from config.py
        }

        try:
            # Send GET request to Have I Been Pwned API
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                breaches = response.json()

                if breaches:
                    # Paginate results (up to 10 breaches per page)
                    pages = [breaches[i:i + 10] for i in range(0, len(breaches), 10)]
                    current_page = 0

                    # Send the first page
                    view = PwnedView(self.bot, pages, current_page, email)
                    await view.send(ctx)  # Send message and store it in PwnedView

                else:
                    await ctx.send(f"❌ No breaches found for `{email}`.")
            
            elif response.status_code == 404:
                await ctx.send(f"❌ No breaches found for `{email}`.")
            elif response.status_code == 429:
                await ctx.send("⏳ Rate limit exceeded. Please wait and try again later.")
            else:
                await ctx.send(f"⚠️ Error: Unable to check pwned status for `{email}`. Please try again later.")

        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ An error occurred while connecting to the API: {e}")


class PwnedView(discord.ui.View):
    """View to handle button interactions for pagination of pwned breaches."""

    def __init__(self, bot, pages, current_page, email):
        super().__init__(timeout=120)  # Set a 2-minute timeout for interactions
        self.bot = bot  # Pass the bot instance
        self.pages = pages
        self.current_page = current_page
        self.email = email
        self.message = None  # Store the message reference

    async def send(self, ctx):
        """Send the initial message and store it for future edits."""
        embed = self.create_embed(self.current_page)  # Create the embed for the current page
        self.message = await ctx.send(embed=embed, view=self)

    @discord.ui.button(label="◀️ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to the previous page."""
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to the next page."""
        self.current_page += 1
        await self.update_page(interaction)

    def create_embed(self, page_num):
        """Create an embed for the specified page."""
        embed = discord.Embed(
            title=f"💥 Breaches Found for {self.email} - Page {page_num + 1}/{len(self.pages)}",
            description=f"The email `{self.email}` has been found in the following breaches:",
            color=discord.Color.blue()
        )
        for breach in self.pages[page_num]:
            title = breach.get('Title', 'No Title Available')
            breach_date = breach.get('BreachDate', 'Unknown Date')
            data_classes = ', '.join(breach.get('DataClasses', [])) if breach.get('DataClasses') else "No Data Classes"
            domain = breach.get('Domain', 'No Domain Available')

            # Add emoji depending on the breach type
            emoji = "💣" if "hacked" in title.lower() else "⚠️"  # Example condition to decide emoji

            # Show basic breach information
            embed.add_field(
                name=f"{emoji} {title}",
                value=f"Date: {breach_date}\nData Types: {data_classes}\nDomain: {domain}",
                inline=False
            )

        embed.set_footer(
            text=f"Powered by {config.BOT_NAME} - Beta v{config.BOT_VERSION}",
            icon_url=self.bot.user.avatar.url
        )
        return embed

    async def update_page(self, interaction: discord.Interaction):
        """Update the embed based on the current page and handle button states."""
        embed = self.create_embed(self.current_page)  # Create embed for the current page
        self.children[0].disabled = self.current_page == 0  # Disable Back button on first page
        self.children[1].disabled = self.current_page == len(self.pages) - 1  # Disable Next button on last page

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        """Disable buttons when the interaction timeout expires."""
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  # Ignore error if message was deleted


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Pwned(bot))
