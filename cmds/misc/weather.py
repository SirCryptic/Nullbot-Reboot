import discord
from discord.ext import commands
import requests
import config

class Weather(commands.Cog):
    """Weather-related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='weather')
    async def weather(self, ctx, *, city: str = None):
        """Fetch and display weather information for a given city."""
        
        if not city:
            embed = discord.Embed(
                title="🌤️ Weather Command Help",
                description="Fetch current weather for a city.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}weather <city>` to fetch weather information.\nExample: `{config.BOT_PREFIX}weather London`",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Note",
                value="Ensure the city name is spelled correctly.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Powered by OpenWeatherMap",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            # OpenWeatherMap API setup
            api_key = config.WEATHER_API_KEY  # Your OpenWeatherMap API key
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                # Extract weather details
                weather = data["weather"][0]["description"].capitalize()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]
                country = data["sys"]["country"]

                # Create an embed with weather information
                embed = discord.Embed(
                    title=f"🌤️ Weather in {city.capitalize()}, {country}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="🌡️ Temperature", value=f"{temp}°C (Feels like {feels_like}°C)", inline=False)
                embed.add_field(name="🌧️ Weather", value=weather, inline=False)
                embed.add_field(name="💧 Humidity", value=f"{humidity}%", inline=False)
                embed.add_field(name="🌬️ Wind Speed", value=f"{wind_speed} m/s", inline=False)

                embed.set_footer(
                    text=f"{config.BOT_NAME} - Powered by OpenWeatherMap",
                    icon_url=self.bot.user.avatar.url
                )

                await ctx.send(embed=embed)

            elif data.get("message"):
                # Handle specific OpenWeatherMap errors
                await ctx.send(f"Error: {data['message'].capitalize()}. Please check the city name and try again.")
            else:
                # Handle generic errors
                await ctx.send("Error: Unable to fetch weather data. Please try again later.")

        except Exception as e:
            # Catch any unexpected errors
            await ctx.send(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Weather(bot))
