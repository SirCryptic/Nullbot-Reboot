import discord
from discord.ext import commands
import aiohttp
import re
import asyncio
import os
from datetime import datetime
import config

# Global variable to track ongoing scans
ongoing_scans = {}

# Country codes to country names map
country_names = {
    "US": "United States", "GB": "United Kingdom", "DE": "Germany", "FR": "France", "IT": "Italy",
    "ES": "Spain", "RU": "Russia", "IN": "India", "BR": "Brazil", "AU": "Australia",
    "CA": "Canada", "JP": "Japan", "KR": "South Korea", "CN": "China", "MX": "Mexico", 
    "ZA": "South Africa", "NG": "Nigeria", "SA": "Saudi Arabia", "ID": "Indonesia", "TR": "Turkey",
    "AR": "Argentina", "PL": "Poland", "SE": "Sweden", "NL": "Netherlands", "AT": "Austria", 
    "NO": "Norway", "FI": "Finland", "DK": "Denmark", "BE": "Belgium", "CH": "Switzerland",
    "EG": "Egypt", "MA": "Morocco", "CO": "Colombia", "PH": "Philippines", "TH": "Thailand", 
    "PK": "Pakistan", "BD": "Bangladesh", "SG": "Singapore", "MY": "Malaysia", "AE": "United Arab Emirates", 
    "IL": "Israel", "HU": "Hungary", "CZ": "Czech Republic", "PT": "Portugal", "RO": "Romania", 
    "SK": "Slovakia", "BG": "Bulgaria", "EE": "Estonia", "LT": "Lithuania", "LV": "Latvia", "UA": "Ukraine", 
    "BY": "Belarus", "SI": "Slovenia", "HR": "Croatia", "RS": "Serbia", "ME": "Montenegro", "AL": "Albania", 
    "BA": "Bosnia and Herzegovina", "MK": "North Macedonia", "XK": "Kosovo", "AM": "Armenia", "GE": "Georgia", 
    "AZ": "Azerbaijan", "KZ": "Kazakhstan", "UZ": "Uzbekistan", "KG": "Kyrgyzstan", "TJ": "Tajikistan", 
    "TM": "Turkmenistan", "MN": "Mongolia", "NP": "Nepal", "LK": "Sri Lanka", "MM": "Myanmar", 
    "KH": "Cambodia", "LA": "Laos", "VN": "Vietnam", "JO": "Jordan", "QA": "Qatar", "KW": "Kuwait", 
    "OM": "Oman", "BH": "Bahrain", "YE": "Yemen", "SY": "Syria", "AF": "Afghanistan", "IR": "Iran", "IQ": "Iraq"
}

class OpenCams(commands.Cog):
    """Fetch open camera links based on country codes."""

    def __init__(self, bot):
        self.bot = bot

    async def fetch_camera_ips(self, country_code):
        found_ips = []
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "www.insecam.org",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            try:
                country_url = f"http://www.insecam.org/en/bycountry/{country_code}"
                async with session.get(country_url, headers=headers) as response:
                    html = await response.text()
                    last_page_match = re.findall(r'pagenavigator\("\?page=", (\d+)', html)
                    if not last_page_match:
                        return f"❌ Could not find any pages for country code `{country_code}`."

                    last_page = int(last_page_match[0])
                    for page in range(last_page):
                        page_url = f"http://www.insecam.org/en/bycountry/{country_code}/?page={page+1}"
                        async with session.get(page_url, headers=headers) as page_response:
                            page_html = await page_response.text()
                            ips = re.findall(r"http://\d+\.\d+\.\d+\.\d+:\d+", page_html)
                            found_ips.extend(ips)

                return found_ips

            except Exception as e:
                return f"❌ An error occurred while fetching data: `{str(e)}`"
            
    @commands.has_role(config.BOT_USER_ROLE)
    @commands.command(name='opencams')
    @commands.cooldown(1, 15, commands.BucketType.user)  # 15 seconds cooldown per user
    async def cams_by_country(self, ctx, country_code: str = None):
        """Fetch open camera links for a given country code."""
        
        if country_code is None:
            return await self.opencams_help(ctx)  # Show help if no country code is provided

        country_code = country_code.upper()

        # If a valid country code is passed, reset cooldown
        if country_code in country_names:
            self.bot.get_command("opencams").reset_cooldown(ctx)

        if country_code in ongoing_scans and ongoing_scans[country_code]:
            await ctx.send(f"❌ A search is already in progress for `{country_code}`. Please wait.")
            return

        ongoing_scans[country_code] = True
        wait_message = await ctx.send(f"🔄 Searching for open cameras in `{country_code}`. Please wait...")

        try:
            found_ips = await self.fetch_camera_ips(country_code)

            if isinstance(found_ips, str):  # If the result is a string, an error occurred
                await ctx.send(found_ips)
                return

            if not found_ips:
                await ctx.send(f"❌ No open cameras found for `{country_code}`.")
                return

            country_name = country_names.get(country_code, "Unknown Country")
            pages = [found_ips[i:i + 5] for i in range(0, len(found_ips), 5)]  # Paginate results in sets of 5
            current_page = 0
            view = CameraView(pages, current_page, country_code, self.bot)
            await view.send(ctx, country_name)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: `{e}`")
        finally:
            ongoing_scans[country_code] = False
            await wait_message.delete()

    async def opencams_help(self, ctx):
        """Provide help information for using the !opencams command."""
        
        prefix = config.BOT_PREFIX  # Fetch bot prefix dynamically

        # List of country codes
        country_codes = list(country_names.keys())

        country_pages = [country_codes[i:i + 10] for i in range(0, len(country_codes), 10)]

        help_pages = [
            {
                "title": "📸 Open Camera Search Help - Page 1",
                "description": f"Search for open cameras in different countries.\n\n"
                               f"Use the command:\n\n"
                               f"`{prefix}opencams <country_code>`\n\n"
                               f"Example: `{prefix}opencams US` to search for open cameras in the United States."
            }
        ]
        
        for idx, page in enumerate(country_pages, 2):
            page_content = "\n".join([f"`{code}`: {country_names[code]}" for code in page])
            help_pages.append({
                "title": f"Country Codes - Page {idx}",
                "description": f"Available country codes:\n\n{page_content}"
            })

        current_page = 0
        view = HelpView(help_pages, current_page, prefix, self.bot)
        await view.send(ctx)

