import json

from fastapi import FastAPI, HTTPException

STATUS = "status"
AMOUNT = "amount"
PAYMENT_METHOD = "payment_method"

STATUS_REGISTRADO = "REGISTRADO"
STATUS_PAGADO = "PAGADO"
STATUS_FALLIDO = "FALLIDO"

DATA_PATH = "data.json"

app = FastAPI()

@app.get("/payments")
async def get_all_payments():
    """
    Endpoint para obtener todos los pagos del sistema.
    """
    # Usamos la función helper que nos dieron en el código de referencia
    # para cargar todos los pagos desde data.json
    all_payments = load_all_payments()
    
    # FastAPI se encarga automáticamente de convertir
    # este diccionario de Python a formato JSON
    return all_payments

@app.post("/payments/{payment_id}")
async def register_payment(payment_id: str, amount: float, payment_method: str):
    """
    Endpoint para registrar un nuevo pago en el sistema.
    El pago se crea en estado 'REGISTRADO'.
    """
    
    # Usamos la función helper 'save_payment' que nos dio el código de referencia.
    # Le pasamos los datos recibidos y el estado inicial fijo.
    save_payment(
        payment_id=payment_id,
        amount=amount,
        payment_method=payment_method,
        status=STATUS_REGISTRADO  # Usamos la constante del código base
    )
    
    # Devolvemos un mensaje de éxito y los datos guardados.
    return {
        "message": "Pago registrado exitosamente",
        "payment_id": payment_id,
        "amount": amount,
        "payment_method": payment_method,
        "status": STATUS_REGISTRADO
    }

@app.post("/payments/{payment_id}/revert")
async def revert_payment(payment_id: str):
    """
    Endpoint para revertir un pago.
    Solo funciona si el pago está en estado 'FALLIDO'.
    Lo cambia de 'FALLIDO' -> 'REGISTRADO'.
    """
    
    # 1. Cargar los datos del pago específico
    try:
        # Usamos la función helper 'load_payment' del código base
        payment_data = load_payment(payment_id)
    except KeyError:
        # Si el payment_id no existe, 'load_payment' dará un error.
        # Lo capturamos y devolvemos un error 404 (Not Found)
        raise HTTPException(status_code=404, detail=f"Pago con id '{payment_id}' no encontrado.")

    current_status = payment_data.get(STATUS)

    # 2. Validar el estado (Lógica de Estado)
    # Verificamos si el estado actual es 'FALLIDO'
    if current_status != STATUS_FALLIDO:
        # Si no es 'FALLIDO', devolvemos un error 400 (Bad Request)
        # No podemos revertir un pago que ya está pagado o registrado.
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede revertir un pago que no está en estado 'FALLIDO'. Estado actual: {current_status}"
        )

    # 3. Actualizar el estado
    payment_data[STATUS] = STATUS_REGISTRADO
    
    # 4. Guardar los cambios en el archivo
    # Usamos 'save_payment_data' para guardar el diccionario modificado
    save_payment_data(payment_id, payment_data)

    return {
        "message": "Pago revertido exitosamente",
        "payment_id": payment_id,
        "new_status": STATUS_REGISTRADO
    }

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


"""
# Ejemplo de uso:
# Actualizando el status de un pago:
data = load_payment(payment_id)
data[STATUS] = STATUS_PAGADO
save_payment_data(payment_id, data)
"""



# Endpoints a implementar:
# * GET en el path /payments que retorne todos los pagos.
# * POST en el path /payments/{payment_id} que registre un nuevo pago.
# * POST en el path /payments/{payment_id}/update que cambie los parametros de una pago (amount, payment_method)
# * POST en el path /payments/{payment_id}/pay que intente.
# * POST en el path /payments/{payment_id}/revert que revertir el pago.


"""
# Ejemplos:

@app.get("/path/{arg_1}")
async def endpoint_a(arg_1: str, arg_2: float):
    # Este es un endpoint GET que recibe un argumento (arg_1) por path y otro por query (arg_2).
    return {}

@app.post("/path/{arg_1}/some_action")
async def endpoint_b(arg_1: str, arg_2: float, arg_3: str):
    # Este es un endpoint POST que recibe un argumento (arg_1) por path y otros dos por query (arg_2 y arg_3).
    return {}
"""
