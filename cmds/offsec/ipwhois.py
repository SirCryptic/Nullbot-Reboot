import discord
from discord.ext import commands
import requests
import config

class ipwho(commands.Cog):
    """Security-related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='iplookup')
    @commands.has_role(config.BOT_USER_ROLE)
    async def iplookup(self, ctx, ip_address: str = None):
        """Fetch and display IP lookup information from IPWhoIs API."""
        
        if not ip_address:
            # Send help message when no IP address is provided
            embed = discord.Embed(
                title="🌍 IP Lookup Help",
                description="**IP Lookup** - Retrieve detailed information about an IP address.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}iplookup <IP Address>` to fetch IP information.\nExample: `{config.BOT_PREFIX}iplookup 8.8.4.4`",
                inline=False
            )
            embed.add_field(
                name="🛠️ Data Provided",
                value="The response will include details such as:\n- Country\n- Region\n- City\n- Latitude/Longitude\n- ASN\n- ISP\n- Timezone\n- Security (VPN, Proxy, Hosting, etc.)",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Additional Info",
                value="You must have the appropriate role to use this command.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            # Fetch IP information from the IPWhoIs API
            response = requests.get(f"https://ipwho.is/{ip_address}")
            data = response.json()

            if response.status_code == 200 and data.get('success'):
                # Extract details from the API response
                ip = data.get('ip', 'Unknown')
                country = data.get('country', 'Unknown')
                region = data.get('region', 'Unknown')
                city = data.get('city', 'Unknown')
                org = data.get('org', 'Unknown')
                isp = data.get('isp', 'Unknown')
                asn = data.get('asn', 'Unknown')
                timezone = data.get('timezone', {}).get('id', 'Unknown')
                current_time = data.get('timezone', {}).get('current_time', 'Unknown')
                lat = str(data.get('latitude', 'Unknown'))
                lon = str(data.get('longitude', 'Unknown'))
                is_eu = data.get('is_eu', False)
                continent = data.get('continent', 'Unknown')
                postal_code = data.get('postal', 'Unknown')
                calling_code = data.get('calling_code', 'Unknown')
                capital = data.get('capital', 'Unknown')
                borders = data.get('borders', 'Unknown')
                flag_emoji = data.get('flag', {}).get('emoji', '🌐')

                # Security data (VPN, Proxy, TOR, Hosting)
                security = data.get('security', {})
                anonymous = "🛡️ Anonymous" if security.get('anonymous') else "🔓 Not Anonymous"
                proxy = "🕵️ Proxy" if security.get('proxy') else "🔓 No Proxy"
                vpn = "🛡️ VPN" if security.get('vpn') else "🔓 No VPN"
                tor = "🕵️ TOR" if security.get('tor') else "🔓 No TOR"
                hosting = "🏠 Hosting" if security.get('hosting') else "🔓 No Hosting"

                # Construct embed message
                embed = discord.Embed(title=f"🌍 IP Lookup Information for {ip}", color=discord.Color.blue())

                # Group Information into Categories
                embed.add_field(name="🌐 Location", value=f"**Country**: {country} {flag_emoji}\n**Continent**: {continent}\n**Region**: {region}\n**City**: {city}\n**Postal Code**: {postal_code}\n**Capital**: {capital}", inline=False)
                
                embed.add_field(name="📍 Coordinates", value=f"**Latitude**: {lat}\n**Longitude**: {lon}", inline=False)

                embed.add_field(name="🌐 Organization & ISP", value=f"**Organization**: {org}\n**ISP**: {isp}\n**ASN**: {asn}", inline=False)

                embed.add_field(name="🕒 Timezone", value=f"**Timezone**: {timezone}\n**Current Time**: {current_time}", inline=False)

                embed.add_field(name="💬 Additional Info", value=f"**Calling Code**: {calling_code}\n**Borders**: {borders}", inline=False)

                embed.add_field(name="🔒 Security", value=f"{anonymous}\n{proxy}\n{vpn}\n{tor}\n{hosting}", inline=False)

                embed.set_footer(
                    text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                    icon_url=self.bot.user.avatar.url
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send("Error retrieving IP details.")

        except Exception as e:
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(ipwho(bot))