class CameraView(discord.ui.View):
    """View to handle button interactions for paginated camera results."""

    def __init__(self, pages, current_page, country_code, bot):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = current_page
        self.country_code = country_code
        self.bot = bot  # Store the bot instance here
        self.message = None

    async def send(self, ctx, country_name):
        """Send the initial message and store it for updates."""
        embed = await self.create_embed(country_name)
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
        self.children[0].disabled = self.current_page == 0  
        self.children[1].disabled = self.current_page == len(self.pages) - 1  

        embed = await self.create_embed(self.country_code)

        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            self.message = await interaction.followup.send(embed=embed, view=self)

    async def create_embed(self, country_name):
        """Create the embed for camera results."""
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"Open Cameras in {country_name}",
            description="\n".join(page),
            color=discord.Color.blue()
        )
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

class HelpView(discord.ui.View):
    """View to handle button interactions for paginated help content."""

    def __init__(self, help_pages, current_page, prefix, bot):
        super().__init__(timeout=120)
        self.help_pages = help_pages
        self.current_page = current_page
        self.message = None
        self.prefix = prefix  
        self.bot = bot  

    async def send(self, ctx):
        """Send the initial message and store it for updates."""
        embed = await self.create_embed()
        self.message = await ctx.send(embed=embed, view=self)

    @discord.ui.button(label="◀️ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        self.children[0].disabled = self.current_page == 0  
        self.children[1].disabled = self.current_page == len(self.help_pages) - 1  

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        """Create the embed with the footer containing bot details."""
        embed = discord.Embed(
            title=self.help_pages[self.current_page]["title"],
            description=self.help_pages[self.current_page]["description"],
            color=discord.Color.blue()
        )

        owner_name = self.bot.get_user(config.OWNER_ID)
        embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url  # Fixed to use .url instead of .avatar_url
            )

        return embed

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

class HelpView(discord.ui.View):
    """View to handle button interactions for paginated help content."""

    def __init__(self, help_pages, current_page, prefix, bot):
        super().__init__(timeout=120)
        self.help_pages = help_pages
        self.current_page = current_page
        self.message = None
        self.prefix = prefix  
        self.bot = bot  

    async def send(self, ctx):
        """Send the initial message and store it for updates."""
        embed = await self.create_embed()
        self.message = await ctx.send(embed=embed, view=self)

    @discord.ui.button(label="◀️ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        self.children[0].disabled = self.current_page == 0  
        self.children[1].disabled = self.current_page == len(self.help_pages) - 1  

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        """Create the embed with the footer containing bot details."""
        embed = discord.Embed(
            title=self.help_pages[self.current_page]["title"],
            description=self.help_pages[self.current_page]["description"],
            color=discord.Color.blue()
        )

        owner_name = self.bot.get_user(config.OWNER_ID)
        embed.set_footer(
            text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {owner_name.name if owner_name else 'Unknown'}",
            icon_url=self.bot.user.avatar.url
        )

        return embed
    
    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  

async def setup(bot):
    await bot.add_cog(OpenCams(bot))