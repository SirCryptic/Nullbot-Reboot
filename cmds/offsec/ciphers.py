import discord
from discord.ext import commands
import asyncio
import subprocess
import os
import config

class CipherScan(commands.Cog):
    """Cipher Scan command to scan weak and strong ciphers on a given host and port."""

    def __init__(self, bot):
        self.bot = bot
        self.ongoing_scans = {}  # To track ongoing scans for each user

        # Full list of ciphers for testing (both weak and strong ciphers)
        self.all_ciphers = [
            # Weak ciphers (RC4, DES, NULL, MD5, SHA-1, etc.)
            "RC4", "RC4-SHA", "RC4-MD5", "RC4-128", "RC4-40", "DES", "DES-CBC3-SHA", "3DES", "3DES-CBC", "3DES-EDE-CBC-SHA",
            "NULL", "NULL-MD5", "NULL-SHA", "MD5", "SHA-1", "AES128-SHA", "AES256-SHA", "AES128-CBC", "AES256-CBC", "IDEA",
            "SEED", "CAMELLIA128-SHA", "CAMELLIA256-SHA", "RC2", "RC2-CBC", "RC2-40", "RC2-128", "RC2-40-CBC", "RC2-128-CBC",

            # Strong ciphers
            "ECDHE-RSA-AES128-GCM-SHA256", "ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-RSA-AES128-SHA256", "ECDHE-RSA-AES256-SHA384",
            "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-ECDSA-AES256-GCM-SHA384", "DHE-RSA-AES128-GCM-SHA256", "DHE-RSA-AES256-GCM-SHA384",
            "DHE-RSA-AES128-SHA256", "DHE-RSA-AES256-SHA384", "ECDHE-RSA-AES128-SHA", "ECDHE-RSA-AES256-SHA", "ECDHE-ECDSA-AES128-SHA",
            "ECDHE-ECDSA-AES256-SHA", "DHE-RSA-AES128-SHA", "DHE-RSA-AES256-SHA", "ECDHE-RSA-AES128-CCM", "ECDHE-RSA-AES256-CCM",
            "ECDHE-RSA-CHACHA20-POLY1305", "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-AES128-CTR", "ECDHE-RSA-AES256-CTR",
            "DHE-RSA-AES128-CTR", "DHE-RSA-AES256-CTR", "DHE-RSA-AES128-CCM", "DHE-RSA-AES256-CCM", "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256", "TLS_AES_128_CCM_SHA256", "TLS_AES_256_CCM_SHA384",
            "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256", "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"
        ]

    @commands.has_role(config.BOT_USER_ROLE)
    @commands.command(name='ciphers')
    async def ciphers(self, ctx, host: str = None, port: int = None):
        """Performs a cipher scan for weak and strong ciphers on a given host and port."""
        
        if host is None or port is None:
            # Send the help message when no host or port is provided
            embed = discord.Embed(
                title="🔐 Cipher Scan Help",
                description="**Cipher Scan** - Scan a server for weak and strong ciphers on a specific port.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔎 Command Usage",
                value=f"Use `{config.BOT_PREFIX}ciphers <host> <port>` to perform a cipher scan.\nExample: `{config.BOT_PREFIX}ciphers example.com 443`",
                inline=False
            )
            embed.add_field(
                name="⚠️ Warning",
                value="This operation may take a while, depending on the number of ciphers being tested and the target server's response times. Please be patient.",
                inline=False
            )
            embed.add_field(
                name="💡 Additional Info",
                value="The scan will test both weak and strong ciphers. Weak ciphers include deprecated ones like RC4, 3DES, and others. Strong ciphers provide better security for encrypted communication.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}"
            )
            await ctx.send(embed=embed)
            return

        if ctx.author.id in self.ongoing_scans:
            await ctx.send("A scan is already in progress. Please wait for it to complete before starting a new one.")
            return

        # Add user to ongoing scans to prevent spamming
        self.ongoing_scans[ctx.author.id] = True

        # Send initial message informing user the scan is starting
        progress_message = await ctx.send(f"Scanning ciphers on {host}:{port}...\n\nThis may take a while, please be patient...")

        try:
            # Run tests and collect results for weak and strong ciphers
            weak_ciphers_result = await self.run_openssl_ciphers(host, port, weak=True)
            strong_ciphers_result = await self.run_openssl_ciphers(host, port, weak=False)

            # Combine all results into a single output
            full_results = f"""
            Cipher Scan Results for {host}:{port}
            
            {weak_ciphers_result}
            {strong_ciphers_result}

            -- Scanned by {config.BOT_NAME} v{config.BOT_VERSION} --
            """

            # Save the results to a file
            file_path = os.path.join(config.DOWNLOAD_DIR, f"cipher_scan_{host}_{port}.txt")
            with open(file_path, "w") as f:
                f.write(full_results)

            # Update progress message to indicate scan completion
            await progress_message.edit(content="Scanning ciphers complete! Displaying results...")

            # Paginate results into chunks
            pages = [full_results[i:i + 1900] for i in range(0, len(full_results), 1900)]
            current_page = 0

            # Function to create an embed for a specific page
            def create_embed(page_num):
                embed = discord.Embed(
                    title=f"Cipher Scan Results - {host}:{port}",
                    description=pages[page_num],
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Page {page_num + 1}/{len(pages)}")
                return embed

            # Send the first page
            message = await ctx.send(embed=create_embed(current_page))

            # Add reactions for page navigation if needed
            if len(pages) > 1:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

                def check(reaction, user):
                    return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["⬅️", "➡️"]

                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                        if str(reaction.emoji) == "⬅️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=create_embed(current_page))

                        elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=create_embed(current_page))

                        # Remove the user's reaction to keep the interface clean
                        await message.remove_reaction(reaction.emoji, user)

                    except asyncio.TimeoutError:
                        try:
                            await message.clear_reactions()
                        except discord.errors.NotFound:
                            pass
                        break

            # Send the download link for the results
            await ctx.send(f"The full results are available for download:", file=discord.File(file_path))

            # Delete the file after sending it
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            await progress_message.edit(content=f"An error occurred while scanning: {e}")

        finally:
            # Remove the user from ongoing scans
            self.ongoing_scans.pop(ctx.author.id, None)

    async def run_openssl_ciphers(self, host, port, weak=True):
        """Runs the OpenSSL cipher test and returns the results."""
        result = ""
        if weak:
            result += "\nTesting for weak ciphers...\n"
        else:
            result += "\nTesting for strong ciphers...\n"

        for cipher in self.all_ciphers:
            test_command = ["openssl", "s_client", "-cipher", cipher, "-connect", f"{host}:{port}"]
            process = await asyncio.create_subprocess_exec(*test_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                result += f"Cipher {cipher} is enabled\n"
            else:
                result += f"Cipher {cipher} is disabled\n"

        # Filter out weak ciphers if weak=True
        if weak:
            result = "\n".join([line for line in result.splitlines() if "NULL" in line or "RC4" in line or "DES" in line or "3DES" in line or "MD5" in line or "SHA-1" in line])
        else:
            result = "\n".join([line for line in result.splitlines() if "NULL" not in line and "RC4" not in line and "DES" not in line and "3DES" not in line and "MD5" not in line and "SHA-1" not in line])

        return result

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(CipherScan(bot))
