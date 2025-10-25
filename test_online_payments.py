import unittest  
import os
from fastapi.testclient import TestClient

# Importamos todo desde 'online_payments'
from online_payments import (
    app, 
    save_all_payments,
    STATUS, 
    AMOUNT, 
    PAYMENT_METHOD,
    STATUS_REGISTRADO,
    STATUS_FALLIDO
)

# Creamos una clase que hereda de unittest.TestCase
class TestPaymentAPI(unittest.TestCase):

    # Creamos el cliente de prueba como una variable de clase
    client = TestClient(app)

    def setUp(self):
        """
        Este método se ejecuta ANTES de cada test (test_...).
        Limpia el 'data.json' para asegurar que cada test sea independiente.
        """
        save_all_payments({})
    
    def tearDown(self):
        """
        Este método se ejecuta DESPUÉS de cada test.
        Limpia el 'data.json' por si un test falla a mitad de camino.
        """
        save_all_payments({})

    def test_get_all_payments_empty(self):
        """
        Test 1: Verifica GET /payments con base de datos vacía.
        """
        response = self.client.get("/payments")
        
        # En lugar de 'assert', usamos los métodos de self
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_register_payment_success(self):
        """
        Test 2: Verifica el registro exitoso de un pago.
        """
        response = self.client.post(
            "/payments/pago123?amount=150.50&payment_method=Tarjeta"
        )
        
        # Verificamos la respuesta de la API
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["message"], "Pago registrado exitosamente")
        self.assertEqual(response_data["status"], STATUS_REGISTRADO)
        
        # Verificamos que se haya guardado
        response_get = self.client.get("/payments")
        all_payments = response_get.json()
        
        self.assertIn("pago123", all_payments) # Verifica que la key exista
        self.assertEqual(all_payments["pago123"][AMOUNT], 150.50)

    def test_revert_payment_not_found(self):
        """
        Test 3: Verifica error 404 al revertir un ID inexistente.
        """
        response = self.client.post("/payments/id-no-existe/revert")
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("no encontrado", response.json()["detail"]) # Verifica que el mensaje de error sea correcto

    def test_revert_payment_wrong_state(self):
        """
        Test 4: Verifica error 400 al revertir un pago en estado 'REGISTRADO'.
        """
        # 1. Creamos un pago
        self.client.post("/payments/pago-registrado?amount=100&payment_method=Test")
        
        # 2. Intentamos revertirlo
        response = self.client.post("/payments/pago-registrado/revert")
        
        # 3. Verificamos el error
        self.assertEqual(response.status_code, 400)
        self.assertIn("no está en estado 'FALLIDO'", response.json()["detail"])