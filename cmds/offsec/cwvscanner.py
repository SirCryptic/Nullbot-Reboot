import discord
from discord.ext import commands
import aiohttp
import re
import asyncio
import os
import config
from urllib.parse import urlparse

class cwvscan(commands.Cog):
    """Security-related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.scanning_urls = set()  # To track URLs/IPs currently being scanned

    def normalize_url(self, url: str):
        """Normalize the URL/IP to make sure similar URLs aren't considered different."""
        # Strip http(s) and www. If the URL is an IP address, do nothing
        parsed_url = urlparse(url.lower())
        normalized_url = parsed_url.netloc if parsed_url.netloc else parsed_url.path
        return normalized_url

    @commands.command(name="cwvscan")
    @commands.has_role(config.BOT_USER_ROLE)
    async def cwvscan(self, ctx, *, url: str = None):
        """Scan a URL/IP for vulnerabilities and display results in a paginated format."""
        
        if not url:
            # Send fancy help message when no URL is provided
            embed = discord.Embed(
                title="🛡️ CWVScan Help",
                description=f"**Common Web Application Vulnerability Scanner** - scans URLs for security vulnerabilities. Here's how you can use it:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🔍 Command Usage",
                value=f"Use `{config.BOT_PREFIX}cwvscan <URL>` to scan a URL for vulnerabilities.\nExample: `{config.BOT_PREFIX}cwvscan https://example.com`",
                inline=False
            )
            embed.add_field(
                name="⚠️ Supported Vulnerabilities",
                value="SQL Injection, XSS, Command Injection, Remote Code Execution, and many more.",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Additional Info",
                value="You must have the appropriate role to use this command.",
                inline=False
            )
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )

            await ctx.send(embed=embed)
            return
        
        # Normalize the URL/IP to avoid conflicts
        normalized_url = self.normalize_url(url)
        
        # Check if the URL/IP is already being scanned
        if normalized_url in self.scanning_urls:
            waiting_message = await ctx.send(f"⏳ Please wait, a scan for `{url}` is already in progress.")
            await asyncio.sleep(5)  # Wait for 5 seconds
            await waiting_message.delete()  # Delete the message after 5 seconds
            return
        
        # Add the URL/IP to the scanning set
        self.scanning_urls.add(normalized_url)
        
        # Send a "please wait" message
        waiting_message = await ctx.send(f"🔍 **Scanning** `{url}` for vulnerabilities. Please wait...")

        # Start the scan in the background
        asyncio.create_task(self.run_scan(ctx, url, normalized_url, waiting_message))

    async def run_scan(self, ctx, url: str, normalized_url: str, waiting_message: discord.Message):
        """Run the scan in the background."""
        try:
            # Check if the URL starts with either "http://" or "https://"
            if not url.startswith(("http://", "https://")):
                url = "https://" + url  # Default to https:// if no scheme is found

            # Perform the scan
            scan_results, detailed_report = await self.scan_vulnerabilities(url)

            # If results exceed Discord's limit, provide a downloadable report
            if len(scan_results) > 2000:
                with open("scan_results.txt", "w") as file:
                    file.write(detailed_report)
                await ctx.send("🔍 **Scan results are too long. Download the full report:**", file=discord.File("scan_results.txt"))
                os.remove("scan_results.txt")
            else:
                # Generate paginated embeds
                pages = self.create_paginated_embeds(scan_results, url)
                view = PaginatedScanView(pages)
                await view.send(ctx)  # Send paginated results

        except Exception as e:
            await ctx.send(f"⚠️ Scan error: `{e}`")
        finally:
            # Delete the "please wait" message after the scan is done
            try:
                await waiting_message.delete()
            except discord.NotFound:
                pass  # Ignore if the message has already been deleted

            # Remove the URL/IP from the scanning set after the scan completes
            self.scanning_urls.discard(normalized_url)  # Ensure URL is removed even if an error occurs

    async def scan_vulnerabilities(self, url: str):
        """Scan the provided URL for vulnerabilities and return formatted results."""
        vulnerabilities = {
    "SQL Injection": r"'|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|WHERE|FROM|INTO|VALUES|TABLE)\b",
    "XSS": r"<script.*?>.*?</script>",
    "File Inclusion": r"(include|require)(_once)?\s*[\(\"']\s*([A-Za-z0-9_]+(\.[A-Za-z]+)?)",
    "Directory Traversal": r"\.\.(\/|\\)",
    "Command Injection": r";\s*(rm|ls|cat|echo|wget|curl|whoami|pwd)\b",
    "Session Hijacking": r"document\.cookie",
    "RCE": r"(eval|exec|passthru|shell_exec|system|popen|proc_open)\s*\(",
    "SSRF": r"(curl|file_get_contents|fsockopen|fopen|readfile|ftp_connect)\s*\(",
    "XXE": r"<!ENTITY.*SYSTEM.*>",
    "Object Injection": r"(unserialize|__wakeup|__destruct)",
    "CORS": r"Access-Control-Allow-Origin:\s*\*",
    "Buffer Overflow": r"%s|%x|%n|%h|%p",
    "LDAP Injection": r"[\|&;$><\(\)]",
    "XPath Injection": r"'[^\']*'",
    "IDOR": r"\/(users|accounts|orders)\/\d+",
    "JSON Injection": r"({|}|\[|\]|:)",
    "CRLF Injection": r"%0d%0a|\\r\\n",
    "NoSQL Injection": r"({.*:\s*.*})|(\".*\":\s*\".*\")",
    "Malicious File Upload": r"Content-Disposition:\s*form-data;\s*name=",
    "Unvalidated Redirects": r"(Location:|window\.location).*",
    "HTML Injection": r"<(iframe|embed|object|form).*?>",
    "DNS Rebinding": r"(.*\.local|.*\.lan)",
    "Host Header Injection": r"Host:\s+[^\n]*",
    "Reflected File Download": r"Content-Disposition:.*filename=.*",
    "Null Byte Injection": r"%00",
    "API Key Exposure": r"(api_key|apikey|access_token|auth_token)[\"'=:\s]+[\w\d]+",
    "Clickjacking": r"<iframe.*?>",
    "Open Redirect": r"Location:\s*https?:\/\/(?!trusted-domain).*",
    "Weak Hash Algorithm": r"(MD5|SHA1|DES|RC4)",
    "Prototype Pollution": r"\.__proto__\s*|constructor\s*\(",
    "Subdomain Takeover": r"CNAME\s+.*(unresolved|expired|not found)",
    "Bash Injection": r"\$\(.*\)",
    "Cloud Misconfiguration": r"(?i)(aws|gcp|azure).*?secret|access_key|api_key",
    "Broken Authentication": r"(login|authenticate|session)[\"'=:\s]+[^\s]+",
    "Insecure Cookies": r"Set-Cookie:\s*[^\n]*\b(Secure|HttpOnly)\b",
    "Hardcoded Credentials": r"(username|password|admin|root)[\"'=:\s]+[^\s]+",
    "Email Injection": r"(bcc:|cc:|to:)[^@]*@",
    "Server Misconfiguration": r"Server:\s*(nginx|Apache|nginx/|Microsoft-IIS)",
    "Integer Overflow": r"\b(int|long|unsigned)\s*\[\w\s\]+\s*\([0-9]+(\*|\/|%)\d+\)",
    "DDoS Vulnerability": r"(\d+)\.(\d+)\.(\d+)\.(\d+):\d+",
    "Unauthorized API Access": r"Authorization:\s*Bearer\s*([A-Za-z0-9_-]+)",
    "Session Fixation": r"JSESSIONID|PHPSESSID|ASPSESSIONID|session_id",
    "API Rate Limiting Bypass": r"X-Forwarded-For|X-Real-IP",
    "JSONP Injection": r"callback\([^\)]*\);",
    "Exposed Sensitive Data": r"(AWS|GCP|Azure|GitHub|Slack|Twilio|SendGrid)[\"'=:\s]+[\w\d]+",
    "Weak Password Policy": r"(password|username|email).*?:.*?(12345|password|qwerty|admin|123456|letmein|welcome|password1)",
    "Local File Disclosure": r"file:\/\/|\/proc\/self\/environ|\/etc\/passwd|\/etc\/shadow",
    "Server-Side Request Forgery (SSRF)": r"(curl|file_get_contents|fopen|http_request|request\s*\()",
    "Open Database Connectivity (ODBC) Injection": r"(\bODBC\s*|SQLNET|TNS\s*)",
    "Cache Poisoning": r"(cache-control|pragma|etag|expires|last-modified)\s*",
    "Resource Exhaustion (DoS)": r"(stress-test|stress|flooding|DDos|DoS|slowloris)",
    "Cross-Site Request Forgery (CSRF)": r"<form\s*action\s*=\s*\"[^\"]*\".*>\s*<input\s*type=\"hidden\"\s*name=\".*\" value=\".*\"/>",
    "Broken Object Level Authorization (BOLA)": r"\/[A-Za-z0-9_]+\/[A-Za-z0-9]+\/?([A-Za-z0-9]+)?",
    "HTTP Response Splitting": r"(Location|Content-Length|Set-Cookie)\s*:\s*[^\r\n]+",
    "Weak Session Management": r"SessionID\s*=\s*[A-Za-z0-9]{32,}",
    "Insecure Deserialization": r"(deserialize|unserialize|json_decode)\s*\(",
    "Improper Error Handling": r"(?i)(error|exception|fatal|warning|trace)",
    "Information Disclosure (Stack Trace)": r"(stack trace|backtrace|debugging|exception)",
    "Code Injection": r"eval\(.*\)|exec\(.*\)|system\(.*\)|passthru\(.*\)",
    "JWT Vulnerabilities": r"Authorization:\s*Bearer\s*([A-Za-z0-9_-]+)\.",
    "Race Condition": r"(?i)(lock|mutex|semaphore|threading)\s*=\s*(false|locked|unlocked)",
    "Path Traversal (../)": r"(\/\.\./|\/\.\.\\|\/[^/]+/[^/]+/)",
    "HSTS Missing": r"Strict-Transport-Security:\s*max-age=[0-9]{1,}",
    "SAMEORIGIN Policy Bypass": r"<iframe.*?src\s*=\s*\".*?\".*?sandbox\s*=\s*\".*?\".*?>",
    "Unsecured API Endpoints": r"(\bGET\b|\bPOST\b|\bPUT\b|\bDELETE\b)\s+.*api/v1/.*",
    "Weak Client-Side Validation": r"onerror\s*=\s*\".*\"|onload\s*=\s*\".*\"",
    "Unrestricted File Upload": r"Content-Type:\s*application\/(octet-stream|zip|exe|tar|php|html)",
    "JWT None Algorithm Vulnerability": r"alg\":\"none\"",
    "Unprotected Sensitive Data in Transit": r"(?i)(base64_encode|base64_decode)\(.*\)",
    "API Key in URL": r"(apikey|access_token|secret|jwt|auth_token)=[^\s]+",
    "Unescaped HTML": r"<([a-z]+)[^>]*>.*<\/\\1>.*",
    "Cross-Domain Scripting (XDS)": r"window\.location\s*=\s*\"[^\"]*\"",
    "Broken Link Redirects": r"href\s*=\s*\".*redirect=.*\"",
    "Session ID Exposure in URL": r"[\?&]session_id=\w+",
    "Insecure Cryptography": r"(DES|RC4|MD5|SHA1|SHA0|CRC32|FIPS|CBC)",
    "Sensitive Data Leak via Logs": r"(debug|log|exception|stack trace|traceback|request)",
    "Subdomain Enumeration": r"\.example\.com.*[\w-]+\.example\.com",
    "Data Leaks in HTTP Headers": r"Referer:.*\bhttps?://.*\b",
    "Improper Authentication Flow": r"(login|logout)\s*(\/|\.html|\.php)\b",
    "Unauthenticated API Access": r"GET\s+\/api\/v1\/(?:[A-Za-z0-9]+\/)?[A-Za-z0-9]+",
    "Unsecured WebSocket Endpoint": r"ws:\/\/[A-Za-z0-9.-]+:[0-9]+\/[A-Za-z0-9]+",
    "Command Injection via URL": r"([A-Za-z0-9\-]+)\s*=[^=&]+(\+|\&)\w+",
    "XML Injection": r"<\?xml.*?encoding=[\"']?UTF-8[\"']?\?>",
    "Sensitive Data Exposure via Cookies": r"cookie\s*=\s*[A-Za-z0-9]+",
    "Untrusted Data in WebSocket": r"ws://[A-Za-z0-9.-]+:[0-9]+/[A-Za-z0-9]+",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if "text" not in response.headers.get("Content-Type", ""):
                        return f"❌ Error: Response is not text-based (Content-Type: {response.headers.get('Content-Type', '')}).", ""

                    html_content = await response.text()

                    results = []
                    detailed_report = f"🔎 **Detailed Vulnerability Report for {url}**\n{'='*60}\n"

                    for vuln, pattern in vulnerabilities.items():
                        try:
                            # Ensure that the HTML content is not empty or None
                            if not html_content:
                                raise ValueError(f"HTML content for {url} is empty or None.")

                            # Use asyncio.to_thread to run regex search in a non-blocking thread
                            match = await asyncio.to_thread(self.run_regex, pattern, html_content)
                            if match:
                                match_text = match.group(0)[:100]  # Limit match display length
                                results.append(f"❗ **{vuln}** - `Vulnerable` (Matched: `{match_text}`)")
                                detailed_report += f"🛑 **{vuln}**\n🔹 Matched String: `{match_text}`\n🔹 Pattern Used: `{pattern}`\n\n"
                            else:
                                results.append(f"✅ **{vuln}** - `Not Vulnerable`")
                                detailed_report += f"✅ **{vuln}**\n🔹 No matching patterns found.\n\n"

                        except Exception as e:
                            results.append(f"⚠️ **{vuln}** - `Error`")
                            detailed_report += f"⚠️ **{vuln}**\n🔹 {str(e)}\n\n"

                    return results, detailed_report

            except Exception as e:
                return f"❌ Error: `{e}`", ""

    def run_regex(self, pattern, html_content):
        """Run the regex search in a non-blocking manner."""
        return re.search(pattern, html_content, re.IGNORECASE)

    def create_paginated_embeds(self, scan_results, url):
        """Create paginated embeds for better readability."""
        embeds = []
        max_items_per_page = 5  # Adjust this based on preference

        for i in range(0, len(scan_results), max_items_per_page):
            embed = discord.Embed(title=f"🔍 Scan Results for {url}", color=discord.Color.blue())
            embed.description = "\n".join(scan_results[i : i + max_items_per_page])
            embed.set_footer(
                text=f"{config.BOT_NAME} - Beta v{config.BOT_VERSION} - Developed by {self.bot.get_user(config.OWNER_ID).name}",
                icon_url=self.bot.user.avatar.url
            )
            embeds.append(embed)

        return embeds

class PaginatedScanView(discord.ui.View):
    """View to handle pagination for scan results."""

    def __init__(self, embeds):
        super().__init__(timeout=120)  # Set a 2-minute timeout
        self.embeds = embeds
        self.current_page = 0
        self.message = None

    async def send(self, ctx):
        """Send the message and store it for future updates."""
        self.message = await ctx.send(embed=self.embeds[0], view=self)

    @discord.ui.button(label="◀️ Back", style=discord.ButtonStyle.secondary, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to the previous page."""
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to the next page."""
        self.current_page += 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        """Update the embed based on the current page."""
        self.children[0].disabled = self.current_page == 0  # Disable Back button on first page
        self.children[1].disabled = self.current_page == len(self.embeds) - 1  # Disable Next button on last page

        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def on_timeout(self):
        """Disable buttons when interaction timeout expires."""
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  # Ignore error if message was deleted

async def setup(bot):
    await bot.add_cog(cwvscan(bot))
