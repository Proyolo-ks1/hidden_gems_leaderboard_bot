# helper_scripts/custom_help.py

import discord
from discord.ext import commands
from typing import Optional

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self, **options):
        # Set a default color for all help embeds
        super().__init__(**options)
        self.embed_color = discord.Color.blue()
        self.no_category = "General Commands" # Name for commands not in a cog

    def generate_embed(self, title: str, description: Optional[str] = None) -> discord.Embed:
        """Helper function to quickly create a base embed."""
        embed = discord.Embed(
            title=f"🤖 {title}",
            description=description,
            color=self.embed_color
        )
        # Use the bot's current prefix in the footer
        embed.set_footer(text=f"Use {self.context.prefix}help [command] for more details.")
        return embed

    # --- Help for the entire bot (No argument: !help) ---
    async def send_bot_help(self, mapping: dict):
        ctx = self.context
        prefix = ctx.prefix
        
        embed = self.generate_embed(
            f"Hidden Gems Leaderboard Bot Commands",
            f"Here are the command categories. The current prefix is: `{prefix}`"
        )
        
        for cog, cog_commands in mapping.items():
            # Filter out hidden commands and check if commands exist
            filtered_commands = await self.filter_commands(cog_commands, sort=True)
            
            if filtered_commands:
                # Get cog info, falling back to a default name
                cog_name = getattr(cog, "qualified_name", self.no_category)
                cog_description = getattr(cog, "description", "")
                
                # List commands, aliases, and their short descriptions (UPDATED LOGIC)
                command_list = []
                for c in filtered_commands:
                    # Safely extract short description
                    # Uses '\n' for safety check, as requested
                    short_desc = c.short_doc or (c.help.split('\n')[0].strip() if c.help else '...')
                    
                    # Prepare and include aliases
                    alias_str = f" (Aliases: {', '.join(c.aliases)})" if c.aliases else ""
                    
                    command_list.append(
                        # Format: `command_name (Aliases: alias1, alias2)` - Short description
                        f"`{c.name}{alias_str}` - {short_desc}"
                    )

                field_value = (
                    f"*{cog_description}*\n\n"
                    # Uses '\n'.join for clarity, as requested
                    f"{'\n'.join(command_list)}" if cog_description else '\n'.join(command_list)
                )

                embed.add_field(
                    name=f"✨ {cog_name}",
                    value=field_value,
                    inline=False
                )
        
        await ctx.send(embed=embed)


    # --- Help for a specific command (e.g., !help maps) ---
    async def send_command_help(self, command: commands.Command):
        ctx = self.context
        
        embed = self.generate_embed(
            f"Command: {command.qualified_name}",
            # command.help naturally handles new lines (\n) in the docstring
            command.help or "No detailed description provided."
        )
        
        # Add usage field
        signature = command.signature
        embed.add_field(
            name="Usage",
            value=f"`{ctx.prefix}{command.qualified_name} {signature}`",
            inline=False
        )
        
        if command.aliases:
            embed.add_field(
                name="Aliases",
                # Lists aliases in a single code block
                value=f"`{', '.join(command.aliases)}`",
                inline=False
            )
            
        await ctx.send(embed=embed)

    # --- Error handling ---
    async def send_error_message(self, error: str):
        destination = self.get_destination()
        embed = discord.Embed(
            title="❌ Help Error",
            description=error,
            color=discord.Color.red()
        )
        await destination.send(embed=embed)