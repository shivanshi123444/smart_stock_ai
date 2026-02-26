from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel  # Added for JSON validation
from database import get_db, Product, engine, Base
import ai_agent
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = FastAPI()

# Pydantic model to match the JSON sent by your index.html
class ProductCreate(BaseModel):
    name: str
    qty: int
    price: float

@app.on_event("startup")
def on_startup():
    try:
        # This creates the tables in Render's PostgreSQL if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

# FIXED CORS: Using "*" and allowing credentials to fix the "Blocked by CORS" error
# Change allow_origins to specifically name your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://smart-stock-ai-1.onrender.com"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/inventory")
def read_root(db: Session = Depends(get_db)):
    return db.query(Product).all()

# FIXED: Now accepts JSON body instead of URL parameters
@app.post("/add-item")
def add_item(item: ProductCreate, db: Session = Depends(get_db)):
    # Check if item already exists to update instead of duplicate
    db_item = db.query(Product).filter(Product.name == item.name).first()
    if db_item:
        db_item.quantity += item.qty
        db_item.price = item.price
    else:
        new_item = Product(name=item.name, quantity=item.qty, price=item.price)
        db.add(new_item)
    
    db.commit()
    return {"message": "Success"}

@app.get("/ask-ai")
def ask_ai(question: str, db: Session = Depends(get_db)):
    ai_response_text = ai_agent.get_ai_advice(db, question)
    return {"answer": ai_response_text}

@app.delete("/delete-item/{name}")
def delete_item(name: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.name == name).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": f"Deleted {name}"}

@app.get("/export-pdf")
def export_pdf(db: Session = Depends(get_db)):
    items = db.query(Product).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Smart-Stock Inventory Report", styles['Title']))
    
    data = [["Product", "Quantity", "Price (INR)"]]
    for item in items:
        data.append([item.name, item.quantity, f"Rs.{item.price}"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Inventory_Report.pdf"}
    )
