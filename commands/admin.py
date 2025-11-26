# commands/admin.py

from discord.ext import commands
from discord import TextChannel

class AdminCommands(commands.Cog):
    def __init__(self, bot, admins, channels_to_post, scheduled_channels, save_channels_func):
        self.bot = bot
        self.admins = admins
        self.channels_to_post = channels_to_post
        self.scheduled_channels = scheduled_channels
        self.save_channels = save_channels_func

    @commands.command(name="ping", aliases=["p"])
    async def ping_command(self, ctx):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! {latency_ms}ms")

    @commands.command(name="stopbot", aliases=["stop"])
    async def stop_bot_command(self, ctx):
        if ctx.author.id not in self.admins:
            return await ctx.send("🚫 Keine Berechtigung.")
        await ctx.send("⏹️ Bot wird heruntergefahren...")
        await self.bot.close()

    @commands.command(name="schedule", aliases=["s"])
    async def schedule_command(self, ctx, action: str = ""):
        valid_actions = ["start", "stop", "list"]
        if not action or action.lower() not in valid_actions:
            return await ctx.send(f"Usage: {ctx.prefix}schedule [start|stop|list]")

        action = action.lower()
        channel_id = ctx.channel.id

        if action == "start":
            self.channels_to_post.add(channel_id)
            self.scheduled_channels[str(channel_id)] = f"{ctx.guild.name}#{ctx.channel.name}"
            self.save_channels()
            await ctx.send("✅ Scheduler aktiviert.")

        elif action == "stop":
            if channel_id in self.channels_to_post:
                self.channels_to_post.remove(channel_id)
                self.scheduled_channels.pop(str(channel_id), None)
                self.save_channels()
                await ctx.send("✅ Scheduler deaktiviert.")
            else:
                await ctx.send("ℹ️ Nicht aktiviert.")

        elif action == "list":
            if ctx.author.id not in self.admins:
                return await ctx.send("🚫 Admins only.")
            msg = "\n".join([f"`{k}`: {v}" for k, v in self.scheduled_channels.items()])
            await ctx.send(f"📋 Channels:\n{msg}" if msg else "📭 Leer.")

async def setup(bot):
    # This setup is handled manually in registry.py due to custom init args
    pass