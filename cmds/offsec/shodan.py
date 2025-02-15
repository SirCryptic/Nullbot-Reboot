import discord
from discord.ext import commands
import shodan
import asyncio
from datetime import datetime
import config

# Initialize Shodan API client with API key imported from config
shodan_client = shodan.Shodan(config.SHODAN_API_KEY)

# Track last time a user used the shodan command to prevent spamming
last_used = {}

class ShodanCog(commands.Cog):
    """Shodan related commands for searching IP information."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='shodan')
    @commands.has_role(config.BOT_USER_ROLE)
    async def shodan_search(self, ctx, ip: str = None):
        """Check if an IP exists in Shodan and paginate results."""

        if not ip:
            # Send fancy help message when no IP is provided
            embed = discord.Embed(
                title="🛠️ Shodan Help",
                description="**Shodan Search** - Retrieve detailed information about an IP address using Shodan.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔍 Command Usage",
                value=f"Use `{config.BOT_PREFIX}shodan <IP>` to search for an IP's details.\nExample: `{config.BOT_PREFIX}shodan 8.8.8.8`",
                inline=False
            )
            embed.add_field(
                name="⚙️ Supported Data",
                value="The results will include details such as the organization, location, open ports, operating system, and service banners.",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Additional Info",
                value="You must have the appropriate role to use this command. The command also enforces a cooldown of 15 seconds per user to prevent spamming.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        user_id = ctx.author.id
        current_time = datetime.now()

        # Check if the user has spammed (allow 1 request every 15 seconds)
        if user_id in last_used:
            time_diff = current_time - last_used[user_id]
            if time_diff.total_seconds() < 15:  # Prevent command usage within 15 seconds
                return  # Do nothing, just return without sending the cooldown message

        # Update the last used time for the user
        last_used[user_id] = current_time

        try:
            # Perform a Shodan search for the IP
            result = shodan_client.host(ip)

            # Extract general information
            embed_title = f"Shodan Information for {ip}"
            organization = result.get('org', 'Unknown')
            location = f"{result.get('city', 'Unknown')}, {result.get('country_name', 'Unknown')}"
            ports = ', '.join(map(str, result.get('ports', [])))
            operating_system = result.get('os', 'Unknown')
            services = result.get('data', [])

            # Paginate services if necessary (5 services per page to avoid message limit)
            pages = [services[i:i + 5] for i in range(0, len(services), 5)]
            current_page = 0

            # Function to create embed for a specific page
            def create_embed(page_num):
                embed = discord.Embed(
                    title=embed_title,
                    color=discord.Color.blue()
                )
                embed.add_field(name="IP", value=ip, inline=False)
                embed.add_field(name="Organization", value=organization, inline=False)
                embed.add_field(name="Location", value=location, inline=False)
                embed.add_field(name="Ports", value=ports if ports else "None", inline=False)
                embed.add_field(name="Operating System", value=operating_system, inline=False)

                # Add service details for the current page
                page = pages[page_num]
                for index, service in enumerate(page):
                    port = service.get('port', 'Unknown')
                    service_name = service.get('product', 'Unknown')
                    version = service.get('version', 'Unknown')
                    banner = service.get('data', 'No banner available')

                    service_details = f"**Port:** {port}\n"
                    service_details += f"**Service:** {service_name} {version}\n"
                    service_details += f"**Banner:**\n{banner[:500]}"  # Truncate to avoid exceeding embed limits

                    embed.add_field(name=f"Service {index + 1}", value=service_details, inline=False)

                    footer_text = f"Page {self.current_page + 1} of {len(self.pages)} - {config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name if self.bot.get_user(config.OWNER_ID) else 'Unknown'}"
                    embed.set_footer(
                text=footer_text,
             icon_url=self.bot.user.avatar.url
        )
                return embed

            # Send the first page
            message = await ctx.send(embed=create_embed(current_page))

            # Add reactions for navigation if there are multiple pages
            if len(pages) > 1:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

                def check(reaction, user):
                    return (
                        user == ctx.author
                        and reaction.message.id == message.id
                        and str(reaction.emoji) in ["⬅️", "➡️"]
                    )

                while True:
                    try:
                        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)

                        if str(reaction.emoji) == "⬅️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=create_embed(current_page))

                        elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=create_embed(current_page))

                        # Remove the user's reaction to keep the interface clean
                        await message.remove_reaction(reaction.emoji, user)

                    except asyncio.TimeoutError:
                        # If the user doesn't react within 60 seconds, remove reactions and stop waiting
                        try:
                            await message.clear_reactions()
                        except discord.errors.NotFound:
                            pass
                        break

        except shodan.APIError as e:
            await ctx.send(f"Error: {e}")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(ShodanCog(bot))
