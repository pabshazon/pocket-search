
class ComputeRequest(BaseModel):
    operation: str
    a: int
    b: int
    input_vector: list[float]
