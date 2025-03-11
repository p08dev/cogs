from .exclusiveroles import ExclusiveRoles


async def setup(bot):
    cog = ExclusiveRoles(bot)
    r = bot.add_cog(cog)
    if r is not None:
        await r