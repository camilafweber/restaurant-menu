from http import cookies
import json
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Response
from fastapi.staticfiles import StaticFiles
from math import ceil


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static_dish", StaticFiles(directory="static_dish"), name="static_dish")



DB_NAME = "menuproject3.db"
COMPANY_CATEGORY_DEFINITIONS = [
        {"slug": "cafes", "label": "Cafes"},
        {"slug": "bakeries", "label": "Bakeries"},
        {"slug": "bars", "label": "Bars"},
        {"slug": "fast-food", "label": "Fast Food"},
        {"slug": "gourmet", "label": "Gourmet"},
]
COMPANY_CATEGORY_SEEDS = {
        "cafes": [7, 13, 38],
        "bakeries": [16, 17, 32, 39, 46],
        "bars": [27, 35, 48, 50],
        "fast-food": [2, 14, 18, 21, 29, 42],
        "gourmet": [1, 9, 22],
}

def get_conection():
        conection =  sqlite3.connect(DB_NAME)
        conection.row_factory = sqlite3.Row
        return conection

def ensure_company_category_schema():
        conection = get_conection()
        cursor = conection.cursor()

        cursor.execute("PRAGMA table_info(company)")
        company_columns = {row["name"] for row in cursor.fetchall()}

        if "category_id" not in company_columns:
                cursor.execute("ALTER TABLE company ADD COLUMN category_id INTEGER")

        category_ids = {}
        for option in COMPANY_CATEGORY_DEFINITIONS:
                cursor.execute("SELECT id FROM category WHERE name = ?", (option["label"],))
                row = cursor.fetchone()

                if row is None:
                        cursor.execute("INSERT INTO category (name) VALUES (?)", (option["label"],))
                        category_ids[option["slug"]] = cursor.lastrowid
                else:
                        category_ids[option["slug"]] = row["id"]

        for slug, company_ids in COMPANY_CATEGORY_SEEDS.items():
                category_id = category_ids[slug]
                for company_id in company_ids:
                        cursor.execute(
                                "UPDATE company SET category_id = ? WHERE id = ? AND category_id IS NULL",
                                (category_id, company_id),
                        )

        conection.commit()
        cursor.close()
        conection.close()

def get_company_category_options():
        cursor = conection.cursor()
        options = []

        for option in COMPANY_CATEGORY_DEFINITIONS:
                cursor.execute("SELECT id, name FROM category WHERE name = ?", (option["label"],))
                row = cursor.fetchone()
                if row:
                        options.append({"id": row["id"], "label": row["name"]})

        cursor.close()
        return options

def get_cart():
        raw_cart = cookies.get("cart", "{}")

        try:
                parsed_cart = json.loads(raw_cart)
        except json.JSONDecodeError:
                return {}

        if not isinstance(parsed_cart, dict):
                return {}

        clean_cart = {}
        for dish_id, quantity in parsed_cart.items():
                try:
                        normalized_dish_id = int(dish_id)
                        normalized_quantity = int(quantity)
                except (TypeError, ValueError):
                        continue

                if normalized_quantity > 0:
                        clean_cart[str(normalized_dish_id)] = normalized_quantity

        return clean_cart

def get_cart_count():
        return sum(get_cart().values())

def build_cart_response(redirect_to: str, cart: dict[str, int]):
        response = Response(url=redirect_to, status_code=303)
        response.set_cookie(
                "cart",
                json.dumps(cart),
                max_age=60 * 60 * 24 * 30,
                samesite="lax",
        )
        return response

def dish_exists(dish_id: int):
        cursor = conection.cursor()
        cursor.execute("SELECT id FROM dish WHERE id = ?", (dish_id,))
        row = cursor.fetchone()
        cursor.close()
        return row is not None

ensure_company_category_schema()
conection = get_conection()
cursor = conection.cursor()

