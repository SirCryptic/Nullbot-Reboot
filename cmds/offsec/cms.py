import discord
import requests
from discord.ext import commands
import time
from urllib.parse import urlparse
import config


class CMSDetect(commands.Cog):
    """Detects CMS and attempts user enumeration for WordPress only."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cmsdetect")
    async def cmsdetect(self, ctx, url: str = None):
        """
        Detects CMS and attempts user enumeration for WordPress only.
        If no URL is provided, show help message.
        """
        if url is None:
            # Display help message if no URL is provided
            embed = discord.Embed(
                title="🖥️ CMS Detection Help",
                description="**CMS Detection** - Detect CMS type and try user enumeration.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}cmsdetect <url>` to detect the CMS of a website and attempt user enumeration.\nExample: `{config.BOT_PREFIX}cmsdetect http://example.com`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command detects CMS based on certain indicators and tries to enumerate users for WordPress only.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Normalize the URL to ensure a valid schema
        url = self.normalize_url(url)

        # Strip the protocol from the URL
        clean_url = self.strip_protocol(url)

        # Send "please wait" message before CMS detection starts
        wait_message = await ctx.send("🔍 Please wait, detecting CMS...")

        try:
            # Detect CMS - Look for common CMS indicators
            cms = await self.detect_cms(url)
            if cms:
                embed = discord.Embed(
                    title="🖥️ CMS Detection Result",
                    description=f"Detected CMS: {cms}",
                    color=discord.Color.green()
                )
                embed.add_field(name="🔗 URL", value=clean_url, inline=False)

                # Only attempt user enumeration for WordPress
                if cms == "WordPress":
                    embed.add_field(name="👥 Attempting User Enumeration...", value="Please wait...", inline=False)
                    await ctx.send(embed=embed)

                    # Attempt user enumeration using WordPress REST API
                    await self.enumerate_wordpress_users(ctx, url)
                else:
                    embed.add_field(name="👥 User Enumeration", value="User enumeration has not been implemented for this CMS yet.", inline=False)
                    await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Could not detect CMS for {clean_url}.")
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")

        # Delete the "please wait" message after the CMS detection is complete
        await wait_message.delete()

    def normalize_url(self, url):
        """
        Ensures the URL has a valid scheme (http:// or https://). Adds http:// by default if no scheme is present.
        """
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            # Default to http:// if no scheme is provided
            return f"http://{url}"
        return url

    async def detect_cms(self, url):
        """
        Detects CMS based on URL indicators, HTML meta tags, headers, and HTML class names.
        """
        try:
            response = self.get_with_retry(url)
            if response is None or response.status_code != 200:
                return None

            html_content = response.text

            # WordPress Detection
            if self.is_wordpress(html_content):
                return "WordPress"
            # XenForo Detection
            elif self.is_xenforo(html_content):
                return "XenForo"
            # Joomla Detection
            elif self.is_joomla(html_content):
                return "Joomla"
            # Drupal Detection
            elif self.is_drupal(html_content):
                return "Drupal"
            # MyBB Detection
            elif self.is_mybb(html_content):
                return "MyBB"
            # phpBB Detection
            elif self.is_phpbb(html_content):
                return "phpBB"
            # Discourse Detection
            elif self.is_discourse(html_content):
                return "Discourse"
            # Flarum Detection
            elif self.is_flarum(html_content):
                return "Flarum"
            # SMF Detection
            elif self.is_smf(html_content):
                return "SMF"

            return None
        except requests.exceptions.RequestException:
            return None

    def get_with_retry(self, url, retries=3, timeout=10):
        """
        Attempts to send a GET request with retries and custom timeout.
        """
        for _ in range(retries):
            try:
                response = requests.get(url, timeout=timeout)
                return response
            except requests.exceptions.Timeout:
                print(f"Timeout while trying to fetch {url}, retrying...")
                time.sleep(5)  # Wait for 5 seconds before retrying
            except requests.exceptions.RequestException as e:
                print(f"Error while fetching {url}: {e}")
                return None
        return None  # Return None if all retries fail

    # CMS-specific detection functions
    def is_wordpress(self, html):
        """Detects WordPress CMS"""
        if "wp-content" in html or "wp-admin" in html:
            return True
        return False

    def is_xenforo(self, html):
        """Detects XenForo CMS"""
        if "community platform by XenForo" in html.lower() or "xenforo" in html.lower():
            return True
        return False

    def is_joomla(self, html):
        """Detects Joomla CMS"""
        if "administrator" in html or "index.php?option=com_" in html:
            return True
        return False

    def is_drupal(self, html):
        """Detects Drupal CMS"""
        if "node/" in html or "drupal/" in html or "sites/default/" in html:
            return True
        return False

    def is_mybb(self, html):
        """Detects MyBB CMS"""
        if "forum" in html or "member.php" in html:
            return True
        return False

    def is_phpbb(self, html):
        """Detects phpBB CMS"""
        if "viewtopic.php" in html or "ucp.php" in html:
            return True
        return False

    def is_discourse(self, html):
        """Detects Discourse CMS"""
        if "/t/" in html or "/posts/" in html:
            return True
        return False

    def is_flarum(self, html):
        """Detects Flarum CMS"""
        if "/forum/" in html or "/discussion/" in html:
            return True
        return False

    def is_smf(self, html):
        """Detects SMF CMS"""
        if "index.php?topic=" in html or "index.php?action=" in html:
            return True
        return False

    # User enumeration function for WordPress only
    async def enumerate_wordpress_users(self, ctx, url):
        """Enumerates WordPress users using the REST API."""
        wp_users_url = f"{url.rstrip('/')}/wp-json/wp/v2/users"
        response = self.get_with_retry(wp_users_url)

        if response and response.status_code == 200:
            users = response.json()
            if users:
                embed = discord.Embed(
                    title="👥 WordPress Users Found",
                    description=f"User enumeration results for {url}:",
                    color=discord.Color.green()
                )
                for user in users:
                    embed.add_field(
                        name=f"👤 {user['name']}",
                        value=f"**Username:** {user['slug']}\n**ID:** {user['id']}",
                        inline=False
                    )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ No users found for {url}.")
        elif response and response.status_code == 404:
            await ctx.send(f"❌ {url} does not appear to have a WordPress REST API endpoint.")
        else:
            await ctx.send(f"❌ Failed to fetch users. HTTP Status: {response.status_code if response else 'None'}")

    def strip_protocol(self, url):
        """Strips 'http://' or 'https://' from the URL"""
        return urlparse(url).netloc


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(CMSDetect(bot))
