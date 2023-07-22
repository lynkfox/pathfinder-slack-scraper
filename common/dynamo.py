
def build_pk(
    week: int,
) -> str:
    """
    builds the PK
    """
    return f"WEEK#{week}"
    




def build_sk(name: str, signature:str, date:str) -> str:
    """
    Builds the SK
    """
    return f"{name}#{signature}#{date}"

