import discord
from discord.ext import commands
import base64
import hashlib
import re
import config
import codecs  # For ROT13

class EncoderDecoder(commands.Cog):
    """A cog for encoding and decoding text in various formats."""

    def __init__(self, bot):
        self.bot = bot

    # Morse Code Dictionary
    MORSE_CODE_DICT = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..',
        '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
        '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...',
        ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
    }

    @commands.command(name="encode")
    async def encode_command(self, ctx, format: str = None, *, text: str = None):
        """
        Encode text in a specified format.
        Supported formats: base64, binary, hex, sha256, md5, rot13, morse
        """
        if format is None or text is None:
            # Send help message if format or text is not provided
            embed = discord.Embed(
                title="🔒 Encode Command Help",
                description="Encode text into various formats.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔧 Command Usage",
                value=f"Use `{config.BOT_PREFIX}encode <format> <text>` to encode text.\nExample: `{config.BOT_PREFIX}encode base64 Hello World`",
                inline=False
            )
            embed.add_field(
                name="📜 Supported Formats",
                value="`base64` - Base64 encoding\n`binary` - Binary encoding\n`hex` - Hexadecimal encoding\n`sha256` - SHA-256 hash encoding\n`md5` - MD5 hash encoding\n`rot13` - ROT13 encoding\n`morse` - Morse code encoding",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Sanitize the input text
        sanitized_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        # Perform the encoding
        try:
            if format.lower() == "base64":
                encoded_text = base64.b64encode(sanitized_text.encode()).decode()
            elif format.lower() == "binary":
                encoded_text = ' '.join(format(ord(char), '08b') for char in sanitized_text)
            elif format.lower() == "hex":
                encoded_text = sanitized_text.encode().hex()
            elif format.lower() == "sha256":
                encoded_text = hashlib.sha256(sanitized_text.encode()).hexdigest()
            elif format.lower() == "md5":
                encoded_text = hashlib.md5(sanitized_text.encode()).hexdigest()
            elif format.lower() == "rot13":
                encoded_text = codecs.encode(sanitized_text, 'rot_13')
            elif format.lower() == "morse":
                encoded_text = self.to_morse(sanitized_text)
            else:
                await ctx.send(f"❌ Invalid format. Use `base64`, `binary`, `hex`, `sha256`, `md5`, `rot13`, or `morse`.")
                return
        except Exception as e:
            await ctx.send(f"❌ Error encoding text: {e}")
            return

        # Send the encoded message
        await ctx.send(f"🔒 Encoded in `{format}`:\n```\n{encoded_text}\n```")

    @commands.command(name="decode")
    async def decode_command(self, ctx, format: str = None, *, encoded_text: str = None):
        """
        Decode text from a specified format.
        Supported formats: base64, binary, hex, sha256, md5, rot13, morse
        """
        if format is None or encoded_text is None:
            # Send help message if format or text is not provided
            embed = discord.Embed(
                title="🔓 Decode Command Help",
                description="Decode text from various formats.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="🔧 Command Usage",
                value=f"Use `{config.BOT_PREFIX}decode <format> <text>` to decode text.\nExample: `{config.BOT_PREFIX}decode base64 SGVsbG8gV29ybGQ=`",
                inline=False
            )
            embed.add_field(
                name="📜 Supported Formats",
                value="`base64` - Base64 decoding\n`binary` - Binary decoding\n`hex` - Hexadecimal decoding\n`sha256` - SHA-256 hash decoding (not reversible)\n`md5` - MD5 hash decoding (not reversible)\n`rot13` - ROT13 decoding\n`morse` - Morse code decoding",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            await ctx.send(embed=embed)
            return

        # Perform the decoding
        try:
            if format.lower() == "base64":
                decoded_text = base64.b64decode(encoded_text.encode()).decode()
            elif format.lower() == "binary":
                decoded_text = ''.join(
                    chr(int(binary_char, 2)) for binary_char in encoded_text.split()
                )
            elif format.lower() == "hex":
                decoded_text = bytes.fromhex(encoded_text).decode()
            elif format.lower() == "sha256":
                await ctx.send(f"SHA-256 is a one-way hash and cannot be decoded.")
                return
            elif format.lower() == "md5":
                await ctx.send(f"MD5 is a one-way hash and cannot be decoded.")
                return
            elif format.lower() == "rot13":
                decoded_text = codecs.encode(encoded_text, 'rot_13')  # ROT13 is symmetric, so encode = decode
            elif format.lower() == "morse":
                decoded_text = self.from_morse(encoded_text)
            else:
                await ctx.send(f"❌ Invalid format. Use `base64`, `binary`, `hex`, `sha256`, `md5`, `rot13`, or `morse`.")
                return
        except Exception as e:
            await ctx.send(f"❌ Error decoding text: {e}")
            return

        # Send the decoded message
        await ctx.send(f"🔓 Decoded from `{format}`:\n```\n{decoded_text}\n```")

    # Helper methods for Morse Code conversion
    def to_morse(self, text):
        text = text.upper()
        morse_code = []
        for char in text:
            if char == " ":
                morse_code.append(" / ")
            elif char in self.MORSE_CODE_DICT:
                morse_code.append(self.MORSE_CODE_DICT[char])
        return " ".join(morse_code)

    def from_morse(self, morse_code):
        morse_code = morse_code.split(" ")
        decoded_text = []
        for code in morse_code:
            if code == "/":
                decoded_text.append(" ")
            elif code in self.MORSE_CODE_DICT.values():
                decoded_text.append(
                    [key for key, value in self.MORSE_CODE_DICT.items() if value == code][0]
                )
        return "".join(decoded_text)

    @commands.command(name="sha256")
    async def sha256(self, ctx, *, text: str = None):
        """Generate a SHA-256 hash for the given text."""
        if not text:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}sha256 <text>`")
            return

        hash_result = hashlib.sha256(text.encode()).hexdigest()
        await ctx.send(f"SHA-256 Hash: `{hash_result}`")

    @commands.command(name="md5")
    async def md5(self, ctx, *, text: str = None):
        """Generate an MD5 hash for the given text."""
        if not text:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}md5 <text>`")
            return

        hash_result = hashlib.md5(text.encode()).hexdigest()
        await ctx.send(f"MD5 Hash: `{hash_result}`")

    @commands.command(name="hex2dec")
    async def hex2dec(self, ctx, hex_value: str = None):
        """Convert Hexadecimal to Decimal."""
        if not hex_value:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}hex2dec <hex_value>`")
            return

        try:
            decimal_value = int(hex_value, 16)
            await ctx.send(f"Hexadecimal `{hex_value}` is `{decimal_value}` in Decimal.")
        except ValueError:
            await ctx.send(f"❌ Invalid Hex value. Please provide a valid Hexadecimal number.")

    @commands.command(name="dec2hex")
    async def dec2hex(self, ctx, decimal_value: int = None):
        """Convert Decimal to Hexadecimal."""
        if decimal_value is None:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}dec2hex <decimal_value>`")
            return

        hex_value = hex(decimal_value)[2:]  # Remove the '0x' prefix
        await ctx.send(f"Decimal `{decimal_value}` is `{hex_value}` in Hexadecimal.")

    @commands.command(name="reverse")
    async def reverse(self, ctx, *, text: str = None):
        """Reverse the given string."""
        if not text:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}reverse <text>`")
            return

        reversed_text = text[::-1]
        await ctx.send(f"Reversed Text: `{reversed_text}`")

    @commands.command(name="caesar")
    async def caesar(self, ctx, shift: int = 3, *, text: str = None):
        """Encode or Decode text using Caesar Cipher."""
        if not text:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}caesar <shift> <text>`")
            return

        result = ""
        for char in text:
            if char.isalpha():
                shift_base = 65 if char.isupper() else 97
                result += chr((ord(char) - shift_base + shift) % 26 + shift_base)
            else:
                result += char

        await ctx.send(f"Caesar Cipher Result: `{result}`")

    @commands.command(name="leet")
    async def leet(self, ctx, *, text: str = None):
        """Convert text into Leet Speak."""
        if not text:
            await ctx.send(f"Usage: `{config.BOT_PREFIX}leet <text>`")
            return

        leet_dict = {
            'A': '4', 'B': '8', 'C': '<', 'D': '|)', 'E': '3', 'F': '|=', 'G': '6', 'H': '#', 'I': '1', 'J': ';', 'K': '|<',
            'L': '1', 'M': '/\/\\', 'N': '^/', 'O': '0', 'P': '|*', 'Q': '0,', 'R': '|2', 'S': '$', 'T': '7', 'U': '(_)', 'V': '\\/',
            'W': '\\^/', 'X': '><', 'Y': '/', 'Z': '2'
        }
        leet_text = ''.join(leet_dict.get(c.upper(), c) for c in text)
        await ctx.send(f"Leet Speak: `{leet_text}`")

async def setup(bot):
    await bot.add_cog(EncoderDecoder(bot))
