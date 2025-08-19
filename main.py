from fastapi import FastAPI
from router import expenses,categories,users, roles,funds

app = FastAPI()
# Include routes
app.include_router(expenses.router)
app.include_router(categories.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(funds.router)



