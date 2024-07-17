import sqlite3

conn = sqlite3.connect('./-images.db')
cursor = conn.cursor()

cursor.execute('''
ALTER TABLE images
ADD COLUMN origianl_alt TEXT;
''')

conn.commit()
conn.close()
