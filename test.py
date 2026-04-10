import smtplib
from email.message import EmailMessage
import re
def enviar_notificacao_lead(nome_cliente, contacto_cliente, interesse_cliente):
    meu_email = "evaall283@gmail.com"
    minha_senha = "fvwklzagrflecckj"
    email_destino = "evaall283@gmail.com"
    
    msg = EmailMessage()
    msg['From'] = meu_email
    msg['To'] = email_destino
    msg['Subject'] = f"🔥 NOVO LEAD: {nome_cliente} está interessado!"

    corpo = f"""
    Temos um novo potencial cliente interessado!
    
    Nome: {nome_cliente}
    Contacto: {contacto_cliente}
    Interesse: {interesse_cliente}
    
    Responde rápido para não perderes a venda!
    """
    msg.set_content(corpo)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(meu_email, minha_senha)
            server.send_message(msg)
            print("email enviado")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

mensagem  = input("digita seu contacto:")
padrao_tel = r"9\d{2}\s?\d{3}\s?\d{3}"
tell = re.search(padrao_tel, mensagem)
padrao_email = r"[\w\.-]+@[\w\.-]+\.\w+"
email = re.search(padrao_email, mensagem) 

if tell or email:
    mensagem = tell if tell else email
    enviar_notificacao_lead("evandro", mensagem, "perguntou sobre a empresa")
