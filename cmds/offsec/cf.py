import discord
import dns.resolver
from discord.ext import commands
import config


class CloudflareResolver(commands.Cog):
    """Resolve DNS records for a given domain, handling Cloudflare and pagination."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(config.BOT_USER_ROLE)  # Ensure user has the required role
    @commands.command(name="resolve_dns")
    async def resolve_dns(self, ctx, domain: str = None):
        """
        Resolves DNS records (A/AAAA) for a given domain, with support for pagination.
        """
        if domain is None:
            embed = discord.Embed(
                title="🌐 DNS Resolver Help",
                description="**DNS Resolver** - Resolve A and AAAA DNS records for a domain.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}resolve_dns <domain>` to resolve DNS records.\nExample: `{config.BOT_PREFIX}resolve_dns example.com`",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Normalize the domain to ensure validity
        domain = self.normalize_domain(domain)

        # Send "please wait" message before starting
        wait_message = await ctx.send("🔍 Please wait, resolving DNS records...")

        try:
            # Query A (IPv4) and AAAA (IPv6) records for the domain
            a_records = dns.resolver.resolve(domain, 'A')
            aaaa_records = dns.resolver.resolve(domain, 'AAAA')

            ip_addresses = [str(answer) for answer in a_records] + [str(answer) for answer in aaaa_records]

            if ip_addresses:
                # Pagination setup (5 results per page)
                pages = [ip_addresses[i:i + 5] for i in range(0, len(ip_addresses), 5)]
                current_page = 0
                view = DNSResolverView(pages, current_page, domain, self.bot)
                await view.send(ctx)
            else:
                await ctx.send(f"No IP addresses found for {domain}.")

        except dns.resolver.NoAnswer:
            await ctx.send(f"⚠️ No DNS records found for {domain}. It may be behind Cloudflare.")
        except dns.resolver.NXDOMAIN:
            await ctx.send(f"⚠️ The domain {domain} does not exist.")
        except Exception as e:
            await ctx.send(f"⚠️ Error resolving domain {domain}: {e}")

        await wait_message.delete()  # Delete the "please wait" message

    def normalize_domain(self, domain):
        """
        Ensures the domain has a valid format. Strips unnecessary parts (e.g., http:// or https://)
        and returns only the domain name.
        """
        from urllib.parse import urlparse

        # Parse the domain to ensure it's valid
        parsed = urlparse(domain)
        if parsed.scheme:  # If the domain includes http:// or https://
            return parsed.netloc
        return domain  # Return as-is if no scheme is included


class DNSResolverView(discord.ui.View):
    """View to handle pagination for DNS record results."""

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
        """Create the embed with DNS data."""
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"🌐 DNS Records for {self.domain}",
            description="Here are the resolved DNS records (IP addresses):",
            color=discord.Color.blue()
        )

        # Add each IP address from the current page
        for ip in page:
            embed.add_field(name="🖥️ IP Address", value=ip, inline=False)

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
    await bot.add_cog(CloudflareResolver(bot))
