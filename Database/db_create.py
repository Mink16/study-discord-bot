import sqlite3

con = sqlite3.connect('./Database/discord_bot.db')
cursor = con.cursor()
cursor.executescript("""
DROP TABLE IF EXISTS messages;
CREATE TABLE messages(
  user_id INTEGER
  ,message_id INTEGER
  ,send_text_channel_id INTEGER
  ,target_voice_channel_id INTEGER
)
""")

con.commit()