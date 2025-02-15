import discord
import requests
from discord.ext import commands
import config

class test(commands.Cog):
    """Website Technology Lookup command to identify technologies used by a website."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)
    @commands.command(name="test")
    async def test(self, ctx, domain: str = None):
        """Identifies technologies used by a website based on HTTP headers."""

        if domain is None:
            # Display help message if no domain is provided
            embed = discord.Embed(
                title="🌐 WhatWeb Lookup Help",
                description="**WhatWeb Lookup** - Identify the technologies used by a website.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}whatweb <domain>` to analyze a website.\nExample: `{config.BOT_PREFIX}whatweb example.com`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command extracts:\n- Web Server Technology\n- X-Powered-By Information (Frameworks, Languages, etc.)",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}"
            )
            await ctx.send(embed=embed)
            return

        try:
            # Validate and format the domain
            if not domain.startswith("http://") and not domain.startswith("https://"):
                domain = "http://" + domain

            response = requests.get(domain, timeout=10)
            headers = response.headers

            # Extract some basic technology information
            server = headers.get("Server", "Unknown")
            x_powered_by = headers.get("X-Powered-By", "Unknown")

            # Embed the results
            embed = discord.Embed(
                title=f"🌍 Website Technology for {domain}",
                description="The following technologies were detected:",
                color=discord.Color.blue()
            )
            embed.add_field(name="🖥 Server", value=server, inline=True)
            embed.add_field(name="⚙️ X-Powered-By", value=x_powered_by, inline=True)
            embed.set_footer(text="🔍 Data extracted from HTTP Headers")

            await ctx.send(embed=embed)

        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Error fetching data from the website: {e}")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(test(bot))
