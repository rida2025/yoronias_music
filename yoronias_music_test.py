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
        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='lavalink2.devamop.in',
                                            port=8830,
                                            password="DevamOP")


    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')


    @app_commands.command(name="play", description="this is the working play")
    async def play(self, interaction: discord.Interaction, *, search: str):

        search_results = await wavelink.YouTubeTrack.search(search)
        search = search_results[0]

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        if vc.queue.is_empty and not vc.is_playing():
            await vc.queue.put_wait(search)
            vc.autoplay = True
            await vc.play(await vc.queue.get_wait())
            await interaction.response.send_message(f"Now playing `{search.title}` by `{search.author}`",

                                                allowed_mentions=discord.AllowedMentions.none())
        else:
            await vc.queue.put_wait(search)
            await interaction.response.send_message(f'Added `{search.title}` to the queue...')

    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: commands.Context):
        vc: wavelink.Player = interaction.guild.voice_client

        if not vc or vc.queue.is_empty:
            await interaction.response.send_message("The queue is currently empty.", ephemeral=True)
        else:
            tracks = [f"{i + 1}. {track.title}" for i, track in enumerate(vc.queue)]
            queue_message = "\n".join(tracks)
            await interaction.response.send_message(f"Current Queue:\n{queue_message}", ephemeral=True)

    @app_commands.command(name="skip", description="to skip the current music")
    async def skip(self, interaction: commands.Context):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc.queue.is_empty:
            await vc.stop()
            search = await vc.queue.get_wait()
            await vc.play(search)
            # {wavelink.Player.queue.history[vc.queue.history.find_position(wavelink.Player.current) + 1]}
            await interaction.response.send_message(f"Now playing `{search.title}` by `{search.author}", delete_after=5)

    @app_commands.command(name="pause", description="to pause the music")
    async def pause(self, interaction):
        voice = interaction.guild.voice_client
        if voice and voice.is_playing():
            await voice.pause()
            await interaction.response.send_message('pause...')
        else:
            await interaction.response.send_message('the bot is not in a voice chat')

    @app_commands.command(name="leave", description="to leave the voice chat")
    async def leave(self, interaction):
        voice = interaction.guild.voice_client
        if voice and voice.is_playing():
            await voice.disconnect()
            await interaction.response.send_message('stop...')
        else:
            await interaction.response.send_message('the bot is not in a voice chat')

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
            await interaction.response.send_message('Resuming playback.')
            return

    @app_commands.command(name="clear", description="to clear lines")
    async def clear(self, ctx: Context, amount: int):
        amount = amount + 1
        await ctx.response.defer()
        await ctx.channel.purge(limit=amount)
        await ctx.followup.send(f"```{amount-1} Messages will be cleared```")

    @app_commands.command(name="help", description="a help command")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message('```play,leave,clear,resume,pause,skip```')

    @app_commands.command(name="volume", description="from 0 to 100")
    async def volume(self, interaction: commands.Context, value: int):
        value = value * 10
        vc: wavelink.Player = interaction.guild.voice_client

        if vc and vc.is_playing():
            await vc.set_volume(value)
            value = value / 10
            await interaction.response.send_message(f"``` the volume is {value}```")
        else:
            await interaction.response.send_message('the bot is not in a voice chat')

    @app_commands.command(name="stop", description="to stop the music some time it skip xD")
    async def stop(self, interaction):
        voice = interaction.guild.voice_client
        if voice and voice.is_playing():
            await voice.stop()
            await interaction.response.send_message('stop...')
        else:
            await interaction.response.send_message('the bot is not in a voice chat')



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
bot.run("TOKEN")
