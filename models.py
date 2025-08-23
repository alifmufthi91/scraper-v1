from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime

class Book(BaseModel):
    """Data model for a book"""
    title: str
    author: Optional[str] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: Optional[str] = None
    category: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScrapingResult(BaseModel):
    """Model for scraping results"""
    site_name: str
    category: str
    total_books: int
    pages_scraped: int
    books: List[Book]
    scraping_started: datetime
    scraping_completed: datetime
    success: bool = True
    errors: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }