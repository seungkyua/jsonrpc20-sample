from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastmcp import FastMCP
import uvicorn

# Models
class Product(BaseModel):
    name: str
    price: float
    category: str
    description: str | None = None

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str
    description: str | None = None

# Create FastAPI app
app = FastAPI(title="E-commerce API", version="1.0.0")

# In-memory database
products_db = {
    1: ProductResponse(id=1, name="Laptop", price=999.99, category="Electronics"),
    2: ProductResponse(id=2, name="Mouse", price=29.99, category="Electronics"),
    3: ProductResponse(id=3, name="Desk Chair", price=299.99, category="Furniture"),
}
next_id = 4

@app.get("/products", response_model=list[ProductResponse])
def list_products(category: str | None = None, max_price: float | None = None) -> list[ProductResponse]:
    """List all products with optional filtering."""
    products = list(products_db.values())
    if category:
        products = [p for p in products if p.category == category]
    if max_price:
        products = [p for p in products if p.price <= max_price]
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Get a specific product by ID."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.post("/products", response_model=ProductResponse)
def create_product(product: Product):
    """Create a new product."""
    global next_id
    product_response = ProductResponse(id=next_id, **product.model_dump())
    products_db[next_id] = product_response
    next_id += 1
    return product_response

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: Product):
    """Update an existing product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    products_db[product_id] = ProductResponse(id=product_id, **product.model_dump())
    return products_db[product_id]

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    """Delete a product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted"}

# Convert to MCP server
mcp = FastMCP.from_fastapi(app=app)

# # Add a new tool
# @mcp.tool
# def get_product(product_id: int) -> ProductResponse:
#     """Get a product by ID."""
#     return products_db[product_id]

# Get HTTP app for Streamable HTTP transport
http_app = mcp.http_app()

if __name__ == "__main__":
    uvicorn.run(http_app, host="127.0.0.1", port=8000, log_level="info")
