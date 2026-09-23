from fastapi import Header, HTTPException
from app.core.config import settings
ROLES={"viewer":1,"analyst":2,"approver":3,"admin":4}
async def current_role(authorization: str | None = Header(default=None), x_demo_role: str = Header(default="analyst")) -> str:
    if authorization and authorization != f"Bearer {settings.auth_demo_token}": raise HTTPException(401,"Invalid demo token")
    role=x_demo_role.lower()
    if role not in ROLES: raise HTTPException(403,"Unknown role")
    return role
def require(min_role:str):
    async def dep(role:str=__import__('fastapi').Depends(current_role)):
        if ROLES[role] < ROLES[min_role]: raise HTTPException(403,"Insufficient role")
        return role
    return dep
