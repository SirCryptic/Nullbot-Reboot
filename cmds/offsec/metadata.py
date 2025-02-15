import discord
from discord.ext import commands
import requests
import io
from PIL import Image, UnidentifiedImageError
import pyheif
from PIL.ExifTags import TAGS
import config

# Global variable to track ongoing metadata scans
ongoing_scans = {}

class MetadataExtractor(commands.Cog):
    """Extracts and displays metadata (EXIF) from images hosted online."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='metadata')
    @commands.has_role(config.BOT_USER_ROLE)
    async def metadata(self, ctx, image_url: str = None):
        """Fetch and display EXIF metadata for an image URL."""

        if image_url is None:
            # Display help message if no URL is provided
            embed = discord.Embed(
                title="📷 Metadata Command Help",
                description="**Metadata Command** - Retrieve and analyze EXIF metadata from an image URL.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}metadata <image_url>` to fetch metadata.\nExample: `{config.BOT_PREFIX}metadata https://example.com/image.jpg`",
                inline=False
            )
            embed.add_field(
                name="📌 Information Retrieved",
                value="The command extracts EXIF metadata, which may include:\n- Camera model\n- Image orientation\n- Exposure settings\n- Date and time of capture",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Supported Formats",
                value="Supported image formats include:\n- **JPEG (.jpg, .jpeg)** ✅\n- **PNG (.png)**",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Ensure the URL is valid
        if not (image_url.lower().startswith("http://") or image_url.lower().startswith("https://")):
            await ctx.send("❌ Please provide a **valid image URL** (http:// or https://).")
            return

        # Check if there is an ongoing scan for this image
        if image_url in ongoing_scans and ongoing_scans[image_url]:
            await ctx.send(f"❌ A metadata scan is already in progress for this image. Please wait.")
            return

        ongoing_scans[image_url] = True
        wait_message = await ctx.send(f"🔄 Processing the image. Please wait...")

        try:
            metadata = await self.fetch_metadata(image_url)

            if isinstance(metadata, str):  # If the result is a string, an error occurred
                await ctx.send(metadata)
                return

            # Paginate metadata if needed (5 items per page)
            pages = [metadata[i:i + 5] for i in range(0, len(metadata), 5)]
            current_page = 0
            view = MetadataView(self.bot, pages, current_page, image_url)  # Pass the bot here
            await view.send(ctx)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: `{e}`")
        finally:
            ongoing_scans[image_url] = False
            await wait_message.delete()

    async def fetch_metadata(self, image_url):
        """Fetch EXIF metadata from an image URL."""
        try:
            response = requests.get(image_url)
            if response.status_code != 200:
                return f"❌ Failed to download the image from the provided URL."

            img_data = response.content
            file_ext = image_url.split('.')[-1].lower()

            try:
                # Handle HEIC/HEIF
                if file_ext in ['heic', 'heif']:
                    heif_file = pyheif.read(io.BytesIO(img_data))
                    img = Image.frombytes(
                        heif_file.mode,
                        heif_file.size,
                        heif_file.data,
                        "raw",
                        heif_file.mode,
                        heif_file.stride,
                    )
                else:
                    img = Image.open(io.BytesIO(img_data))

                # Extract EXIF Data
                exif_data = img._getexif()
                if not exif_data:
                    return "ℹ️ No EXIF data found in this image."

                # Format EXIF data
                exif_info = [f"**{TAGS.get(tag, tag)}:** {value}" for tag, value in exif_data.items()]
                return exif_info

            except UnidentifiedImageError:
                return "❌ Unsupported image format. Try using **JPG or PNG**."

        except Exception as e:
            return f"⚠️ An error occurred while processing the image: {e}"

class MetadataView(discord.ui.View):
    """View to handle button interactions for paginated EXIF metadata results."""

    def __init__(self, bot, pages, current_page, image_url):
        super().__init__(timeout=120)
        self.bot = bot  # Save the bot reference
        self.pages = pages
        self.current_page = current_page
        self.image_url = image_url
        self.message = None

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
        """Create the embed with EXIF metadata."""
        page = self.pages[self.current_page]
        description = "\n".join(page)
        
        # If the description exceeds 4096 characters, split it across multiple embeds
        if len(description) > 4096:
            chunks = [description[i:i + 4096] for i in range(0, len(description), 4096)]
            embed = discord.Embed(
                title=f"📷 Metadata (EXIF) Information (Part {self.current_page + 1})",
                description=chunks[0],  # Set the first chunk
                color=discord.Color.blue()
            )
            footer_text = f"Page {self.current_page + 1} of {len(self.pages)} - {config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name if self.bot.get_user(config.OWNER_ID) else 'Unknown'}"
            embed.set_footer(
                text=footer_text,
                icon_url=self.bot.user.avatar.url
            )
            embed.set_image(url=self.image_url)
            return embed
        else:
            embed = discord.Embed(
                title=f"📷 Metadata (EXIF) Information",
                description=description,
                color=discord.Color.blue()
            )
            footer_text = f"Page {self.current_page + 1} of {len(self.pages)} - {config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name if self.bot.get_user(config.OWNER_ID) else 'Unknown'}"
            embed.set_footer(
                text=footer_text,
                icon_url=self.bot.user.avatar.url
            )
            embed.set_image(url=self.image_url)
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
    await bot.add_cog(MetadataExtractor(bot))
