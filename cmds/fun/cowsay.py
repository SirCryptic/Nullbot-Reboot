import discord
from discord.ext import commands
import cowsay
import re
import io
import sys
import config

class FunCommands(commands.Cog):
    """Commands for fun and miscellaneous stuff"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cowsay")
    async def cowsay_command(self, ctx, character: str = "cow", *, text: str = None):
        """Generate a cowsay message with sanitized input, allowing different characters like 'cow', 'tux', 'fish'."""
        
        if text is None:
            # Send help message when no text is provided
            embed = discord.Embed(
                title="🐄 Cowsay Help",
                description="**Cowsay Command** - Generate a message using a cow or other characters.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}cowsay <character> <message>` to generate a cowsay message.\nExample: `{config.BOT_PREFIX}cowsay cow Hello World`",
                inline=False
            )
            embed.add_field(
                name="🐮 Available Characters",
                value="You can choose from the following characters:\nbeavis, cheese, cow, daemon, dragon, fox, ghostbusters, kitty, meow, miki, milk, octopus, pig, stegosaurus, stimpy, trex, turkey, turtle, tux",
                inline=False
            )
            embed.add_field(
                name="⚠️ Text Limit",
                value="The text you input should be no longer than 25 characters.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # List of valid characters
        valid_characters = ['beavis', 'cheese', 'cow', 'daemon', 'dragon', 'fox', 'ghostbusters', 'kitty',
                             'meow', 'miki', 'milk', 'octopus', 'pig', 'stegosaurus', 'stimpy', 'trex', 
                             'turkey', 'turtle', 'tux']
        
        # Check if the specified character is valid
        if character not in valid_characters:
            await ctx.send(f"Invalid character! Please choose one of the following: {', '.join(valid_characters)}")
            return

        # Sanitize the input by removing any non-alphanumeric characters
        sanitized_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Keep only alphanumeric and spaces

        # Check if the input exceeds the 25-character limit
        if len(sanitized_text) > 25:
            await ctx.send("Text is too long. Please limit it to 25 characters.")
            return

        # Log who used the command in the console
        print(f"Cowsay Command invoked by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")

        # Redirect stdout to suppress any console output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Generate the cowsay message using the specified character and sanitized input
            char_func = getattr(cowsay, character, cowsay.cow)  # Default to 'cow' if the character is invalid
            char_func(sanitized_text)
        except TypeError:
            await ctx.send("An error occurred while processing the cowsay message.")
            sys.stdout = old_stdout  # Reset stdout
            return

        # Get the output from StringIO (this is the cowsay message)
        message = sys.stdout.getvalue()

        # Reset stdout back to the original
        sys.stdout = old_stdout
        
        # Send the cowsay message to the Discord channel (not DM)
        await ctx.send(f"```{message}```")

async def setup(bot):
    await bot.add_cog(FunCommands(bot))
