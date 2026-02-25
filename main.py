from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, Product
import ai_agent
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- EXISTING ROUTES (Missing in your logs) ---

@app.get("/inventory")
def read_root(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.post("/add-item")
def add_item(name: str, qty: int, price: float, db: Session = Depends(get_db)):
    item = Product(name=name, quantity=qty, price=price)
    db.add(item)
    db.commit()
    return {"message": "Success"}

@app.get("/ask-ai")
def ask_ai(question: str, db: Session = Depends(get_db)):
    ai_response_text = ai_agent.get_ai_advice(db, question)
    return {"answer": ai_response_text}

# --- NEW FEATURES ---

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