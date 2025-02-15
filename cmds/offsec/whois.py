import discord
from discord.ext import commands
import requests
import re
import socket
import config

class whois(commands.Cog):
    """Security-related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='whois')
    @commands.has_role(config.BOT_USER_ROLE)
    async def whois(self, ctx, domain: str = None):
        """Fetch and display WHOIS information for a domain."""

        if not domain:
            # Send help message when no domain is provided
            embed = discord.Embed(
                title="🔍 WHOIS Help",
                description="**WHOIS** - Retrieve WHOIS information for a domain or ip address.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}whois <domain/ip>` to fetch WHOIS information.\nExample: `{config.BOT_PREFIX}whois example.com`",
                inline=False
            )
            embed.add_field(
                name="🛠️ Data Provided",
                value="The response will include details such as:\n- IP Address\n- Registrar\n- Country, City, Organization\n- ISP, ASN\n- Timezone, Latitude/Longitude\n- Email addresses and phone numbers",
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
            # Resolve the domain to an IP address
            ip = socket.gethostbyname(domain)

            # Fetch WHOIS data from the API
            response = requests.get(f"https://ipwhois.app/json/{ip}")
            data = response.json()

            if response.status_code == 200 and not data.get('error'):
                # Extract WHOIS details
                country = data.get('country', 'Unknown')
                city = data.get('city', 'Unknown')
                org = data.get('org', 'Unknown')
                isp = data.get('isp', 'Unknown')
                asn = data.get('asn', 'Unknown')
                timezone = data.get('timezone', 'Unknown')
                lat = str(data.get('latitude', 'Unknown'))
                lon = str(data.get('longitude', 'Unknown'))
                registrar = data.get('org', 'Unknown')  # Sometimes 'org' contains the registrar name

                # Extract email and phone numbers using regex
                raw_data = str(data)

                # Get emails from the WHOIS response
                emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zAZ0-9-]+\.[a-zA-Z0-9-.]+", raw_data)

                # Get phone numbers (excluding lat/lon and avoid coordinates)
                phone_numbers = re.findall(r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", raw_data)

                # Filter out phone numbers that look like latitude/longitude (those containing dots)
                phone_numbers = [
                    num for num in phone_numbers
                    if "." not in num  # Ensure the phone number does not contain a dot
                ]

                # Format extracted emails and phones
                emails = ", ".join(set(emails)) if emails else "Not found"
                phone_numbers = ", ".join(set(phone_numbers)) if phone_numbers else "Not found"

                # Construct embed
                embed = discord.Embed(title=f"WHOIS Information for {domain}", color=discord.Color.blue())
                embed.add_field(name="IP Address", value=ip, inline=False)  # Display IP
                embed.add_field(name="Registrar", value=registrar, inline=False)
                embed.add_field(name="Country", value=country, inline=True)
                embed.add_field(name="City", value=city, inline=True)
                embed.add_field(name="Organization", value=org, inline=False)
                embed.add_field(name="ISP", value=isp, inline=False)
                embed.add_field(name="ASN", value=asn, inline=True)
                embed.add_field(name="Timezone", value=timezone, inline=True)
                embed.add_field(name="Latitude", value=lat, inline=True)
                embed.add_field(name="Longitude", value=lon, inline=True)
                embed.add_field(name="Emails", value=f"```{emails}```", inline=False)
                embed.add_field(name="Phone Numbers", value=f"```{phone_numbers}```", inline=False)
                embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )

                await ctx.send(embed=embed)
            else:
                await ctx.send("Error retrieving WHOIS data.")

        except socket.gaierror:
            await ctx.send(f"Could not resolve domain {domain} to an IP address.")
        except Exception as e:
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(whois(bot))
