import json
import abc

from fastapi import FastAPI, HTTPException

STATUS = "status"
AMOUNT = "amount"
PAYMENT_METHOD = "payment_method"

STATUS_REGISTRADO = "REGISTRADO"
STATUS_PAGADO = "PAGADO"
STATUS_FALLIDO = "FALLIDO"

DATA_PATH = "data.json"

class PaymentStrategy(abc.ABC):
    """
    Interfaz abstracta (Patrón Strategy) para una estrategia de validación de pago.
    """
    @abc.abstractmethod
    def validate(self, payment_data: dict, all_payments: dict) -> bool:
        """
        Valida un pago. Devuelve True si es válido, False si no.
        """
        pass
        
class CreditCardStrategy(PaymentStrategy):
    """
    Estrategia de validación para "Tarjeta de Crédito".
    """
    def validate(self, payment_data: dict, all_payments: dict) -> bool:
        # [cite_start]Regla 1: Verifica que el pago sea menor a $10.000 [cite: 1228]
        rule_amount = payment_data.get(AMOUNT, 0) < 10000
        # [cite_start]Regla 2: Valida que no haya más de 1 pago... en estado "REGISTRADO" [cite: 1229]
        # Contamos cuántos pagos (incluyendo este) están 'REGISTRADO'
        # con 'Tarjeta de Crédito'.
        registered_count = 0
        for payment in all_payments.values():
            if (payment.get(PAYMENT_METHOD) == "Tarjeta de Crédito" and
                payment.get(STATUS) == STATUS_REGISTRADO):
                registered_count += 1
        # La regla dice "no haya más de 1".
        # Si el conteo es 1 (solo este pago), pasa.
        # Si es 2 o más (este pago + otro ya registrado), falla.
        rule_count = (registered_count <= 1)
        return rule_amount and rule_count
class PayPalStrategy(PaymentStrategy):
    """
    Estrategia de validación para "PayPal".
    """
    def validate(self, payment_data: dict, all_payments: dict) -> bool:
        # [cite_start]Regla 1: Verifica que el pago sea menor de $5000 [cite: 1233]
        rule_amount = payment_data.get(AMOUNT, 0) < 5000
        return rule_amount

PAYMENT_STRATEGIES = {
    "Tarjeta de Crédito": CreditCardStrategy(),
    "PayPal": PayPalStrategy()
}

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

@app.post("/payments/{payment_id}/update")
async def update_payment(payment_id: str, amount: float, payment_method: str):
    """
    Endpoint para actualizar la información de un pago existente.
    Solo funciona si el pago está en estado 'REGISTRADO'.
    """
   
    # 1. Cargar los datos del pago
    try:
        payment_data = load_payment(payment_id)
    except KeyError:
        # Si el ID no existe, devolvemos 404
        raise HTTPException(status_code=404, detail=f"Pago con id '{payment_id}' no encontrado.")

    current_status = payment_data.get(STATUS)

    # 2. Validar el estado (Lógica de Estado)
    # Verificamos si el estado actual es 'REGISTRADO'
    if current_status != STATUS_REGISTRADO:
        # Si no es 'REGISTRADO', devolvemos un error 400 (Bad Request)
        # No podemos modificar un pago que ya fue pagado o falló.
        raise HTTPException(
            status_code=400,
            detail=f"No se puede actualizar un pago que no está en estado 'REGISTRADO'. Estado actual: {current_status}"
        )

    # 3. Actualizar los datos
    payment_data[AMOUNT] = amount
    payment_data[PAYMENT_METHOD] = payment_method
   
    # 4. Guardar los cambios
    save_payment_data(payment_id, payment_data)

    return {
        "message": "Pago actualizado exitosamente",
        "payment_id": payment_id,
        "new_data": payment_data
    }

@app.post("/payments/{payment_id}/pay")
async def pay_payment(payment_id: str):
    """
    Endpoint para procesar un pago.
    Valida y marca como PAGADO o FALLIDO. Utiliza el Patrón Strategy.
    """
    # 1. Cargar pago (y verificar 404)
    try:
        payment_data = load_payment(payment_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pago con id '{payment_id}' no encontrado.")
    # 2. State Guard: Solo podemos pagar un pago 'REGISTRADO'
    current_status = payment_data.get(STATUS)
    if current_status != STATUS_REGISTRADO:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede pagar un pago en estado 'REGISTRADO'. Estado actual: {current_status}"
        )
    # 3. Cargar TODOS los pagos (necesario para la regla de Tarjeta de Crédito)
    all_payments = load_all_payments()
    # 4. Seleccionar la Estrategia
    payment_method = payment_data.get(PAYMENT_METHOD)
    strategy = PAYMENT_STRATEGIES.get(payment_method)
    # Si el método no es "Tarjeta de Crédito" ni "PayPal", no tenemos estrategia
    if not strategy:
        raise HTTPException(
            status_code=400,
            detail=f"Método de pago '{payment_method}' no soportado o desconocido."
        )
    # 5. Ejecutar la Estrategia
    # El flujo de pago depende de esta validación
    is_valid = strategy.validate(payment_data, all_payments)
    # 6. Actualizar Estado (PAGADO o FALLIDO)
    if is_valid:
        new_status = STATUS_PAGADO
        message = "Pago procesado y aprobado exitosamente."
    else:
        new_status = STATUS_FALLIDO
        message = "Pago fallido. La validación no pasó."
    payment_data[STATUS] = new_status
    save_payment_data(payment_id, payment_data)
    return {
        "message": message,
        "payment_id": payment_id,
        "new_status": new_status
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
