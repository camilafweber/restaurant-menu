import sqlite3
from fastapi import FastAPI
import uvicorn

app = FastAPI()

DB_NAME = "menuproject.db"

def get_conection():
    conection =  sqlite3.connect(DB_NAME)
    conection.row_factory = sqlite3.Row
    return conection

conection = get_conection()
#cursor = conection.cursor()

@app.get("/company")
async def companies():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM company")
        rows = cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]


@app.get("/category")
async def categories():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM category")
        rows = cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]


@app.get("/dish")
async def dish():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM dish")
        rows = cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]


@app.get("/dish_category")
async def dishes():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM dish_category")
        rows = cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]

@app.get("/rating")
async def rating():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM rating")
        rows = cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]

