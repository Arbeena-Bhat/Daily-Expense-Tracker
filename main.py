from fastapi import FastAPI
from router import expenses,categories

app = FastAPI()
# Include routes
app.include_router(expenses.router)
app.include_router(categories.router)





