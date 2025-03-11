import asyncio

import discord
from redbot.core import Config, checks, commands
from redbot.core.commands import Cog


class ExclusiveRole(Cog):
    """
    Create roles that prevent all other exclusive roles from being added
    """

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9999114111108101)
        default_guild = {"role_list": []}

        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    @commands.guild_only()
    @commands.group(aliases=["exclusiverole"])
    async def exclusive(self, ctx):
        """Base command for managing exclusive roles"""

        pass

    @exclusive.command(name="add")
    @checks.mod_or_permissions(administrator=True)
    async def exclusive_add(self, ctx, role: discord.Role):
        """Adds an exclusive role"""
        if role.id in (await self.config.guild(ctx.guild).role_list()):
            await ctx.send("That role is already exclusive")
            return

        async with self.config.guild(ctx.guild).role_list() as rl:
            rl.append(role.id)

        await self.check_guild(ctx.guild)

        await ctx.send("Exclusive role added")

    @exclusive.command(name="delete")
    @checks.mod_or_permissions(administrator=True)
    async def exclusive_delete(self, ctx, role: discord.Role):
        """Deletes an exclusive role"""
        if role.id not in (await self.config.guild(ctx.guild).role_list()):
            await ctx.send("That role is not exclusive")
            return

        async with self.config.guild(ctx.guild).role_list() as rl:
            rl.remove(role.id)

        await ctx.send("Exclusive role removed")

    @exclusive.command(name="list")
    @checks.mod_or_permissions(administrator=True)
    async def exclusive_list(self, ctx):
        """List current exclusive roles"""
        role_list = await self.config.guild(ctx.guild).role_list()
        guild: discord.Guild = ctx.guild

        role_list = [guild.get_role(role_id) for role_id in role_list]
        out = "**Exclusive roles**\n\n"

        for role in role_list:
            out += "{}\n".format(role)

        await ctx.send(out)

    async def check_guild(self, guild: discord.Guild):
        role_set = set(await self.config.guild(guild).role_list())
        for member in guild.members:
            try:
                await self.remove_non_exclusive_roles(member, role_set=role_set)
            except discord.Forbidden:
                pass

    async def remove_non_exclusive_roles(self, member: discord.Member, role_set=None):
        if role_set is None:
            role_set = set(await self.config.guild(member.guild).role_list())

        member_set = {role.id for role in member.roles}
        
        # Rolle für exklusive Rollen
        exclusive_roles = {role.id for role in role_set if role.is_exclusive}  # Beispiel, du kannst dies je nach Implementierung anpassen
        
        # Prüfen, ob bereits eine exklusive Rolle gesetzt ist
        existing_exclusive_roles = member_set & exclusive_roles
        
        if existing_exclusive_roles:
            # Entferne alle exklusiven Rollen, wenn eine andere exklusive Rolle gesetzt wird
            to_remove = [discord.utils.get(member.guild.roles, id=r_id) for r_id in existing_exclusive_roles]
            await member.remove_roles(*to_remove, reason="Exclusive role replaced")

        # Jetzt die neue exklusive Rolle hinzufügen, falls sie gesetzt ist
        new_exclusive_role = next((role for role in role_set if role.id not in member_set), None)
        if new_exclusive_role:
            await member.add_roles(new_exclusive_role, reason="Exclusive role added")
        
        # Entferne alle nicht-exklusiven Rollen, die gesetzt sind
        to_remove_non_exclusive = (member_set - role_set) - {member.guild.default_role.id} - exclusive_roles
        if to_remove_non_exclusive:
            to_remove_non_exclusive = [discord.utils.get(member.guild.roles, id=r_id) for r_id in to_remove_non_exclusive]
            await member.remove_roles(*to_remove_non_exclusive, reason="Non-exclusive roles removed")


    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return

        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return

        await asyncio.sleep(1)

        role_set = set(await self.config.guild(after.guild).role_list())
        member_set = {role.id for role in after.roles}

        if role_set & member_set:
            try:
                await self.remove_non_exclusive_roles(after, role_set=role_set)
            except discord.Forbidden:
                pass