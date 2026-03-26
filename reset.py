import os
if os.path.exists('bot_database.db'):
    os.remove('bot_database.db')
    print("Database deleted!")
else:
    print("Database not found!")
