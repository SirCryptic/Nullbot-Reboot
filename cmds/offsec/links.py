import discord
import requests
from discord.ext import commands
import config
from bs4 import BeautifulSoup


class LinkFinder(commands.Cog):
    """Fetches all links from a given host."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)  # Ensure user has the required role to use the command
    @commands.command(name="links")
    async def links(self, ctx, host: str = None):
        """
        Fetches all links from a given host and displays them in a structured format.
        If no host is provided, shows help.
        """
        if host is None:
            # Display help message if no host is provided
            embed = discord.Embed(
                title="🌐 Link Finder Help",
                description="**Link Finder** - Retrieve all links from a given host.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}linkfinder <host>` to fetch links from a host.\nExample: `{config.BOT_PREFIX}linkfinder https://example.com`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command fetches all the links found on the given host's HTML content. This includes internal and external links.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Normalize the URL to ensure it has a valid schema
        host = self.normalize_url(host)

        # Send "please wait" message before the search starts
        wait_message = await ctx.send("🔍 Please wait, fetching links from the host...")

        try:
            # Fetch HTML content of the host
            response = requests.get(host, timeout=10)
            if response.status_code != 200:
                await ctx.send(f"❌ Failed to fetch links. HTTP Status: {response.status_code}")
                await wait_message.delete()  # Delete the "please wait" message
                return

            html_content = response.text

            # Extract links from HTML content
            links = self.extract_links(html_content, host)

            if links:
                # Paginate results if there are multiple links
                pages = [links[i:i + 10] for i in range(0, len(links), 10)]  # 10 links per page
                current_page = 0
                view = LinkView(pages, current_page, host, self.bot)
                await view.send(ctx)
            else:
                await ctx.send(f"No links found for {host}.")

        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")

        # Delete the "please wait" message after the search is complete
        await wait_message.delete()

    def normalize_url(self, url):
        """
        Ensures the URL has a valid scheme (http:// or https://). Adds http:// by default if no scheme is present.
        """
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            # Default to http:// if no scheme is provided
            return f"http://{url}"
        return url

    def extract_links(self, html, host):
        """Extracts all links from the HTML content."""
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Convert relative links to absolute links
            if href.startswith("/"):
                href = host.rstrip("/") + href
            elif not href.startswith("http"):
                href = f"{host.rstrip('/')}/{href.lstrip('/')}"
            links.append(href)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(links))


class LinkView(discord.ui.View):
    """View to handle button interactions for paginated link results."""

    def __init__(self, pages, current_page, host, bot):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = current_page
        self.host = host
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
        """Create the embed with link data."""
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"🌐 Links from {self.host}",
            description="Here are the discovered links from the given host:",
            color=discord.Color.blue()
        )

        for i, link in enumerate(page, start=1):
            embed.add_field(name=f"🔗 Link {i}", value=link, inline=False)

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
    await bot.add_cog(LinkFinder(bot))
