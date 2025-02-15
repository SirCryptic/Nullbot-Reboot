import discord
import random
import aiofiles
import os
import asyncio
from discord.ext import commands
import config

class AdminFinder(commands.Cog):
    """Find admin panels for a given domain."""

    def __init__(self, bot):
        self.bot = bot
        self.temp_found_urls = []  # In-memory list to store valid URLs temporarily

    @commands.has_role(config.BOT_USER_ROLE)  # Ensure user has the required role
    @commands.command(name="acpf")
    async def acpf(self, ctx, domain: str = None):
        """
        Scan a domain for possible admin panels and provide pagination for results.
        """
        if domain is None:
            embed = discord.Embed(
                title="🔍 Admin Finder Help",
                description="**Admin Finder** - Check for possible admin panels on a domain.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}acpf <domain>` to scan a domain for admin panels.\nExample: `{config.BOT_PREFIX}acpf example.com`",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Strip any trailing slashes from the domain
        domain = domain.rstrip('/')

        # Ensure domain has a schema (http:// or https://)
        if not domain.startswith(('http://', 'https://')):
            domain = f'http://{domain}'  # Add http:// if no schema is provided

        # Send "please wait" message as embed
        embed_wait = discord.Embed(
            title="🔍 Scanning for Admin Panels...",
            description="Please wait while we scan the provided domain for possible admin panels.",
            color=discord.Color.blue()
        )
        embed_wait.set_footer(text="This may take some time, please be patient.")
        wait_message = await ctx.send(embed=embed_wait)

        # Prepare file paths
        admin_urls_path = config.ADMIN_URLS_PATH
        user_agents_path = config.USER_AGENTS_PATH

        if not os.path.exists(admin_urls_path) or not os.path.exists(user_agents_path):
            await ctx.send("⚠️ Error: Missing required files.")
            return

        found_admin_panels = []
        async with aiofiles.open(admin_urls_path, 'r') as file:
            urls = await file.readlines()

        async with aiofiles.open(user_agents_path, 'r') as file:
            user_agents = await file.readlines()

        # Initialize pagination structure
        pages = []
        current_page = 0

        async def scan_admin_panels():
            nonlocal current_page, pages  # Ensure pages is updated within this function
            for url_suffix in urls:
                url_suffix = url_suffix.strip()
                url = f"{domain}{url_suffix}"
                user_agent = random.choice(user_agents).strip()

                try:
                    # Use GET request instead of HEAD
                    status, _ = await self.send_get_request(url, user_agent)

                    # Only store URLs with Status: 200
                    if status == "200":
                        self.temp_found_urls.append(url)
                        found_admin_panels.append(f"✅ {url} - Status: 200")
                    elif status == "404":
                        # Retry if status is 404 (this is optional)
                        await asyncio.sleep(1)  # Delay before retry
                        status, _ = await self.send_get_request(url, user_agent)
                        if status == "200":
                            self.temp_found_urls.append(url)
                            found_admin_panels.append(f"✅ {url} - Status: 200")
                    # Pagination (5 results per page)
                    if len(found_admin_panels) % 5 == 0:
                        pages.append(found_admin_panels[-5:])

                except Exception as e:
                    found_admin_panels.append(f"❓ Error checking {url}: {str(e)}")

            if not pages:
                # No admin panels found, create an informative embed
                embed_no_panels = discord.Embed(
                    title="⚠️ No Admin Panels Found",
                    description=f"Unfortunately, we couldn't find any admin panels for `{domain}`. Please double-check the domain or try again later.",
                    color=discord.Color.red()
                )
                embed_no_panels.add_field(name="🔍 What to do next?", value="1. Make sure the domain is correct.\n2. Try other known admin panel paths.\n3. Wait a few moments and try again later.", inline=False)
                embed_no_panels.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed_no_panels)
            else:
                # Split the found admin panels into pages for pagination
                pages = [found_admin_panels[i:i+5] for i in range(0, len(found_admin_panels), 5)]
                view = AdminFinderView(pages, current_page, domain, self.bot)
                await view.send(ctx)

            # After sending the result, clean up the temporary in-memory data
            self.cleanup()

        # Run the scan in the background
        await asyncio.gather(scan_admin_panels())

        await wait_message.delete()  # Delete "please wait" message

    async def send_get_request(self, url, user_agent):
        """Sends a GET request to the URL."""
        import aiohttp
        headers = {'User-Agent': user_agent}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    # Return the status code
                    return str(response.status), response.headers
        except Exception as e:
            return str(e), {}

    def cleanup(self):
        """Clean up temporary stored data."""
        # Clear the in-memory list of URLs
        self.temp_found_urls.clear()

class AdminFinderView(discord.ui.View):
    """View to handle pagination for admin panel scan results."""

    def __init__(self, pages, current_page, domain, bot):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = current_page
        self.domain = domain
        self.bot = bot
        self.message = None

        # Disable navigation buttons if there's only one page
        if len(pages) == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

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
        self.children[0].disabled = self.current_page == 0  # Disable Back button on first page
        self.children[1].disabled = self.current_page == len(self.pages) - 1  # Disable Next button on last page

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        """Create the embed with admin panel scan data."""
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"🔍 Admin Panels for {self.domain}",
            description="Here are the results from the scan:",
            color=discord.Color.green()
        )

        # Add each result from the current page
        for result in page:
            embed.add_field(name="Result", value=result, inline=False)

        # Add pagination footer
        footer_text = f"Page {self.current_page + 1} of {len(self.pages)} - {config.BOT_NAME} - Beta v{config.BOT_VERSION}"
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
    await bot.add_cog(AdminFinder(bot))
