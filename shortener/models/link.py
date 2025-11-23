from sqlmodel import SQLModel, Field, Column, String


class Link(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    original_url: str
    short_name: str
    short_url: str = Field(sa_column=Column(String, unique=True, index=True))
    clicks: int = 0
