import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from math import ceil



app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static_dish", StaticFiles(directory="static_dish"), name="static_dish")

templates = Jinja2Templates(directory="ProjectMenu/frontend/templates")

DB_NAME = "menuproject3.db"

def get_conection():
        conection =  sqlite3.connect(DB_NAME)
        conection.row_factory = sqlite3.Row
        return conection

conection = get_conection()
cursor = conection.cursor()

@app.get("/company/{company_id}", response_class=HTMLResponse)
async def company(request: Request, company_id: int):

        cursor = conection.cursor()
        

        cursor.execute(f"SELECT * FROM company WHERE id = {company_id}",)
        row = cursor.fetchone()

        cursor.close()
        
       
        return templates.TemplateResponse(
                "company.html",
                {
                        "request": request,
                        "name": row["name"],
                        "id": row["id"],
                        "description": row["description"],
                        "summary": row["summary"]
                        
                }
        )
       

@app.get("/category")
async def categories():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM category")
        rows= cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]


@app.get("/dish/{dish_id}", response_class=HTMLResponse)
async def dish(request:Request, dish_id):
        cursor = conection.cursor()


        cursor.execute(f"SELECT * FROM dish where id = {dish_id}")
        row= cursor.fetchone()
        
        cursor.close()

        id = row ['id']
        name = row ['name']
        price = row ['price']
        descript = row ["descript"]
        category_id = row ['category_id']
        rating = row ['rating']
        image_url = row ['image_url']

        return templates.TemplateResponse(
                request=request, name="dish.html", context={"id": id, "name": name, "price": price, "descript": descript, "category_id":category_id, "rating": rating, "image_url": image_url}     
        )

     
      

@app.get("/dish_category")
async def dish_category():
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

@app.get("/companies", response_class=HTMLResponse)
async def companies(request: Request, page: int = 1):
        
        items_per_page = 12
        offset = (page - 1) * items_per_page

        
        cursor = conection.cursor()
        
        query = """
                SELECT company.*, rating.stars
                FROM company
                LEFT JOIN rating ON rating.company_id = company.id
                ORDER BY company.id
                LIMIT ? OFFSET ?
                
                 """
        cursor.execute(query, (items_per_page, offset))
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT (*) FROM company")
        total_items = cursor.fetchone()[0]
        total_pages = ceil(total_items / items_per_page)
        
        cursor.close()

        return templates.TemplateResponse(
                 "companies.html", {"request": request, "companies": rows, "current_page": page, "total_pages": total_pages }
               
       )


@app.get("/dishes", response_class=HTMLResponse)
async def dishes(request:Request, page: int = 1):
        
        items_per_page = 12
        offset = (page - 1) * items_per_page
        
        cursor = conection.cursor()
        cursor.execute("SELECT * FROM dish ORDER BY id LIMIT ? OFFSET ?", (items_per_page, offset))
        rows = cursor.fetchall()

        cursor.execute("SELECT  COUNT(*) FROM dish")
        total_items = cursor.fetchone()[0]
        total_pages = ceil(total_items / items_per_page)


        cursor.close()
        
        return templates.TemplateResponse(
                "dishes.html", {"request": request, "dishes": rows, "current_page": page, "total_pages": total_pages}
        )
        
        
