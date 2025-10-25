import json

from fastapi import FastAPI

STATUS = "status"
AMOUNT = "amount"
PAYMENT_METHOD = "payment_method"

STATUS_REGISTRADO = "REGISTRADO"
STATUS_PAGADO = "PAGADO"
STATUS_FALLIDO = "FALLIDO"

DATA_PATH = "data.json"

app = FastAPI()


def load_all_payments():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return data


def save_all_payments(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)


def load_payment(payment_id):
    data = load_all_payments()[payment_id]
    return data


def save_payment_data(payment_id, data):
    all_data = load_all_payments()
    all_data[str(payment_id)] = data
    save_all_payments(all_data)


def save_payment(payment_id, amount, payment_method, status):
    data = {
        AMOUNT: amount,
        PAYMENT_METHOD: payment_method,
        STATUS: status,
    }
    save_payment_data(payment_id, data)


“””
# Ejemplo de uso:
# Actualizando el status de un pago:
data = load_payment(payment_id)
data[STATUS] = STATUS_PAGADO
save_payment_data(payment_id, data)
“””



# Endpoints a implementar:
# * GET en el path /payments que retorne todos los pagos.
# * POST en el path /payments/{payment_id} que registre un nuevo pago.
# * POST en el path /payments/{payment_id}/update que cambie los parametros de una pago (amount, payment_method)
# * POST en el path /payments/{payment_id}/pay que intente.
# * POST en el path /payments/{payment_id}/revert que revertir el pago.


“””
# Ejemplos:

@app.get("/path/{arg_1}")
async def endpoint_a(arg_1: str, arg_2: float):
    # Este es un endpoint GET que recibe un argumento (arg_1) por path y otro por query (arg_2).
    return {}

@app.post("/path/{arg_1}/some_action")
async def endpoint_b(arg_1: str, arg_2: float, arg_3: str):
    # Este es un endpoint POST que recibe un argumento (arg_1) por path y otros dos por query (arg_2 y arg_3).
    return {}
“””
