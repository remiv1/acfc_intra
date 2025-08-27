import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from redis import Redis, RedisError
from rq import Queue
from rq.job import Job
from mail_service import send_mail_task, check_unread_emails, get_email_details
from pydantic import BaseModel

app = FastAPI()

# Configuration Redis depuis les variables d'environnement
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))

redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
q = Queue(connection=redis_conn)

# Modèles Pydantic pour les réponses
class EmailInfo(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    snippet: str

class UnreadEmailsResponse(BaseModel):
    count: int
    emails: List[EmailInfo]

@app.get("/health")
def health_check() -> Dict[str, str]:
    """Endpoint pour vérifier la santé de l'application et Redis"""
    try:
        redis_conn.ping()
        return {"status": "healthy", "redis": "connected"}
    except RedisError:
        return {"status": "unhealthy", "redis": "disconnected"}

@app.post("/send-email")
def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Envoie un email de manière asynchrone"""
    try:
        job: Job = q.enqueue(send_mail_task, to, subject, body)
        return {
            "status": "accepted", 
            "job_id": job.id,
            "message": "Email en cours de traitement"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

@app.get("/unread-emails")
def get_unread_emails() -> UnreadEmailsResponse:
    """Récupère la liste des emails non lus"""
    try:
        unread_emails = check_unread_emails()
        return UnreadEmailsResponse(
            count=len(unread_emails),
            emails=unread_emails
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des emails: {str(e)}")

@app.get("/unread-emails/count")
def get_unread_count() -> Dict[str, int]:
    """Récupère uniquement le nombre d'emails non lus"""
    try:
        unread_emails = check_unread_emails()
        return {"count": len(unread_emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du comptage des emails: {str(e)}")

@app.get("/email/{email_id}")
def get_email(email_id: str) -> Dict[str, Any]:
    """Récupère les détails d'un email spécifique"""
    try:
        email_details = get_email_details(email_id)
        if not email_details:
            raise HTTPException(status_code=404, detail="Email non trouvé")
        return email_details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'email: {str(e)}")

@app.post("/check-emails")
def check_emails_async() -> Dict[str, Any]:
    """Lance une vérification asynchrone des emails"""
    try:
        job: Job = q.enqueue(check_unread_emails)
        return {
            "status": "accepted",
            "job_id": job.id,
            "message": "Vérification des emails en cours"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la vérification: {str(e)}")