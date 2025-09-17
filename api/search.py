# routers/search.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from db.session import get_db
from models import Movie, MovieFTS

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def search_movies(query: str, db: Session = Depends(get_db)):
    """
    Search movies using SQLite FTS5.
    """
    # The `MATCH` operator is used for FTS5 queries.
    # We are searching for movies where the title, genre, OR tags match the query.
    # FTS5 can search across all columns of the virtual table at once.
    # Note: SQLite's MATCH operator is very powerful and handles boolean logic.
    # The `?` syntax is for SQLAlchemy's parameterized queries.

    # This is a bit of a trick to use the virtual table effectively.
    # We first search the FTS table for matching rowids, then use that to filter the main table.
    
    # FTS5 query syntax: "term1 AND term2 OR term3"
    # We'll use a simple "OR" search for now.
    fts_query = " OR ".join(query.split())

    # Get the rowids of matching movies from the FTS table
    fts_results = db.query(MovieFTS.rowid).filter(
        text("MovieFTS MATCH :query")
    ).params(query=fts_query).all()
    
    # Extract the list of rowids
    matching_ids = [r[0] for r in fts_results]

    if not matching_ids:
        return {
            "success": True,
            "results": []
        }

    # Now, use the matching IDs to get the full movie details from the main table
    results = db.query(Movie).filter(Movie.id.in_(matching_ids)).all()

    return {
        "success": True,
        "results": [
            {
                "id": m.id,
                "title": m.title,
                "genre": m.genre,
                "description": m.description,
                "cover": m.cover,
                "tags": m.tags.split(",") if m.tags else []
            } for m in results
        ]
    }