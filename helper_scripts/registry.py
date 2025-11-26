# helper_scripts/registry.py

from commands.admin import AdminCommands
from commands.leaderboard import LeaderboardCommand
from commands.tracking import TrackingCommand
from commands.stats import StatsCommand
from commands.maps import MapsCommand

async def register_commands(bot, admins, channels_to_post, scheduled_channels, save_channels, send_leaderboard):
    
    # Add Cogs with Dependencies
    await bot.add_cog(AdminCommands(bot, admins, channels_to_post, scheduled_channels, save_channels))
    await bot.add_cog(LeaderboardCommand(bot))
    await bot.add_cog(TrackingCommand(bot))
    await bot.add_cog(StatsCommand(bot))
    await bot.add_cog(MapsCommand(bot))

    print("✅ All commands registered.")