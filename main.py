# -*- coding: utf-8 -*-
import os

import discord
import requests
from discord import CategoryChannel, Guild, RawReactionActionEvent
from discord.channel import VoiceChannel
from discord.ext import commands
from discord.member import Member, VoiceState
from dotenv import load_dotenv

from Database.bot_db import BotDb

load_dotenv()
BASE_URL = 'https://discord.com/api'
API_TOKEN = os.getenv('API_TOKEN')
TARGET_V_CHANNEL_ID = os.getenv('TARGET_V_CHANNEL_ID')
INVITE_CHANNEL_ID = os.getenv('INVITE_CHANNEL_ID')
INVITE_ROLE_ID = os.getenv('INVITE_ROLE_ID')
ADD_ROLE_CHANNEL_ID = os.getenv('ADD_ROLE_CHANNEL_ID')
ADD_ROlE_EMOJI = os.getenv('ADD_ROlE_EMOJI')
RECOG_STR = os.getenv('RECOG_STR')

headers = {
	'Authorization': 'Bot ' + API_TOKEN
}
client: commands.Bot = commands.Bot(command_prefix=os.getenv('PREFIX'), intents=discord.Intents.all())
bot_db = BotDb()

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

			msg_id = bot_db.get_message_id(client.user.id, old_channel.id)
			requests.delete(f'{BASE_URL}/channels/{INVITE_CHANNEL_ID}/messages/{msg_id}', headers=headers)

	if new.channel is not None:
		new_v_channel: VoiceChannel = new.channel
		# 対象ボイスチャンネルに入室したらテキスト、ボイスチャンネルを作成して
		# メンバーを移動後、招待メッセージを送信
		if new_v_channel.id == int(TARGET_V_CHANNEL_ID):
			guild: Guild = new_v_channel.guild
			categories_num: int = [int(c.name[len(RECOG_STR):]) for c in guild.categories if c.name.startswith(RECOG_STR)]
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
			r = requests.post(f'{BASE_URL}/channels/{INVITE_CHANNEL_ID}/messages', json={'content': '<@&' + INVITE_ROLE_ID + '>\n' + invite.url}, headers=headers)

			bot_db.insert_messages(client.user.id, int(r.json()['id']), int(INVITE_CHANNEL_ID), buntai_channel.id)

# リアクション追加時
@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
	if payload.emoji.name != ADD_ROlE_EMOJI \
		or payload.channel_id != int(ADD_ROLE_CHANNEL_ID): 
		return
	await change_role(payload, True)

# リアクション削除時
@client.event
async def on_raw_reaction_remove(payload: RawReactionActionEvent):
	if payload.emoji.name != ADD_ROlE_EMOJI \
		or payload.channel_id != int(ADD_ROLE_CHANNEL_ID): 
		return
	await change_role(payload, False)

async def change_role(payload: RawReactionActionEvent, role_flg: bool):
	guild: Guild = client.get_guild(payload.guild_id)
	member: Member = guild.get_member(payload.user_id)

	# 役職を編集
	role = guild.get_role(int(INVITE_ROLE_ID))
	await member.add_roles(role) if role_flg else await member.remove_roles(role)

client.run(API_TOKEN)
