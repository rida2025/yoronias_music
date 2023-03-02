import wavelink
import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context, Greedy#, commands
from wavelink.tracks import YouTubeTrack

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

    @app_commands.command()
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
        await interaction.response.send_message(f"Now playing `{track.title}` by `{track.author}`", allowed_mentions=discord.AllowedMentions.none())



    # @client.tree.command()
    # async def resume(ctx):
    #    voice = get(client.voice_clients, guild=ctx.guild)
    #
    #    if not voice.is_playing():
    #        voice.resume()
    #        await ctx.send('Bot is resuming')

    # @client.tree.command(name="join")
    # async def join(ctx):
    #    if not ctx.message.author.voice:
    #        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
    #        return
    #    else:
    #        channel = ctx.message.author.voice.channel
    #    await channel.connect()

    # @client.tree.command()
    # async def clear(ctx, amount=5):
    #    await ctx.channel.purge(limit=amount)
    #    await ctx.send("Messages have been cleared")

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