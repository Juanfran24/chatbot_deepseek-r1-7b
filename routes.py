from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_routes(app, chatbot, conversations, AI_MODEL):

    @app.route("/webhook", methods=["POST"])
    def webhook():
        """Endpoint para recibir mensajes de WhatsApp via Twilio"""
        try:
            # Obtener datos del webhook
            incoming_msg = request.values.get("Body", "").strip()
            from_number = request.values.get("From", "")

            logger.info(f"Mensaje recibido de {from_number}: {incoming_msg}")

            # Crear respuesta de Twilio
            resp = MessagingResponse()

            # Verificar que hay un mensaje o si es un saludo inicial
            if not incoming_msg or incoming_msg.lower() in [
                "hola",
                "hi",
                "hello",
                "buenas",
                "buenos dias",
                "buenas tardes",
                "buenas noches",
            ]:
                resp.message("Hola! Soy tu asistente de IA. ¿En qué puedo ayudarte?")
                return str(resp)

            # Comandos especiales
            if incoming_msg.lower() in ["/help", "ayuda", "help"]:
                help_text = """🤖 **Comandos disponibles:**
• `/reset` - Reinicia la conversación
• `/help` - Muestra esta ayuda

¡Pregúntame lo que quieras! 😊"""
                resp.message(help_text)
                return str(resp)

            if incoming_msg.lower() in ["/reset", "reset", "reiniciar"]:
                # Limpiar historial de conversación
                if from_number in conversations:
                    del conversations[from_number]
                resp.message("✅ Conversación reiniciada. ¿En qué puedo ayudarte?")
                return str(resp)

            # Generar respuesta con IA
            try:
                # Generar respuesta con timeout simple
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        chatbot.generate_response, from_number, incoming_msg
                    )
                    try:
                        ai_response = future.result(timeout=12)  # 12 segundos máximo

                        # Enviar respuesta
                        resp.message(ai_response)
                        return str(resp)

                    except TimeoutError:
                        logger.error(f"Timeout alcanzado para: {incoming_msg[:30]}...")
                        resp.message(
                            "Tu consulta está tardando más de lo esperado. Por favor, intenta con una pregunta más específica."
                        )
                        return str(resp)

            except Exception as ai_error:
                logger.error(f"Error al generar respuesta: {str(ai_error)}")
                resp.message(
                    "Lo siento, hubo un problema al procesar tu mensaje. Por favor, inténtalo de nuevo."
                )
                return str(resp)

        except Exception as e:
            logger.error(f"Error en webhook: {str(e)}")
            resp = MessagingResponse()
            resp.message(
                "Lo siento, hubo un error interno. Por favor, inténtalo más tarde."
            )
            return str(resp)

    @app.route("/", methods=["GET"])
    def home():
        """Página de inicio simple"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhatsApp Chatbot - {AI_MODEL}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .status {{ color: #25D366; font-weight: bold; }}
                .info {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 WhatsApp Chatbot con {AI_MODEL}</h1>
                <p class="status">✅ Servicio activo</p>
                
                <div class="info">
                    <h3>Información del servicio:</h3>
                    <ul>
                        <li><strong>Modelo:</strong> {AI_MODEL}</li>
                        <li><strong>Endpoint:</strong> /webhook</li>
                        <li><strong>Estado:</strong> <a href="/status" target="_blank">Verificar estado</a></li>
                    </ul>
                </div>
                
                <div class="info">
                    <h3>Configuración de Twilio:</h3>
                    <p>Configura tu webhook URL en Twilio: <br>
                    <code>https://tu-dominio.com/webhook</code></p>
                </div>
            </div>
        </body>
        </html>
        """

    @app.route("/status", methods=["GET"])
    def status():
        """Endpoint para verificar el estado del servicio"""
        return {
            "status": "active",
            "model": AI_MODEL,
            "endpoints": ["/webhook", "/", "/status"],
        }