@app.get("/company/{company_id}")
async def company(company_id: int, search: str | None = None):

        cursor = conection.cursor()
        search_term = (search or "").strip().lower()

        cursor.execute("SELECT * FROM company WHERE id = ?", (company_id,))
        row = cursor.fetchone()

        if row is None:
                cursor.close()
                return Response(url="/companies", status_code=303)

        dish_query = """
                SELECT id, name, price, descript, rating, image_url
                FROM dish
                WHERE company_id = ?
        """
        dish_params = [company_id]

        if search_term:
                dish_query += """
                        AND (
                                LOWER(name) LIKE ?
                                OR LOWER(COALESCE(descript, '')) LIKE ?
                        )
                """
                like_term = f"%{search_term}%"
                dish_params.extend([like_term, like_term])

        dish_query += " ORDER BY id"
        cursor.execute(dish_query, dish_params)
        dishes = cursor.fetchall()

        cursor.close()
        
       
        if not row:
                return {"error": "Company not found"}, 404      
        
        return {
                "company": dict(row),
                "dishes": [dict(d) for d in dishes],
                "selected_search": search or ""
        }

@app.get("/category")
async def categories():
        cursor = conection.cursor()


        cursor.execute("SELECT * FROM category")
        rows= cursor.fetchall()
        
        cursor.close()

        return [dict(row) for row in rows]


@app.get("/dish/{dish_id}")
async def dish(dish_id):
        cursor = conection.cursor()


        cursor.execute(f"SELECT * FROM dish where id = {dish_id}")
        row= cursor.fetchone()
        
        cursor.close()

        if not row:
                return {"error": "Dish not found"}, 404
        
        return dict(row)
     
      

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

@app.get("/cart")
async def cart():
        cart = get_cart()
        cart_count = sum(cart.values())
        items = []
        total_price = 0.0

        if cart:
                cursor = conection.cursor()
                placeholders = ",".join("?" for _ in cart)
                cursor.execute(
                        f"SELECT id, name, price, image_url FROM dish WHERE id IN ({placeholders})",
                        tuple(int(dish_id) for dish_id in cart.keys()),
                )
                dishes_by_id = {str(row["id"]): row for row in cursor.fetchall()}
                cursor.close()

                for dish_id, quantity in cart.items():
                        dish_row = dishes_by_id.get(dish_id)
                        if not dish_row:
                                continue

                        subtotal = float(dish_row["price"]) * quantity
                        total_price += subtotal
                        items.append(
                                {
                                        "id": dish_row["id"],
                                        "name": dish_row["name"],
                                        "price": dish_row["price"],
                                        "image_url": dish_row["image_url"],
                                        "quantity": quantity,
                                        "subtotal": subtotal,
                                }
                        )

        return {
                        "items": items,
                        "cart_count": cart_count,
                        "total_price": total_price,
                },
    

@app.get("/cart/add")
async def add_to_cart(dish_id: int, next: str = "/dishes"):
        if not dish_exists(dish_id):
                return Response(url=next, status_code=303)

        cart = get_cart()
        cart_key = str(dish_id)
        cart[cart_key] = cart.get(cart_key, 0) + 1
        return build_cart_response(next, cart)

@app.get("/cart/increase")
async def increase_cart_item(dish_id: int, next: str = "/cart"):
        if not dish_exists(dish_id):
                return Response(url=next, status_code=303)

        cart = get_cart()
        cart_key = str(dish_id)
        cart[cart_key] = cart.get(cart_key, 0) + 1
        return build_cart_response(next, cart)

@app.get("/cart/decrease")
async def decrease_cart_item(dish_id: int, next: str = "/cart"):
        cart = get_cart()
        cart_key = str(dish_id)

        if cart_key in cart:
                if cart[cart_key] > 1:
                        cart[cart_key] -= 1
                else:
                        cart.pop(cart_key, None)

        return build_cart_response(next, cart)

