import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

def send_mail_task(to: str, subject: str, body: str) -> bool:
    """Fonction pour envoyer un email (existante)"""
    try:
        # Configuration SMTP depuis les variables d'environnement
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_user or not email_password:
            raise ValueError("Credentials email manquants")
        
        # Création du message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Envoi de l'email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Activation du chiffrement
            server.login(email_user, email_password)
            server.send_message(msg)
        
        return True  # Succès
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False

def check_unread_emails() -> List[Dict[str, Any]]:
    """Vérifie et retourne la liste des emails non lus"""
    try:
        # Configuration IMAP depuis les variables d'environnement
        imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        imap_port = int(os.getenv('IMAP_PORT', '993'))
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_user or not email_password:
            raise ValueError("Credentials email manquants")
        
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_user, email_password)
        mail.select('inbox')
        
        # Recherche des emails non lus
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            return []
        
        unread_emails = []
        message_ids = messages[0].split()
        
        # Limite à 50 emails pour éviter la surcharge
        for msg_id in message_ids[-50:]:
            try:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                if status != 'OK':
                    continue
                    
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extraction des informations
                subject = email_message.get('Subject', 'Sans sujet')
                sender = email_message.get('From', 'Expéditeur inconnu')
                date_str = email_message.get('Date', '')
                
                # Récupération d'un aperçu du contenu
                snippet = get_email_snippet(email_message)
                
                unread_emails.append({
                    'id': msg_id.decode(),
                    'subject': subject,
                    'sender': sender,
                    'date': date_str,
                    'snippet': snippet
                })
                
            except Exception as e:
                print(f"Erreur lors du traitement de l'email {msg_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        return unread_emails
        
    except Exception as e:
        print(f"Erreur lors de la vérification des emails: {e}")
        return []

def get_email_snippet(email_message) -> str:
    """Extrait un aperçu du contenu de l'email"""
    try:
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    return body[:200] + "..." if len(body) > 200 else body
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            return body[:200] + "..." if len(body) > 200 else body
    except:
        return "Aperçu non disponible"

def get_email_details(email_id: str) -> Optional[Dict[str, Any]]:
    """Récupère les détails complets d'un email"""
    try:
        # Configuration IMAP
        imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        imap_port = int(os.getenv('IMAP_PORT', '993'))
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_user or not email_password:
            return None
        
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_user, email_password)
        mail.select('inbox')
        
        # Récupération de l'email spécifique
        status, msg_data = mail.fetch(email_id.encode(), '(RFC822)')
        if status != 'OK':
            return None
            
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # Extraction complète des informations
        details = {
            'id': email_id,
            'subject': email_message.get('Subject', 'Sans sujet'),
            'sender': email_message.get('From', 'Expéditeur inconnu'),
            'to': email_message.get('To', ''),
            'date': email_message.get('Date', ''),
            'body': get_email_body(email_message),
            'attachments': get_attachments_info(email_message)
        }
        
        mail.close()
        mail.logout()
        
        return details
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'email {email_id}: {e}")
        return None

def get_email_body(email_message) -> str:
    """Extrait le corps complet de l'email"""
    try:
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
    except:
        return "Corps de l'email non disponible"

def get_attachments_info(email_message) -> List[Dict[str, str]]:
    """Récupère les informations sur les pièces jointes"""
    attachments = []
    try:
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                        })
    except:
        pass
    return attachments