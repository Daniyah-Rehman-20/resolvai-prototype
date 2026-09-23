from fastapi import Request
from fastapi.responses import JSONResponse
class DomainError(Exception):
    status_code=400; code="DOMAIN_ERROR"
    def __init__(self,message:str): self.message=message; super().__init__(message)
class TransactionNotFound(DomainError): status_code=404; code="TRANSACTION_NOT_FOUND"
class ApprovalNotFound(DomainError): status_code=404; code="APPROVAL_NOT_FOUND"
class DuplicateOperation(DomainError): status_code=409; code="DUPLICATE_OPERATION"
async def domain_exception_handler(request:Request, exc:DomainError):
    cid=getattr(request.state,"correlation_id","")
    return JSONResponse(status_code=exc.status_code,content={"error":{"code":exc.code,"message":exc.message,"correlation_id":cid}})
