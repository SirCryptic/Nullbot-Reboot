import discord
from discord.ext import commands
import config

class Log(commands.Cog):
    """Logs user actions and server events."""

    def __init__(self, bot):
        self.bot = bot

    # Member Update - Mute/Unmute
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            if before.communication_disabled_until != after.communication_disabled_until:
                if after.communication_disabled_until:
                    embed = discord.Embed(
                        title="🔇 User Muted",
                        description=f"**User:** {after.mention}\n**Muted Until:** {after.communication_disabled_until}",
                        color=discord.Color.red()
                    )
                    await log_channel.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="🔊 User Unmuted",
                        description=f"**User:** {after.mention}",
                        color=discord.Color.green()
                    )
                    await log_channel.send(embed=embed)

            if before.nick != after.nick:  # Nickname change log
                embed = discord.Embed(
                    title="✏️ User Nickname Changed",
                    description=f"**User:** {after.mention}\n**Old Nickname:** {before.nick or 'None'}\n**New Nickname:** {after.nick or 'None'}",
                    color=discord.Color.blue()
                )
                await log_channel.send(embed=embed)

    # Member Banned/Unbanned
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🔨 User Banned",
                description=f"**User:** {user.mention}\n**User ID:** {user.id}",
                color=discord.Color.red()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🔓 User Unbanned",
                description=f"**User:** {user.mention}\n**User ID:** {user.id}",
                color=discord.Color.green()
            )
            await log_channel.send(embed=embed)

    # Channel Created/Deleted
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🆕 Channel Created",
                description=f"**Channel:** #{channel.name}",
                color=discord.Color.green()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="❌ Channel Deleted",
                description=f"**Channel:** #{channel.name}",
                color=discord.Color.red()
            )
            await log_channel.send(embed=embed)

    # Voice State Updates (Join/Leave Voice Channel)
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            if before.channel is None and after.channel is not None:
                embed = discord.Embed(
                    title="🎤 User Joined Voice Channel",
                    description=f"**User:** {member.mention}\n**Channel:** {after.channel.name}",
                    color=discord.Color.green()
                )
                await log_channel.send(embed=embed)

            elif before.channel is not None and after.channel is None:
                embed = discord.Embed(
                    title="🎤 User Left Voice Channel",
                    description=f"**User:** {member.mention}\n**Channel:** {before.channel.name}",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)

    # Role Permissions Updated
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            if before.permissions != after.permissions:
                embed = discord.Embed(
                    title="⚙️ Role Permissions Updated",
                    description=f"**Role:** {after.name}\n**Permissions Changed:** {before.permissions} → {after.permissions}",
                    color=discord.Color.blue()
                )
                await log_channel.send(embed=embed)

    # Invite Created/Deleted
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🔗 Invite Created",
                description=f"**Invite Link:** {invite.url}\n**Channel:** #{invite.channel.name}",
                color=discord.Color.green()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="❌ Invite Deleted",
                description=f"**Invite Link:** {invite.url}\n**Channel:** #{invite.channel.name}",
                color=discord.Color.red()
            )
            await log_channel.send(embed=embed)

    # Webhook Created/Deleted
    @commands.Cog.listener()
    async def on_webhook_create(self, webhook):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🆕 Webhook Created",
                description=f"**Webhook Name:** {webhook.name}\n**Channel:** #{webhook.channel.name}",
                color=discord.Color.green()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_webhook_delete(self, webhook):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="❌ Webhook Deleted",
                description=f"**Webhook Name:** {webhook.name}\n**Channel:** #{webhook.channel.name}",
                color=discord.Color.red()
            )
            await log_channel.send(embed=embed)

    # Emojis Updated (Added/Removed)
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            added_emojis = [emoji for emoji in after if emoji not in before]
            removed_emojis = [emoji for emoji in before if emoji not in after]

            if added_emojis:
                added_emoji_names = ", ".join(emoji.name for emoji in added_emojis)
                embed = discord.Embed(
                    title="😀 Emoji Added",
                    description=f"**Emojis Added:** {added_emoji_names}",
                    color=discord.Color.green()
                )
                await log_channel.send(embed=embed)

            if removed_emojis:
                removed_emoji_names = ", ".join(emoji.name for emoji in removed_emojis)
                embed = discord.Embed(
                    title="❌ Emoji Removed",
                    description=f"**Emojis Removed:** {removed_emoji_names}",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)

    # Server Boosted/Unboosted
    @commands.Cog.listener()
    async def on_guild_member_update(self, before, after):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            if before.premium_since != after.premium_since:
                if after.premium_since:
                    embed = discord.Embed(
                        title="🚀 Server Boost",
                        description=f"**User:** {after.mention}\n**Boosted Since:** {after.premium_since.strftime('%Y-%m-%d %H:%M:%S')}",
                        color=discord.Color.green()
                    )
                    await log_channel.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ Server Boost Removed",
                        description=f"**User:** {after.mention}",
                        color=discord.Color.red()
                    )
                    await log_channel.send(embed=embed)

    # File Attachments in Messages
    @commands.Cog.listener()
    async def on_message(self, message):
        log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            if message.attachments:
                file_names = [attachment.filename for attachment in message.attachments]
                embed = discord.Embed(
                    title="📎 File Sent",
                    description=f"**User:** {message.author.mention}\n**Files:** {', '.join(file_names)}",
                    color=discord.Color.blue()
                )
                await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Log(bot))
