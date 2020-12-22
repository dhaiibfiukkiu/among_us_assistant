from typing import List, Optional

import discord
import matplotlib.pyplot as plt
import networkx as nx
from discord.ext import commands
from error import DuplicateRoleError, NotAttendeeError
from networkx.drawing.nx_agraph import graphviz_layout


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)


USAGE_DOUBT = "/doubt {source|optional} {target}"
USAGE_TRUST = "/trust {source|optional} {target}"

ERROR_ROLE_NOT_FOUND = "role not found."
ERROR_DUPLICATE_ROLE = "duplicate role."
ERROR_TOO_FEW_ARGUMENTS = "too few arguments."
ERROR_TOO_MANY_ARGUMENTS = "too many arguments."
ERROR_NOT_ATTENDEE = "specified member is not attendee."
ERROR_BAD_ARGUMENT = "bad argument."
ERROR_COMMAND_INVOKE = "command invoke error."

TRUST = 0
DOUBT = 1

G = nx.DiGraph()
players = {}  # {discord.Member: Player}
relations = {}  # {(discord.Member, discord.Member): int}
plt.style.use('grey')
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Hiragino Maru Gothic Pro",
    "Yu Gothic",
    "Meirio",
    "Takao",
    "IPAexGothic",
    "IPAPGothic",
    "VL PGothic",
    "Noto Sans CJK JP",
]


def node_color(player: Player) -> str:
    """
    ノードカラーのマッピング
    """
    if player.color == "red":
        return "red"
    if player.color == "blue":
        return "blue"
    if player.color == "yellow":
        return "yellow"
    if player.color == "pink":
        return "fuchsia"
    if player.color == "green":
        return "green"
    if player.color == "lime":
        return "lime"
    if player.color == "brown":
        return "saddlebrown"
    if player.color == "white":
        return "whitesmoke"
    if player.color == "purple":
        return "purple"
    if player.color == "cyan":
        return "cyan"
    if player.color == "black":
        return "dimgrey"
    if player.color == "orange":
        return "orange"
    return "black"


def edge_color(relation: int) -> str:
    """
    エッジカラーのマッピング
    """
    if relation == DOUBT:
        return "red"
    if relation == TRUST:
        return "cyan"
    return "black"


def draw_graph() -> discord.File:
    """
    グラフ描画
    """
    plt.clf()
    edges = []
    for r in relations.keys():
        edges.append(r)
    nodes = []
    for p in players.values():
        nodes.append(p)
    G.add_nodes_from(nodes)
    for p in players.values():
        if len([i for i in nx.neighbors(G, p)]) == 0:
            G.remove_node(p)
    G.add_edges_from(edges)
    options = {
        "node_color": [node_color(player) for player in G.nodes()],
        "edge_color": [edge_color(relation) for relation in relations.values()],
        "node_size": 800,
        "width": 2,
        "arrowstyle": "-|>",
        "arrowsize": 20,
    }
    pos = graphviz_layout(G, prog="fdp")
    nx.draw_networkx(
        G, pos, connectionstyle="arc3, rad=0.1", arrows=True, **options, font_size=14
    )
    plt.tight_layout(pad=0)
    plt.savefig("figure.png")
    return discord.File("figure.png")


def get_usage(usage: str, error: str = None) -> discord.Embed:
    if error:
        embed = discord.Embed(title="Error", description=error, color=0xFF0000)
        embed.add_field(name="usage", value=usage)
    else:
        embed = discord.Embed(title="usage", description=usage, color=0x00FF00)
    return embed


def has_duplicates(seq: list) -> bool:
    return len(seq) != len(set(seq))


def update_attendees(func):
    def wrapper(*args, **kwargs):
        # ctx.g
        # attendees ロールのついている人をみてplayersを更新
        func(*args, **kwargs)

    return wrapper


def is_attendee(member: discord.Member) -> bool:
    for r in member.roles:
        if r.name == "attendees":
            return True
    return False


def add_relation(
    source: Optional[discord.Member], target: Optional[discord.Member], type: int
) -> None:
    s = players[source]
    t = players[target]
    relations[(s, t)] = type


def find_attendee_by_role(
    attendees: List[discord.Member], role_name: str
) -> Optional[discord.Member]:
    attendee = None
    for a in attendees:
        for r in a.roles:
            if role_name == r.name:
                attendee = a
    return attendee


class Assistant(commands.Cog):
    @commands.command()
    async def name(self, ctx, *args):
        pass

    @commands.command()
    async def clear(self, ctx, *args):
        global players
        global relations
        plt.clf()
        edges = []
        nodes = []
        for r in relations.keys():
            edges.append(r)
        nodes = []
        for p in players.values():
            nodes.append(p)
        G.remove_edges_from(edges)
        G.remove_nodes_from(nodes)
        players = {}
        relations = {}
        embed = discord.Embed(
            title="clear", description="graph has been cleared", color=0x00FF00
        )
        await ctx.send(embed=embed)
        return

    @commands.command()
    async def trust(
        self, ctx, first_role: discord.Role, second_role: discord.Role = None
    ):
        if first_role == second_role:
            raise DuplicateRoleError
        # TODO decorator化
        members = [i async for i in ctx.guild.fetch_members(limit=150) if not i.bot]
        attendees = [i for i in members if is_attendee(i)]
        for a in attendees:
            role = [
                i for i in a.roles if i.name != "@everyone" and i.name != "attendees"
            ][0]
            players[a] = Player(a.name, role.name)
        if not second_role:
            source: Optional[discord.Member] = discord.utils.find(
                lambda m: m.name == ctx.author.name, attendees
            )
            target: Optional[discord.Member] = find_attendee_by_role(
                attendees, first_role.name
            )
        else:
            source: Optional[discord.Member] = find_attendee_by_role(
                attendees, first_role.name
            )
            target: Optional[discord.Member] = find_attendee_by_role(
                attendees, second_role.name
            )
        if not source or not target:
            raise NotAttendeeError
        add_relation(source, target, TRUST)
        await ctx.send(file=draw_graph())
        return

    @commands.command()
    async def doubt(
        self, ctx, first_role: discord.Role, second_role: discord.Role = None
    ):
        if first_role == second_role:
            raise DuplicateRoleError
        # TODO decorator化
        members = [i async for i in ctx.guild.fetch_members(limit=150) if not i.bot]
        attendees = [i for i in members if is_attendee(i)]
        for a in attendees:
            role = [
                i for i in a.roles if i.name != "@everyone" and i.name != "attendees"
            ][0]
            players[a] = Player(a.name, role.name)
        if not second_role:
            source: Optional[discord.Member] = discord.utils.find(
                lambda m: m.name == ctx.author.name, attendees
            )
            target: Optional[discord.Member] = find_attendee_by_role(
                attendees, first_role.name
            )
        else:
            source: Optional[discord.Member] = find_attendee_by_role(
                attendees, first_role.name
            )
            target: Optional[discord.Member] = find_attendee_by_role(
                attendees, second_role.name
            )
        if not source or not target:
            raise NotAttendeeError
        add_relation(source, target, DOUBT)
        await ctx.send(file=draw_graph())
        return

    @doubt.error
    @trust.error
    async def doubt_error(self, ctx: commands.Context, error):
        print(type(error))
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=get_usage(USAGE_DOUBT, str(error)))
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=get_usage(USAGE_DOUBT, str(error)))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Assistant(bot))
