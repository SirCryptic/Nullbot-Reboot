import discord
from discord.ext import commands
import pyfiglet
import re
import config

class FunCommands(commands.Cog):
    """Commands for fun and miscellaneous stuff"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="figlet")
    async def figlet_command(self, ctx, font: str = "standard", *, text: str = None):
        """Generate ASCII art from the given text using pyfiglet with a specified font."""
        
        if text is None:
            # Send help message when no text is provided
            embed = discord.Embed(
                title="🎨 Figlet Help",
                description="**Figlet Command** - Generate ASCII art text with different font styles.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}figlet <font> <text>` to generate ASCII art.\nExample: `{config.BOT_PREFIX}figlet slant Hello, World!`",
                inline=False
            )
            embed.add_field(
                name="⚙️ Available Fonts",
                value="You can choose from many fonts. Some popular ones include: `standard`, `slant`, `block`, `big`, `small`, `roman`, and more.",
                inline=False
            )
            embed.add_field(
                name="⚠️ Text Limit",
                value="The text you input should be no longer than 100 characters.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Sanitize the input by removing any non-alphanumeric characters (optional)
        sanitized_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Keep only alphanumeric and spaces

        # Check if the input exceeds the 100-character limit
        if len(sanitized_text) > 100:
            await ctx.send("Text is too long. Please limit it to 100 characters.")
            return

        # Log who used the command in the console
        print(f"Figlet Command invoked by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")

        try:
            # List of available fonts
            available_fonts = pyfiglet.FigletFont.getFonts()

            # Check if the user-provided font is valid
            if font.lower() not in available_fonts:
                await ctx.send(f"❌ Invalid font! Please choose one from the list: {', '.join(available_fonts)}")
                return

            # Generate the ASCII art using pyfiglet and the specified font
            ascii_art = pyfiglet.figlet_format(sanitized_text, font=font)

            # Send the generated ASCII art to the Discord channel
            await ctx.send(f"```\n{ascii_art}\n```")

        except Exception as e:
            await ctx.send(f"❌ Error generating ASCII art: {e}")

async def setup(bot):
    await bot.add_cog(FunCommands(bot))
