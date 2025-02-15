import discord
import requests
from discord.ext import commands
import config

class GeoIPLookup(commands.Cog):
    """GeoIP Lookup command to fetch geolocation data for an IP address."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)
    @commands.command(name='geoip')
    async def geoip(self, ctx, ip: str = None):
        """Fetches GeoIP information for a given IP address."""

        if ip is None:
            # Display help message if no IP is provided
            embed = discord.Embed(
                title="🌍 GeoIP Lookup Help",
                description="**GeoIP Lookup** - Fetch geolocation data for an IP address.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}geoip <IP>` to look up an IP address.\nExample: `{config.BOT_PREFIX}geoip 8.8.8.8`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command fetches various details such as:\n- Country & Region\n- City & Timezone\n- ISP & ASN\n- Latitude & Longitude\n- Currency & Languages",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            # Fetch GeoIP data
            url = f"https://ipapi.co/{ip}/json/"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                geo_data = response.json()

                # Create an embed for the GeoIP information
                embed = discord.Embed(
                    title=f"🌎 GeoIP Information for {ip}",
                    color=discord.Color.blue()
                )

                # Add fields from the JSON response to the embed
                embed.add_field(name="🆔 IP Address", value=geo_data.get('ip', 'Unknown'), inline=True)
                embed.add_field(name="🌍 Country", value=f"{geo_data.get('country_name', 'Unknown')} ({geo_data.get('country_code', 'Unknown')})", inline=True)
                embed.add_field(name="🏙 City", value=geo_data.get('city', 'Unknown'), inline=True)
                embed.add_field(name="📍 Region", value=geo_data.get('region', 'Unknown'), inline=True)
                embed.add_field(name="⏳ Timezone", value=geo_data.get('timezone', 'Unknown'), inline=True)
                embed.add_field(name="📌 Latitude / Longitude", value=f"{geo_data.get('latitude', 'Unknown')} / {geo_data.get('longitude', 'Unknown')}", inline=True)
                embed.add_field(name="📡 ISP / ASN", value=f"{geo_data.get('org', 'Unknown')} / {geo_data.get('asn', 'Unknown')}", inline=False)
                embed.add_field(name="💰 Currency", value=f"{geo_data.get('currency', 'Unknown')} ({geo_data.get('currency_name', 'Unknown')})", inline=True)
                embed.add_field(name="🗣 Languages", value=geo_data.get('languages', 'Unknown'), inline=True)
                embed.add_field(name="📞 Calling Code", value=geo_data.get('country_calling_code', 'Unknown'), inline=True)
                embed.add_field(name="👥 Population", value=geo_data.get('country_population', 'Unknown'), inline=True)
                embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Error: Unable to fetch data. HTTP Status: {response.status_code}")

        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(GeoIPLookup(bot))
