import unittest  
import os
from fastapi.testclient import TestClient

# Importamos todo desde 'online_payments'
from online_payments import (
    app, 
    save_payment,
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

    def test_update_payment_success(self):
        """
        Test 5: Verifica que se pueda actualizar un pago en estado 'REGISTRADO'.
        """
        # 1. Creamos un pago de prueba
        self.client.post("/payments/pago-para-update?amount=100&payment_method=Test")
        # 2. Lo actualizamos con nuevos datos
        response = self.client.post(
            "/payments/pago-para-update/update?amount=500.75&payment_method=NuevoMetodo"
        )
        # 3. Verificamos la respuesta
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pago actualizado exitosamente", response.json()["message"])
        # 4. Verificamos que los datos se guardaron
        response_get = self.client.get("/payments/pago-para-update") # Asumiendo que GET /id existe o usamos GET /
        # (Usamos GET /payments ya que GET /id no está en la consigna)
        response_get_all = self.client.get("/payments")
        all_payments = response_get_all.json()
        updated_payment = all_payments["pago-para-update"]
        self.assertEqual(updated_payment[AMOUNT], 500.75)
        self.assertEqual(updated_payment[PAYMENT_METHOD], "NuevoMetodo")
        
    def test_update_payment_not_found(self):
        """
        Test 6: Verifica error 404 al actualizar un ID inexistente.
        """
        response = self.client.post(
            "/payments/id-no-existe/update?amount=1&payment_method=X"
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("no encontrado", response.json()["detail"])
        
    def test_update_payment_wrong_state(self):
        """
        Test 7: Verifica error 400 al actualizar un pago que NO está 'REGISTRADO'.
        """
        # 1. Forzamos la creación de un pago en estado 'FALLIDO'
        #    Usamos la función helper 'save_payment' directamente
        save_payment(
            payment_id="pago-fallido",
            amount=100,
            payment_method="Test",
            status=STATUS_FALLIDO
        )
        # 2. Intentamos actualizarlo
        response = self.client.post(
            "/payments/pago-fallido/update?amount=200&payment_method=New"
        )
        # 3. Verificamos el error
        self.assertEqual(response.status_code, 400)
        self.assertIn("no está en estado 'REGISTRADO'", response.json()["detail"])

    def test_pay_success_paypal(self):
        """Test 8: PayPal válido (monto < 5000) debe ser PAGADO."""
        self.client.post("/payments/p-ok?amount=4999&payment_method=PayPal")
        response = self.client.post("/payments/p-ok/pay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_status"], STATUS_PAGADO)
        
    def test_pay_fail_paypal_amount(self):
        """Test 9: PayPal inválido (monto >= 5000) debe ser FALLIDO."""
        self.client.post("/payments/p-fail?amount=5000&payment_method=PayPal")
        response = self.client.post("/payments/p-fail/pay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_status"], STATUS_FALLIDO)
        
    def test_pay_success_credit_card(self):
        """Test 10: Tarjeta de Crédito válida (< 10k, único) debe ser PAGADO."""
        self.client.post("/payments/cc-ok?amount=9999&payment_method=Tarjeta de Crédito")
        response = self.client.post("/payments/cc-ok/pay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_status"], STATUS_PAGADO)
        
    def test_pay_fail_credit_card_amount(self):
        """Test 11: Tarjeta de Crédito inválida (monto >= 10k) debe ser FALLIDO."""
        self.client.post("/payments/cc-fail-amt?amount=10000&payment_method=Tarjeta de Crédito")
        response = self.client.post("/payments/cc-fail-amt/pay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_status"], STATUS_FALLIDO)
        
    def test_pay_fail_credit_card_count(self):
        """Test 12: Tarjeta de Crédito inválida (ya existe 1 REGISTRADO) debe ser FALLIDO."""
        # 1. Creamos el primer pago (queda REGISTRADO)
        self.client.post("/payments/cc-1?amount=100&payment_method=Tarjeta de Crédito")
        # 2. Creamos el segundo pago (queda REGISTRADO)
        self.client.post("/payments/cc-2?amount=200&payment_method=Tarjeta de Crédito")
        # 3. Intentamos pagar el segundo. Debería fallar la regla de count.
        response = self.client.post("/payments/cc-2/pay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["new_status"], STATUS_FALLIDO)
        
    def test_pay_wrong_state(self):
        """Test 13: Intentar pagar un pago que no está 'REGISTRADO' da error 400."""
        self.client.post("/payments/p-pagado?amount=100&payment_method=PayPal")
        self.client.post("/payments/p-pagado/pay") # Pasa a PAGADO
        # Intentamos pagar de nuevo
        response = self.client.post("/payments/p-pagado/pay")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Solo se puede pagar un pago en estado 'REGISTRADO'", response.json()["detail"])
        
    def test_pay_unknown_method(self):
        """Test 14: Intentar pagar con un método desconocido da error 400."""
        self.client.post("/payments/p-bitcoin?amount=100&payment_method=Bitcoin")
        response = self.client.post("/payments/p-bitcoin/pay")
        self.assertEqual(response.status_code, 400)
        self.assertIn("no soportado o desconocido", response.json()["detail"])
