import discord
from discord.ui import Select, View, Button
from discord.ext import commands, tasks
from discord import Option, SlashCommandGroup
import aiohttp
from lib.yamlutil import yaml
import lib.picture as getPicture
from typing import List
import lib.sql as SQL
import cogs.uidlist as uidlist
import os
from lib.getCharacterStatus import CharacterStatus
from enums.substatus import SubTypes
from lib.gen_genshin_image import get_character_discord_file
from lib.log_output import log_output, log_output_interaction
from enums.ImageTypeEnums import ImageTypeEnums
import view.genshin_view as genshin_view

charactersYaml = yaml(path='characters.yaml')
characters = charactersYaml.load_yaml()
genshinJpYaml = yaml(path='genshinJp.yaml')
genshinJp = genshinJpYaml.load_yaml()


class GenshinUID():
    def __init__(self, uid: str) -> None:
        self.uid = uid
        self.data = None
        self.character_list = []
        self.score_type: SubTypes = SubTypes.ATTACK_PERCENT.value
        self.image_type: ImageTypeEnums = ImageTypeEnums.DEFAULT.value
        self.file = None
        self.discord_file = None
        self.button_data = None
        self.character_name = None

    def set_button_data(self, data, label):
        self.button_data = data
        self.character_name = label
        return self

    async def get_data(self):
        url = f"https://enka.network/api/uid/{self.uid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                resp = await response.json()
        return resp

    def get_character_list(self):
        character_list = []
        for id in self.data["playerInfo"]["showAvatarInfoList"]:
            character_list.append(id["avatarId"])
        return character_list

    async def get_profile_discord_file(self):
        self.file = await getPicture.getProfile(self.uid, self.data)
        self.discord_file = discord.File(self.file, f"{self.uid}.png")
        return self.discord_file

    def del_filepass(self):
        del self.discord_file
        os.remove(self.file)

    def get_profile_embed(self):
        try:
            embed = discord.Embed(
                title=f"{self.data['playerInfo']['nickname']}",
                color=0x1e90ff,
                description=f"uid: {self.uid}",
                url=f"https://enka.network/api/uid/{self.uid}"
            )
            embed.set_image(url=f"attachment://{self.uid}.png")
            return embed
        except:
            embed = discord.Embed(
                title=f"エラーが発生しました。APIを確認してからもう一度お試しください。\n{f'https://enka.network/api/uid/{self.uid}'}",
                color=0x1e90ff,
                url=f"https://enka.network/api/uid/{self.uid}"
            )
            return embed

    def get_status_image_view(self):
        view = View(timeout=300, disable_on_timeout=True)
        view.add_item(genshin_view.ScoreTypeSelecter(self))
        view.add_item(genshin_view.ImageTypeSelecter(self))
        view = self.get_character_button(view=view)
        return view

    def get_character_button(self, view):
        names = []
        button_data = {}
        for id in self.character_list:
            id = str(id)
            name = genshinJp[characters[str(id)]["NameId"]]
            names.append(name)
            button_data.update({name: id})
        # 名前をラベル、ついでにdictとuidも送り付ける
        for v in names:
            view.add_item(
                genshin_view.CharacterSelectButton(v, button_data, self))
        return view

    async def get_status_image(self, interaction: discord.Interaction, button_data, label):
        await interaction.response.edit_message(content="```読み込み中...（10秒ほどかかります）```", embed=None, view=None)
        log_output_interaction(interaction=interaction,
                               cmd=f"genshinstat get キャラ取得 {self.uid} {button_data[label]}")
        try:
            # キャラクターのデータを取得します。
            json = await CharacterStatus.get_json(uid=self.uid)
            character_status = CharacterStatus.getCharacterStatus(
                json=json, id=button_data[label], build_type=self.score_type)

            # 画像データを取得し、DiscordのFileオブジェクトとしてurlとfileを取得します。
            file, url = get_character_discord_file(
                character_status=character_status, build_type=self.score_type
            )
        except ArithmeticError as e:
            # 失敗したときの処理かく
            # 例外によって種類わける
            pass

        # 取得した画像でembed作成しれすぽんす
        embed = discord.Embed(
            title=f"{label}",
            color=0x1e90ff,
        )

        embed.set_image(url=url)

        return embed, file


# class GenshinProfile():
