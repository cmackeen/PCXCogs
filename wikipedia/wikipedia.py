"""Wikipedia cog for Red-DiscordBot ported by PhasecoreX."""
import aiohttp
import discord
from redbot.core import __version__ as redbot_version
from redbot.core import commands
from redbot.core.utils.chat_formatting import error, warning

__author__ = "PhasecoreX"


class KeyDict(dict):
  def __missing__(self,key):
    return key
  
dfct=KeyDict()
dfct["keith"]="female figure"
dfct["Keith"]="female figure"

dfct["jeff"]="hyperhidrosis"
dfct["Jeff"]="hyperhidrosis"
dfct["jon"]="stoner rock"
dfct["John"]="stoner rock"

class Wikipedia(commands.Cog):
    """Look up stuff on Wikipedia."""

    base_url = "https://en.wikipedia.org/w/api.php"
    headers = {"user-agent": "Red-DiscordBot/" + redbot_version}
    footer_icon = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Wikimedia-logo.png"
        "/600px-Wikimedia-logo.png"
    )
    
    @commands.command(aliases=["add"])
    async def create(self, ctx: commands.Context, key: str, *, text: str):
        """Create a reminder. Same as [p]remindme.
        Accepts: seconds, minutes, hours, days, weeks
        Examples:
        - [p]reminder create 2min Do that thing soon in 2 minutes
        - [p]remindme create 3h40m Do that thing later in 3 hours and 40 minutes
        - [p]reminder create 3 days Have sushi with Ryan and Heather
        """
        dfct[key] = text
        return 
    
    @commands.command(aliases=["wiki"])
    async def wikipedia(self, ctx: commands.Context, *, query: str):
        """Get information from Wikipedia."""
        payload = self.generate_payload(dfct[query])
        conn = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(
                self.base_url, params=payload, headers=self.headers
            ) as res:
                result = await res.json()

        try:
            # Get the last page. Usually this is the only page.
            for page in result["query"]["pages"]:
                title = page["title"]
                description = page["extract"].strip().replace("\n", "\n\n")
                url = "https://en.wikipedia.org/wiki/{}".format(title.replace(" ", "_"))

            if len(description) > 1500:
                description = description[:1500].strip()
                description += "... [(read more)]({})".format(url)

            embed = discord.Embed(
                title="Wikipedia: {}".format(title),
                description=u"\u2063\n{}\n\u2063".format(description),
                color=discord.Color.blue(),
                url=url,
            )
            embed.set_footer(
                text="Information provided by Wikimedia", icon_url=self.footer_icon
            )
            await ctx.send(embed=embed)

        except KeyError:
            await ctx.send(
                error("I'm sorry, I couldn't find \"{}\" on Wikipedia".format(query))
            )
        except discord.Forbidden:
            await ctx.send(
                warning("I'm not allowed to do embeds here...\n{}".format(url))
            )

    @staticmethod
    def generate_payload(query: str):
        """Generate the payload for Wikipedia based on a query string."""
        payload = {}
        payload["action"] = "query"
        payload["titles"] = query.replace(" ", "_")
        payload["format"] = "json"
        payload["formatversion"] = "2"  # Cleaner json results
        payload["prop"] = "extracts"  # Include extract in returned results
        payload["exintro"] = "1"  # Only return summary paragraph(s) before main content
        payload["redirects"] = "1"  # Follow redirects
        payload["explaintext"] = "1"  # Make sure it's plaintext (not HTML)
        return payload
