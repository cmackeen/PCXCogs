"""ReactChannel cog for Red-DiscordBot by PhasecoreX."""
import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import box, error

__author__ = "PhasecoreX"


class ReactChannel(commands.Cog):
    """Per-channel auto reaction tools."""

    default_guild_settings = {"channels": {}}

    def __init__(self, bot):
        """Set up the plugin."""
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, 1224364860)
        self.config.register_guild(**self.default_guild_settings)

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def reactchannelset(self, ctx: commands.Context):
        """Manage ReactChannel settings."""

    @reactchannelset.command()
    async def enable(
        self,
        ctx: commands.Context,
        channel_type: str,
        channel: discord.TextChannel = None,
    ):
        """Enable ReactChannel functionality in this channel.

        `channel_type` can be any of:
        - `checklist`: All messages will have a checkmark. Clicking it will delete the message.
        - `vote`: All messages will have an up and down arrow.
        """
        if channel is None:
            channel = ctx.message.channel
        if channel_type not in ["checklist", "vote"]:
            await ctx.send(
                error("`{}` is not a supported channel type.".format(channel_type))
            )
            return

        channels = await self.config.guild(ctx.message.guild).channels()
        channels[str(channel.id)] = channel_type
        await self.config.guild(ctx.message.guild).channels.set(channels)
        await ctx.send(
            checkmark("{} is now a {} ReactChannel.".format(channel, channel_type))
        )

    @reactchannelset.command()
    async def disable(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Disable ReactChannel functionality in this channel."""
        if channel is None:
            channel = ctx.message.channel

        channels = await self.config.guild(ctx.message.guild).channels()
        try:
            del channels[str(channel.id)]
        except KeyError:
            pass
        await self.config.guild(ctx.message.guild).channels.set(channels)
        await ctx.send(
            checkmark(
                "ReactChannel functionality has been disabled on {}.".format(channel)
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Watch for messages in enabled react channels to add reactions."""
        if message.guild is None or message.channel is None:
            return
        channels = await self.config.guild(message.guild).channels()
        if str(message.channel.id) not in channels:
            return
        can_react = message.channel.permissions_for(message.guild.me).add_reactions
        if not can_react:
            return
        channel_type = channels[str(message.channel.id)]
        if channel_type == "checklist":
            await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        elif channel_type == "vote":
            await message.add_reaction("\N{UPWARDS BLACK ARROW}")
            await message.add_reaction("\N{DOWNWARDS BLACK ARROW}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, member: discord.Member):
        """Watch for reactions on messages in react channels and perform actions on them."""
        if not reaction.message or not reaction.message.guild:
            return
        if member.bot:
            return
        channels = await self.config.guild(reaction.message.guild).channels()
        channel_type = channels[str(reaction.message.channel.id)]
        if (
            str(reaction.emoji) == "\N{WHITE HEAVY CHECK MARK}"
            and channel_type == "checklist"
        ):
            try:
                await reaction.message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
        elif (
            str(reaction.emoji) == "\N{UPWARDS BLACK ARROW}"
            or str(reaction.emoji) == "\N{DOWNWARDS BLACK ARROW}"
        ) and channel_type == "vote":
            opposite_emoji = (
                "\N{DOWNWARDS BLACK ARROW}"
                if str(reaction.emoji) == "\N{UPWARDS BLACK ARROW}"
                else "\N{UPWARDS BLACK ARROW}"
            )
            opposite_reactions = next(
                reaction
                for reaction in reaction.message.reactions
                if str(reaction.emoji) == opposite_emoji
            )
            try:
                await opposite_reactions.remove(member)
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                pass


def checkmark(text: str) -> str:
    """Get text prefixed with a checkmark emoji."""
    return "\N{WHITE HEAVY CHECK MARK} {}".format(text)
