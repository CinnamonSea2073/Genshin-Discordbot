import discord
from discord.ui import Select,View
from discord.ext import commands
from discord.commands import SlashCommandGroup
import datetime
from lib.yamlutil import yaml

l: list[discord.SelectOption] = []

class helpselectView(View):
    @discord.ui.select(
            placeholder="表示するヘルプコマンドを指定してね",
            options=[
                discord.SelectOption(
                    label="メインコマンド",
                    emoji="📰",
                    description="原神ステータスを確認できます。",
                    ),
                discord.SelectOption(
                    label="UIDリストコマンド",
                    emoji="📚",
                    description="忘れがちなUIDを保存してくれるコマンドです。"),
                discord.SelectOption(
                    label="祈願コマンド",
                    emoji="✨",
                    description="いわゆるガチャシミュレーターです。"),
        ])
    async def select_callback(self, select:discord.ui.Select, interaction):
        embed = discord.Embed(title=f"helpコマンド：{select.values[0]}",color=0x1e90ff)
        if select.values[0] == "メインコマンド":
            print("help - メインコマンド")
            embed.add_field(
                name=f"このbotのメインとなるコマンドです。",
                value=f"\
                    \n**・/genshinstat get**\n自分以外が見ることができない状態で原神のステータスを取得します。UIDリスト機能で、自分のUIDを登録しておくと簡単に使えます。原神の設定でキャラ詳細を公開にすると、キャラステータスも確認できます。\
                ")
        elif select.values[0] == "UIDリストコマンド":
            print("help - UIDリストコマンド")
            embed.add_field(
                name=f"いちいち確認するのが面倒なUIDを管理するコマンドです。",
                value=f"\
                    \n**・/uidlist get**\n登録され、公開設定が「公開」になっているUIDがここに表示されます。\
                    \n**・/uidlist control**\n登録したUIDを管理するパネルを表示します。UIDの登録や削除、公開設定の切り替えもここからできます。\
                ")
        elif select.values[0] == "祈願コマンド":
            print("help - 祈願コマンド")
            embed.add_field(
                name=f"いわゆるガチャシミュレーターです。天井もユーザーごとにカウントされています。",
                value=f"\
                    \n**・/wish character**\n原神のガチャ排出時に表示されるイラストを検索します。\
                    \n**・/wish get**\n原神のガチャを10連分引きます。演出をするかしないか設定できます。\
                    \n**・/wish get_n**\n原神のガチャを指定回数分（最大200回）連続で引きます。結果はまとめて表示します。\
                    "
                )
        await interaction.response.edit_message(content=None,embed=embed,view=self)

class DayOfWeekUnexploredRegion:

    EMBEDS = {}
    SELECT_OPTIONS = []
    FILES = {}

    def add_data(key, day_of_week, url):
        # embedの追加
        embed = discord.Embed(
            title=f"{day_of_week}の日替わり秘境はこちら", color=0x1e90ff)
        embed.set_image(url=url)
        DayOfWeekUnexploredRegion.EMBEDS[key] = embed
        # optionsの追加
        DayOfWeekUnexploredRegion.SELECT_OPTIONS.append(
            discord.SelectOption(label=day_of_week, value=key))


y = yaml("weekday.yaml")
_DATA: dict = y.load_yaml()

for k, v in _DATA.items():
    DayOfWeekUnexploredRegion.add_data(
        key=k, day_of_week=v["day_of_week"], url=v["url"])


class weekselectView(View):
    def __init__(self):
        self.weekday = str(datetime.date.today().weekday())
        super().__init__()

    @discord.ui.button(label="今日の秘境に戻る")
    async def today(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.weekday = str(datetime.date.today().weekday())
        await interaction.response.edit_message(embed=DayOfWeekUnexploredRegion.EMBEDS[self.weekday], view=self)

    @discord.ui.button(label="次の日の秘境")
    async def nextday(self, _: discord.ui.Button, interaction: discord.Interaction):
        self.weekday = str((int(self.weekday) + 1) % 7)
        await interaction.response.edit_message(embed=DayOfWeekUnexploredRegion.EMBEDS[self.weekday], view=self)

    @discord.ui.select(
        placeholder="確認したい曜日を選択",
        options=DayOfWeekUnexploredRegion.SELECT_OPTIONS
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        value = select.values[0]
        view = self
        print(
            f"実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}\n日替わり - {select.values[0]}")
        await interaction.response.edit_message(embed=DayOfWeekUnexploredRegion.EMBEDS[value], view=view)


class GenbotCog(commands.Cog):

    def __init__(self, bot):
        print('genbot_initしたよ')
        self.bot = bot

    genbot = SlashCommandGroup('genbot', 'test')

    @genbot.command(name='help', description='原神ステータスbotに困ったらまずはこれ！')
    async def chelp(self, ctx):
        embed = discord.Embed(title=f"helpコマンド：メインコマンド", color=0x1e90ff)
        embed.add_field(
            name=f"このbotのメインとなるコマンドです。",
            value=f"\
                \n**・/genshinstat get**\n自分以外が見ることができない状態で原神のステータスを取得します。UIDリスト機能で、自分のUIDを登録しておくと簡単に使えます。原神の設定でキャラ詳細を公開にすると、キャラステータスも確認できます。\
        ")
        view = helpselectView(timeout=None)
        # レスポンスで定義したボタンを返す
        await ctx.respond("確認したいコマンドのジャンルを選択してね", embed=embed, view=view, ephemeral=True)

    @genbot.command(name='today', description='今日の日替わり秘境などをまとめて確認！')
    async def today(self, ctx):

        view = weekselectView()
        weekday = view.weekday
        await ctx.respond(embed=DayOfWeekUnexploredRegion.EMBEDS[weekday], view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(GenbotCog(bot))