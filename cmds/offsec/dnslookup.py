import discord
from discord.ext import commands
import dns.resolver
import config

class DNSLookup(commands.Cog):
    """DNS Lookup command to fetch DNS records (A, MX, TXT)."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)
    @commands.command(name='dnslookup')
    async def dnslookup(self, ctx, domain: str = None):
        """Performs a DNS lookup for A, MX, and TXT records for a given domain."""

        if domain is None:
            # Send help message when no domain is provided
            embed = discord.Embed(
                title="🌐 DNS Lookup Help",
                description="**DNS Lookup** - Fetch DNS records (A, MX, TXT) for a domain.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}dnslookup <domain>` to perform a DNS lookup.\nExample: `{config.BOT_PREFIX}dnslookup example.com`",
                inline=False
            )
            embed.add_field(
                name="⚠️ Available Records",
                value="The command fetches the following DNS records:\n- A (IPv4 addresses)\n- MX (Mail Exchange servers)\n- TXT (Text records, often used for SPF, DKIM, etc.)",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        try:
            result = ""
            # A Records (IPv4 addresses)
            for rdata in dns.resolver.resolve(domain, 'A'):
                result += f"A Record: {rdata.address}\n"
            
            # MX Records (Mail Exchange servers)
            for rdata in dns.resolver.resolve(domain, 'MX'):
                result += f"MX Record: {rdata.exchange}\n"
            
            # TXT Records (Text records, typically used for SPF, DKIM, etc.)
            for rdata in dns.resolver.resolve(domain, 'TXT'):
                result += f"TXT Record: {rdata.to_text()}\n"

            if result:
                embed = discord.Embed(title=f"DNS Lookup for {domain}", description=result, color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No DNS records found for {domain}.")
        
        except Exception as e:
            await ctx.send(f"Error: {e}")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(DNSLookup(bot))
