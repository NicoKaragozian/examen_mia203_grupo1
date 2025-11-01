"""
Punto de entrada principal para la API de Pagos Online.

Este archivo sirve como punto de entrada para ejecutar la aplicación según
lo mencionado en el enunciado: "fastapi dev main.py"

El código principal está en online_payments.py para mantener la organización
y permitir importaciones fáciles en los tests.
"""

from online_payments import app

# FastAPI va a detectar automáticamente la variable 'app' en este módulo

if __name__ == "__main__":
    import uvicorn
    
    # Si se ejecuta directamente con python main.py, ejecuta el servidor
    uvicorn.run(
        "online_payments:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

