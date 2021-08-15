# -*- coding: utf-8 -*-
import os

import discord
import requests
from discord import CategoryChannel, Guild
from discord.channel import VoiceChannel
from discord.ext import commands
from discord.member import Member, VoiceState
from dotenv import load_dotenv

load_dotenv()
BASE_URL = 'https://discord.com/api'
API_TOKEN = os.getenv('API_TOKEN')
TARGET_V_CHANNEL_ID = os.getenv('TARGET_V_CHANNEL_ID')
INVITE_CHANNEL_ID = os.getenv('INVITE_CHANNEL_ID')
INVITE_ROLE = os.getenv('INVITE_ROLE')
RECOG_STR = os.getenv('RECOG_STR')

headers = {
	'Authorization': 'Bot ' + API_TOKEN
}
client: commands.Bot = commands.Bot(command_prefix=os.getenv('PREFIX'), intents=discord.Intents.all())

@client.event
async def on_ready():
	print(f'起動：{client.user}')

@client.event
async def on_voice_state_update(user: Member, old: VoiceState, new: VoiceState):
	if old.channel is not None:
		old_channel: VoiceChannel = old.channel
		# 対象ボイスチャンネルの人数が0人になったら招待メッセージとカテゴリごと消す
		if old_channel.name.startswith(RECOG_STR) and len(old_channel.members) == 0:
			channel_category: CategoryChannel = old_channel.category
			[await t.delete() for t in channel_category.text_channels]
			[await v.delete() for v in channel_category.voice_channels]
			await channel_category.delete()

	if new.channel is not None:
		new_v_channel: VoiceChannel = new.channel
		# 対象ボイスチャンネルに入室したらテキスト、ボイスチャンネルを作成して
		# メンバーを移動後、招待メッセージを送信
		if new_v_channel.id == int(TARGET_V_CHANNEL_ID):
			guild: Guild = new_v_channel.guild
			categories_num: int = [
				int(c.name[3:]) for c in guild.categories if c.name.startswith(RECOG_STR)]
			next_categorie = 1
			if len(categories_num) > 0:
				next_categorie = max(categories_num) + 1
			next_categorie_name = RECOG_STR + str(next_categorie)

			category: CategoryChannel = await Guild.create_category(guild, next_categorie_name, reason=f'{user.display_name}が{TARGET_V_CHANNEL_ID}に入室({str(user.id)})')
			await category.create_text_channel(next_categorie_name + '_聞き専')
			buntai_channel: VoiceChannel = await category.create_voice_channel(next_categorie_name + '_通話')
			[await m.move_to(buntai_channel) for m in new_v_channel.members]

			# 募集をかける
			invite: discord.Invite = await buntai_channel.create_invite()
			requests.post(f'{BASE_URL}/channels/{INVITE_CHANNEL_ID}/messages', json={'content': INVITE_ROLE + '\n' + invite.url}, headers=headers)

client.run(API_TOKEN)
