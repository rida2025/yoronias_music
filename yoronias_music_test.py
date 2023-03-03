import wavelink
import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context, Greedy#, commands
from wavelink.tracks import YouTubeTrack
import asyncio

from typing import Optional, Literal
from discord import app_commands


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!",
                         intents=discord.Intents.all())

    async def on_ready(self):
        print('Bot online')

    async def setup_hook(self):
        await self.add_cog(Music(bot))




class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot, host='lava1.horizxon.studio', port=80,
                                            password="horizxon.studio")


    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')


    @app_commands.command(name="play", description="this is the working play")
    async def play(self, interaction: discord.Interaction, *, search: str):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """

        search = await wavelink.YouTubeTrack.search(search)

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        track = search[0]

        await vc.play(track)
        await interaction.response.send_message(f"Now playing `{track.title}` by `{track.author}`",
                                                allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="pause", description="to pause the music")
    async def pause(self, interaction):
        voice = interaction.guild.voice_client
        if voice and voice.is_playing():
            await voice.pause()
            await interaction.response.send_message('pause...')
        else:
            await interaction.response.send_message(ephemeral='the bot is not in a voice chat')

    @app_commands.command(name="leave", description="to leave the voice chat")
    async def leave(self, interaction):
        voice = interaction.guild.voice_client
        if voice and voice.is_playing():
            await voice.disconnect()
            await interaction.response.send_message('stop...')
        else:
            await interaction.response.send_message(ephemeral='the bot is not in a voice chat')

    @app_commands.command(name="resume", description="to resume the music after pause")
    async def resume(self, interaction):
        channel = interaction.user.voice.channel
        voice = interaction.guild.voice_client
        if not voice:
            voice = await channel.connect()
        else:
            await voice.move_to(channel)

            # Resume playback if paused
        if voice.is_paused():
            await voice.resume()
            await interaction.response.send_message(ephemeral='Resuming playback.')
            return

    @app_commands.command(name="clear", description="to clear lines")
    async def purge(self, interaction, amount: int):
        amount = amount + 1
        await interaction.response.defer()
        await interaction.channel.purge(limit=amount)
        await interaction.followup.send(ephemeral="Messages have been cleared")




    # @client.tree.command(name="join")
    # async def join(ctx):
    #    if not ctx.message.author.voice:
    #        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
    #        return
    #    else:
    #        channel = ctx.message.author.voice.channel
    #    await channel.connect()


bot = Bot()

@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
        ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
bot.run("ODc4MjY4OTQ1MDc1OTM3Mjkw.GgOI-_.9f_wo78QUu265dtF1qRoAS-VP60fAKItq3qqOU")