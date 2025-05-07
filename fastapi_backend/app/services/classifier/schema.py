from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    text: str

class ClassifyResponse(BaseModel):
    result: str

