from flask import Flask
from flask.globals import request
from flask_apscheduler import APScheduler

import starkbank

from datetime import datetime, timedelta
from cpf_generator import CPF
from random import randint

import names

from dotenv import load_dotenv
import os

load_dotenv()

CHAVE_PRIVADA = os.getenv("CHAVE_PRIVADA")
AMBIENTE = os.getenv("AMBIENTE")
ID_PROJETO = os.getenv("ID_PROJETO")
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")


# Criacao da variavel project para uso da API
projeto = starkbank.Project(environment=AMBIENTE,
                            id=ID_PROJETO,
                            private_key=CHAVE_PRIVADA)

starkbank.user = projeto
app = Flask(__name__)

# Scheduler que faz a funcao de gerar invoices rodar cada 3 horas
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


# Funcao para transferir valor determinado para conta principal stark
def transferir(valor, nome):
    transferencia = starkbank.Transaction(
        amount=valor,
        receiver_id=MAIN_ACCOUNT,
        description=f"{nome} | Carteira Intermediaria -> Carteira Principal",
        external_id=str(randint(1000000, 100000000)))
    starkbank.transaction.create([transferencia])


# Webhook para verificar e atualizar a cada invoice
@app.route('/hook', methods=['POST'])
def hook():
    if request.method == 'POST':
        log = request.json['event']['log']
        valor = log['invoice']['amount']
        nome = log['invoice']['name']

        ### Debug ###
        print("---------------------------")
        print(log['type'])
        print(valor)
        print(nome)
        print("---------------------------")
        ### ##### ###

        if log['type'] == 'paid':
            transferir(valor - 50, nome)
        return 'OK', 200


# Executar funcao a cada 3 horas e enviar de 8 a 12 invoices
@scheduler.task("interval", id='invoices', hours=3)
def gerar_invoices():
    invoice_list = []

    # Loop para criar invoice com cpf valido, nome e valores aleatorios para cada
    for i in range(randint(8, 12)):
        invoice_list.append(
            starkbank.Invoice(amount=randint(10000, 100000),
                              name=names.get_full_name(),
                              tax_id=CPF.format(CPF.generate()),
                              due=datetime.utcnow() + timedelta(hours=24),
                              expiration=timedelta(hours=48).total_seconds(),
                              fine=randint(1, 20),
                              interest=1.5))

    starkbank.invoice.create(invoice_list)

    return None


if __name__ == '__main__':
    gerar_invoices()
    #app.run(host='0.0.0.0', port=80)
