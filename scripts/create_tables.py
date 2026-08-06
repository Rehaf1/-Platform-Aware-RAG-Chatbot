from dotenv import load_dotenv
load_dotenv(".env")

from app.db.database import Base, engine
from app.db import models  # noqa: F401 — must import so Base knows about the tables

Base.metadata.create_all(bind=engine)
print("Tables created successfully.")