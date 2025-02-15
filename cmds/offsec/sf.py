import discord
import requests
import socket
from discord.ext import commands
import config
import time

class SubdomainFinder(commands.Cog):
    """Finds subdomains for a given domain and resolves their IP addresses."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)  # Ensure user has the required role to use the command
    @commands.command(name="subfinder")
    async def subfinder(self, ctx, domain: str = None):
        """
        Fetches subdomains for a given domain using crt.sh and resolves their IP addresses.
        If no domain is provided, shows help.
        """
        if domain is None:
            # Display help message if no domain is provided
            embed = discord.Embed(
                title="🌐 Subdomain Finder Help",
                description="**Subdomain Finder** - Retrieve subdomains and their IP addresses for a given domain using crt.sh.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}subfinder <domain>` to find subdomains and resolve their IP addresses.\nExample: `{config.BOT_PREFIX}subfinder example.com`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command finds subdomains listed on **crt.sh**, a public certificate transparency log. This can reveal subdomains associated with a domain and resolve their IP addresses.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Send "please wait" message before the search starts
        wait_message = await ctx.send("🔍 Please wait, searching for subdomains...")

        try:
            # Fetch data from crt.sh
            url = f"https://crt.sh/?q={domain}&output=json"
            response = requests.get(url, timeout=10)

            # Handle HTTP status codes gracefully
            if response.status_code == 502:
                await ctx.send("❌ The server is temporarily unavailable. Please try again later.")
                await wait_message.delete()  # Delete the "please wait" message
                return
            elif response.status_code == 503:
                await ctx.send("❌ The server is currently unavailable due to maintenance. Please try again later.")
                # Implement retry logic with a delay
                time.sleep(10)  # Wait for 10 seconds before retrying
                response = requests.get(url, timeout=10)
                if response.status_code == 503:
                    await ctx.send("❌ The server is still unavailable. Please try again later.")
                    await wait_message.delete()  # Delete the "please wait" message
                    return
            elif response.status_code == 429:
                await ctx.send("❌ Too many requests sent to the server. Please try again after a short wait.")
                # Implement retry logic with a delay
                time.sleep(10)  # Wait for 10 seconds before retrying
                response = requests.get(url, timeout=10)
                if response.status_code == 429:
                    await ctx.send("❌ Too many requests sent again. Please try again later.")
                    await wait_message.delete()  # Delete the "please wait" message
                    return
            elif response.status_code != 200:
                await ctx.send(f"❌ Failed to fetch subdomains. HTTP Status: {response.status_code}")
                await wait_message.delete()  # Delete the "please wait" message
                return

            subdomains_data = []
            results = response.json()

            # Create a set to avoid duplicate subdomains
            seen_subdomains = set()

            # Extract relevant information from the response and resolve IP addresses
            for entry in results:
                subdomain = entry.get("common_name")
                if subdomain not in seen_subdomains:
                    seen_subdomains.add(subdomain)
                    try:
                        ip = socket.gethostbyname(subdomain)
                    except socket.gaierror:
                        ip = "Unresolved IP"  # Handle unresolved subdomains
                    subdomains_data.append({
                        "subdomain": subdomain,
                        "ip": ip
                    })

            # Filter out the main domain if it's in the subdomains list and display it first
            main_domain_ip = socket.gethostbyname(domain)
            subdomains_data = [data for data in subdomains_data if data["subdomain"] != domain]

            # Paginate results if there are multiple subdomains
            if subdomains_data:
                pages = [subdomains_data[i:i + 5] for i in range(0, len(subdomains_data), 5)]  # 5 subdomains per page
                current_page = 0
                view = SubdomainView(pages, current_page, domain, main_domain_ip, self.bot)
                await view.send(ctx)
            else:
                await ctx.send(f"No subdomains found for {domain}.")

        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")

        # Delete the "please wait" message after the search is complete
        await wait_message.delete()


class SubdomainView(discord.ui.View):
    """View to handle button interactions for paginated subdomain results."""

    def __init__(self, pages, current_page, domain, main_domain_ip, bot):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = current_page
        self.domain = domain
        self.main_domain_ip = main_domain_ip
        self.bot = bot  # Store the bot instance
        self.message = None

        # Disable navigation buttons if there is only one page
        if len(pages) == 1:
            self.children[0].disabled = True  # Disable the Back button
            self.children[1].disabled = True  # Disable the Next button

    async def send(self, ctx):
        """Send the initial message and store it for updates."""
        embed = await self.create_embed()
        self.message = await ctx.send(embed=embed, view=self)

    @discord.ui.button(label="◀️ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous page."""
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next page."""
        self.current_page += 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        """Update the current page of the results."""
        self.children[0].disabled = self.current_page == 0  # Disable Back button on the first page
        self.children[1].disabled = self.current_page == len(self.pages) - 1  # Disable Next button on the last page

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        """Create the embed with subdomain data."""
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"🌐 Subdomains for {self.domain}",
            description="Here are the discovered subdomains and their IP addresses:",
            color=discord.Color.blue()
        )

        # Add the main domain IP at the top of the list
        embed.add_field(
            name=f"🌐 Main Domain: {self.domain}",
            value=f"🖥️ IP Address: {self.main_domain_ip}",
            inline=False
        )

        # Add subdomains
        for data in page:
            embed.add_field(name="🌐 Subdomain", value=data["subdomain"], inline=False)
            embed.add_field(name="🖥️ IP Address", value=data["ip"], inline=False)

        # Concatenate pagination info with bot footer details
        footer_text = f"Page {self.current_page + 1} of {len(self.pages)} - {config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name if self.bot.get_user(config.OWNER_ID) else 'Unknown'}"
        embed.set_footer(
             text=footer_text,
             icon_url=self.bot.user.avatar.url
        )

        return embed

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(SubdomainFinder(bot))
