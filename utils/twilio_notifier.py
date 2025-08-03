# utils/twilio_notifier.py

from twilio.rest import Client
import os

# DICA: use variáveis de ambiente para não deixar tokens visíveis no código
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_FROM")  # número fornecido pela Twilio

def enviar_sms(destino, mensagem):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=mensagem,
            from_=TWILIO_PHONE_NUMBER,
            to=destino
        )
        return msg.sid
    except Exception as e:
        print("Erro ao enviar SMS:", e)
        return None
