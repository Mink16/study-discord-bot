import sqlite3

class BotDb:
	def __init__(self):
		self.con = sqlite3.connect('./Database/discord_bot.db')
		self.cur = self.con.cursor()

	def insert_messages(self, user_id, message_id, txt_c_id, vc_c_id):
		self.cur.execute('insert into messages values(?, ?, ?, ?)'
                    , [user_id, message_id, txt_c_id, vc_c_id])
		self.con.commit()

	def get_message_id(self, user_id, vc_c_id):
		self.cur.execute('''
select
	message_id
from messages
where
	user_id = ?
and target_voice_channel_id = ?
		''', [user_id, vc_c_id])
		return self.cur.fetchall()[0][0]