import discord
import matplotlib.pyplot as plt
import networkx as nx
from discord.ext import commands
from networkx.drawing.nx_agraph import graphviz_layout

bot = commands.Bot(command_prefix="/")

client = discord.Client()
TOKEN: str = ""

USAGE_DOUBT = "/doubt {source|optional} {target}"

ERROR_ROLE_NOT_FOUND = "role not found."
ERROR_DUPLICATE_ROLE = "duplicate role."
ERROR_TOO_FEW_ARGUMENTS = "too few arguments."
ERROR_TOO_MANY_ARGUMENTS = "too many arguments."

TRUST = 0
DOUBT = 1

G = nx.DiGraph()


class Player():
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)


players = {} # {discord.Member: Player}
relations = {} # {(discord.Member, discord.Member): int}


def node_color(player):
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


def edge_color(relation):
    """
    エッジカラーのマッピング
    """
    if relation == DOUBT:
        return "red"
    if relation == TRUST:
        return "cyan"
    return "black"


def draw_graph():
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
    nx.draw_networkx(G, pos, connectionstyle="arc3, rad=0.1", arrows=True, **options, font_size=14)
    # plt.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.15)
    plt.tight_layout(pad=0)
    plt.savefig("figure.png")
    return discord.File("figure.png")


def get_doubt_usage(error=None):
    if error:
        embed = discord.Embed(title="Error", description=error, color=0xFF0000)
        embed.add_field(name="usage", value=USAGE_DOUBT)
    else:
        embed = discord.Embed(
            title="usage", description=USAGE_DOUBT, color=0x00FF00)
    return embed


def has_duplicates(seq: list):
    return len(seq) != len(set(seq))


def update_attendees(func):
    def wrapper(*args, **kwargs):
        # ctx.g
        # attendees ロールのついている人をみてplayersを更新
        func(*args, **kwargs)
    return wrapper


def is_attendee(member: discord.Member):
    for r in member.roles:
        if r.name == "attendees":
            return True
    return False


def add_relation(source, target, type):
    if not source or not target or source == target:
        raise Exception
    s = players[source]
    t = players[target]
    relations[(s, t)] = type


@bot.command()
async def name(ctx, *args):
    pass


@bot.command()
async def trust(ctx, *args):
    pass



@bot.command()
async def doubt(ctx, *args):
    if len(args) == 0:
        await ctx.send(embed=get_doubt_usage(ERROR_TOO_FEW_ARGUMENTS))
        return
    if len(args) > 2:
        await ctx.send(embed=get_doubt_usage(ERROR_TOO_MANY_ARGUMENTS))
        return
    roles = []
    for arg in args:
        r = discord.utils.get(ctx.guild.roles, name=arg)
        if not r:
            await ctx.send(embed=get_doubt_usage(ERROR_ROLE_NOT_FOUND))
            return
        else:
            roles.append(r)
    if has_duplicates(roles):
        await ctx.send(embed=get_doubt_usage(ERROR_DUPLICATE_ROLE))
        return

    # TODO decorator化
    members = [i async for i in ctx.guild.fetch_members(limit=150) if not i.bot]
    attendees = [i for i in members if is_attendee(i)]
    for a in attendees:
        role = [i for i in a.roles if i.name != "@everyone" and i.name != "attendees"][0]
        if not players.get(a):
            players[a] = Player(a.name, role.name)

    if len(args) == 1:
        source = discord.utils.find(lambda m: m.name == ctx.author.name, attendees)
        target = None
        for a in attendees:
            for r in a.roles:
                if args[0] == r.name:
                    target = a
        try:
            add_relation(source, target, DOUBT)
        except:
            print("hogehoge")
        await ctx.send(file=draw_graph())
        return
    else:
        source = None
        target = None
        for a in attendees:
            for r in a.roles:
                if args[1] == r.name:
                    target = a
                if args[0] == r.name:
                    source = a
        try:
            add_relation(source, target, DOUBT)
        except:
            print("hogehoge")
            return
        await ctx.send(file=draw_graph())
        return


bot.run(TOKEN)
# TODO コグでまとめる
# TODO 例外処理をdiscord.pyのビルトインで
# TODO unknown command