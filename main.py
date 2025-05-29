import logging
from flask import Flask
from whatsapp_chatbot import WhatsAppChatbot
from routes import register_routes

# Creación de la aplicación Flask
app = Flask(__name__)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
AI_MODEL = "deepseek-r1:7b"  # Modelo DeepSeek R1 7B local con Ollama

# Almacenamiento en memoria de las conversaciones (en producción usa una base de datos)
conversations = {}

# Instanciar el chatbot
chatbot = WhatsAppChatbot(AI_MODEL)

# Registrar las rutas
register_routes(app, chatbot, conversations, AI_MODEL)

if __name__ == "__main__":
    # Iniciar la aplicación Flask
    app.run(host="0.0.0.0", port=5000, debug=True)
    logger.info("Servidor Flask iniciado en el puerto 5000")
