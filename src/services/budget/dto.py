from pydantic import BaseModel


class BudgetDTO(BaseModel):
    budget: float
    usage: float

    class Config:
        from_attributes = True
