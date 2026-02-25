import sqlite3
DB_NAME = "menuproject.db"

def get_conection():
    return sqlite3.connect(DB_NAME)

conection = get_conection()
cursor = conection.cursor()

conection = sqlite3.connect('menuproject.db')

conection.row_factory = sqlite3.Row

cursor = conection.cursor()


cursor.execute("SELECT * FROM ")
rows = cursor.fetchall()

lista_dict = [dict(row) for row in rows]

for user in lista_dict:
    print(user)

conection.close()
