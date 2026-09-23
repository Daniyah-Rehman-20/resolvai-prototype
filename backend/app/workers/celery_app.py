from celery import Celery
from app.core.config import settings
celery_app=Celery("payresolve",broker=settings.rabbitmq_url,backend=settings.redis_url)
celery_app.conf.task_serializer="json"
@celery_app.task(bind=True,autoretry_for=(Exception,),retry_backoff=True,max_retries=3)
def ingest_document(self,document_id:str): return {"document_id":document_id,"status":"QUEUED_DEMO"}
