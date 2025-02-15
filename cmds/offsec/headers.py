import discord
import requests
from discord.ext import commands
import config

class HTTPHeaders(commands.Cog):
    """Fetch and analyze HTTP headers for a given URL."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)
    @commands.command(name="headers")
    async def headers(self, ctx, url: str = None):
        """Fetches HTTP headers for the given URL and displays them in an embed."""

        if url is None:
            # Display help message if no URL is provided
            embed = discord.Embed(
                title="📡 HTTP Headers Help",
                description="**HTTP Headers** - Retrieve and analyze HTTP headers for a given website.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}headers <url>` to fetch headers.\nExample: `{config.BOT_PREFIX}headers example.com`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command extracts:\n- Server headers\n- Security-related headers\n- Cache and encoding details",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            # Ensure the URL is properly formatted
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url

            # Fetch headers
            response = requests.head(url, timeout=10)
            headers = response.headers

            # Create an embed for the headers
            embed = discord.Embed(
                title=f"📡 HTTP Headers for {url}",
                description="The following headers were retrieved:",
                color=discord.Color.blue()
            )

            # Add headers to the embed (handling Discord's field limit)
            for key, value in headers.items():
                if len(value) > 1024:  # Truncate long values
                    value = value[:1021] + "..."
                embed.add_field(name=key, value=value, inline=False)

            await ctx.send(embed=embed)

        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Error fetching headers: {e}")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(HTTPHeaders(bot))
