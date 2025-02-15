import discord
from discord.ext import commands
import requests
import config

class Inspect(commands.Cog):
    """Inspection commands for Discord invites and domain reputation."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='inspect')
    async def inspect(self, ctx, option: str = None, *, item: str = None):
        """
        Inspect Discord invites or domain reputation.
        Usage:
        - Inspect Discord invites: !inspect invite <invite_code_or_url>
        - Inspect domain reputation: !inspect domain <domain>
        """
        if not option or not item:
            # Show help if no arguments are provided
            embed = discord.Embed(
                title="🔍 Inspect Command Help",
                description="Inspect Discord invites or domain reputation.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=(
                    f"**Inspect a Discord invite:** `{config.BOT_PREFIX}inspect invite <invite_code_or_url>`\n"
                    f"**Inspect a domain reputation:** `{config.BOT_PREFIX}inspect domain <domain>`"
                ),
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        if option.lower() == "invite":
            # Inspect Discord invite
            try:
                invite_code = item.split('/')[-1]  # Extract invite code from URL or input
                invite = await self.bot.fetch_invite(invite_code)

                # Create an embed for invite details
                embed = discord.Embed(
                    title="📩 Discord Invite Details",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Code", value=invite.code, inline=False)
                embed.add_field(name="Guild", value=invite.guild.name, inline=False)
                embed.add_field(name="Channel", value=str(invite.channel), inline=False)
                embed.add_field(name="Inviter", value=str(invite.inviter), inline=False)
                embed.add_field(name="Member Count", value=invite.approximate_member_count, inline=True)
                embed.add_field(name="Online Count", value=invite.approximate_presence_count, inline=True)
                embed.add_field(name="URL", value=invite.url, inline=False)
                embed.set_footer(
                    text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                    icon_url=self.bot.user.avatar.url
                )
                await ctx.send(embed=embed)
            except discord.NotFound:
                await ctx.send("❌ Invalid invite code or URL. Please try again.")
            except Exception as e:
                await ctx.send(f"❌ An unexpected error occurred: {e}")

        elif option.lower() == "domain":
            # Inspect domain reputation using VirusTotal
            try:
                domain = item.strip()
                headers = {"x-apikey": config.VIRUSTOTAL_API_KEY}
                response = requests.get(f"https://www.virustotal.com/api/v3/domains/{domain}", headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    attributes = data["data"]["attributes"]

                    # Create an embed for domain details
                    embed = discord.Embed(
                        title=f"🌐 Domain Reputation: {domain}",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Reputation", value=attributes.get("reputation", "Unknown"), inline=False)
                    embed.add_field(
                        name="Last Analysis Date",
                        value=attributes.get("last_analysis_date", "Unknown"),
                        inline=False
                    )
                    embed.add_field(
                        name="Categories",
                        value=", ".join(attributes.get("categories", {}).values()) or "None",
                        inline=False
                    )
                    embed.add_field(
                        name="Tags",
                        value=", ".join(attributes.get("tags", [])) or "None",
                        inline=False
                    )
                    embed.set_footer(
                        text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                        icon_url=self.bot.user.avatar.url
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ Could not retrieve domain reputation for {domain}.")
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

        else:
            # Handle invalid option
            embed = discord.Embed(
                title="❌ Invalid Option",
                description="The option must be either `invite` or `domain`.",
                color=discord.Color.red()
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inspect(bot))
