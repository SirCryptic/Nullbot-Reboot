import discord
from discord.ext import commands
import requests
import config

class CurrencyConverter(commands.Cog):
    """Currency Conversion commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='convert')
    async def convert(self, ctx, amount: float = None, from_currency: str = None, to_currency: str = None):
        """
        Convert an amount from one currency to another.
        """
        if not amount or not from_currency or not to_currency:
            # Show help message if arguments are missing
            embed = discord.Embed(
                title="💱 Currency Converter Help",
                description="Convert an amount from one currency to another.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}convert <amount> <from_currency> <to_currency>` to convert.\n"
                      f"Example: `{config.BOT_PREFIX}convert 100 USD EUR`",
                inline=False
            )
            embed.add_field(
                name="💡 Note",
                value="Ensure the currency codes follow ISO 4217 format (e.g., USD, EUR, GBP).",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Powered by Exchangerate.host",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            # API setup and request
            api_key = config.CURRENCY_API_KEY  # Get the API key from the config
            url = f"https://api.exchangerate.host/convert?from={from_currency.upper()}&to={to_currency.upper()}&amount={amount}&access_key={api_key}"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                # Extract conversion details
                converted_amount = data.get("result", None)
                rate = data.get("info", {}).get("quote", None)

                if converted_amount is not None and rate is not None:
                    # Create an embed with conversion information
                    embed = discord.Embed(
                        title="💱 Currency Converter",
                        description=f"{amount} {from_currency.upper()} is equal to {converted_amount:.2f} {to_currency.upper()}",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="💵 Exchange Rate", value=f"1 {from_currency.upper()} = {rate:.4f} {to_currency.upper()}", inline=False)
                    embed.set_footer(
                        text=f"{config.BOT_NAME} - Powered by Exchangerate.host",
                        icon_url=self.bot.user.avatar.url
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Error: Unable to fetch conversion rate. Please try again later.")
            else:
                # Handle specific API errors
                error_message = data.get("error", {}).get("info", "An unknown error occurred.")
                await ctx.send(f"Error: {error_message}. Please check your input and try again.")

        except Exception as e:
            # Catch any unexpected errors
            await ctx.send(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(CurrencyConverter(bot))