@app.get("/cart/remove")
async def remove_from_cart(dish_id: int, next: str = "/cart"):
        cart = get_cart()
        cart.pop(str(dish_id), None)
        return build_cart_response(next, cart)

@app.get("/companies")
async def companies(page: int = 1, category_id: int | None = None, search: str | None = None):
        
        items_per_page = 12
        offset = (page - 1) * items_per_page
        category_options = get_company_category_options()
        valid_category_ids = {option["id"] for option in category_options}
        selected_category_id = category_id if category_id in valid_category_ids else None
        search_term = (search or "").strip()

        cursor = conection.cursor()
        base_query = """
                SELECT company.*, rating.stars
                FROM company
                LEFT JOIN rating ON rating.company_id = company.id
                 """
        count_query = "SELECT COUNT(*) FROM company"
        query_params = []
        count_params = []
        where_clauses = []

        if selected_category_id is not None:
                where_clauses.append("company.category_id = ?")
                query_params.append(selected_category_id)
                count_params.append(selected_category_id)

        if search_term:
                where_clauses.append(
                        """
                        (
                                LOWER(company.name) LIKE ?
                                OR LOWER(COALESCE(company.summary, '')) LIKE ?
                                OR LOWER(COALESCE(company.description, '')) LIKE ?
                                OR EXISTS (
                                        SELECT 1
                                        FROM dish
                                        WHERE dish.company_id = company.id
                                        AND LOWER(dish.name) LIKE ?
                                )
                        )
                        """
                )
                like_term = f"%{search_term.lower()}%"
                query_params.extend([like_term, like_term, like_term, like_term])
                count_params.extend([like_term, like_term, like_term, like_term])

        if where_clauses:
                where_sql = " WHERE " + " AND ".join(where_clauses)
                base_query += where_sql
                count_query += where_sql

        query = base_query + " ORDER BY company.id LIMIT ? OFFSET ?"
        cursor.execute(query, (*query_params, items_per_page, offset))
        rows = cursor.fetchall()

        
        cursor.execute(count_query, count_params)
        total_items = cursor.fetchone()[0]
        total_pages = ceil(total_items / items_per_page)

        companies_list =[dict(row) for row in rows]
        
        cursor.close()

        return {
                "companies": [dict(row) for row in rows],
                "total_pages": total_pages,
                "current_page": page,
        }


@app.get("/dishes")
async def dishes(page: int = 1, search: str | None = None):
        
        items_per_page = 12
        offset = (page - 1) * items_per_page
        search_term = (search or "").strip().lower()
        
        cursor = conection.cursor()
        base_query = """
                SELECT dish.*
                FROM dish
                LEFT JOIN company ON company.id = dish.company_id
        """
        count_query = "SELECT COUNT(*) FROM dish LEFT JOIN company ON company.id = dish.company_id"
        query_params = []
        count_params = []

        if search_term:
                where_sql = """
                        WHERE LOWER(dish.name) LIKE ?
                        OR LOWER(COALESCE(dish.descript, '')) LIKE ?
                        OR LOWER(COALESCE(company.name, '')) LIKE ?
                """
                like_term = f"%{search_term}%"
                base_query += where_sql
                count_query += where_sql
                query_params.extend([like_term, like_term, like_term])
                count_params.extend([like_term, like_term, like_term])

        query = base_query + " ORDER BY dish.id LIMIT ? OFFSET ?"
        cursor.execute(query, (*query_params, items_per_page, offset))
        rows = cursor.fetchall()

        cursor.execute(count_query, count_params)
        total_items = cursor.fetchone()[0]
        total_pages = max(1, ceil(total_items / items_per_page)) if total_items else 1

        dishes_list = [dict(row) for row in rows]

        cursor.close()
        
        return {
                        "dishes": [dict(row) for row in rows],
                        "current_page": page,
                        "total_pages": total_pages,
                        "selected_search": search or "",
                        "dishes_list": dishes_list,
                }
        
        
        
