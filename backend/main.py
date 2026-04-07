from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="IDX OpenInsider API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to IDX OpenInsider API"}

@app.get("/insider/latest")
def get_latest_insiders():
    # Placeholder for the latest insider activity
    return []

@app.get("/insider/top-buy")
def get_top_buys():
    # Placeholder for top buys
    return []

@app.get("/insider/top-sell")
def get_top_sells():
    # Placeholder for top sells
    return []

@app.get("/insider/by-ticker/{ticker}")
def get_insider_by_ticker(ticker: str):
    # Placeholder for activity by ticker
    return {"ticker": ticker, "activity": []}
