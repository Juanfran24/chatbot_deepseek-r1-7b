from datetime import datetime
import logging
import ollama

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Clase principal del chatbot de WhatsApp
class WhatsAppChatbot:
    def __init__(self, model_name, conversations={}):
        self.model_name = model_name
        # este atributo lee el context.txt y lo asigna como string
        self.context_prompt = self.load_context()
        self.conversations = conversations

    # Carga el contexto desde un archivo de texto
    def load_context(self):
        try:
            with open("context.txt", "r", encoding="utf-8") as file:
                context = file.read().strip()
                print(
                    f"\nContexto cargado: {context[:50]}..."
                )  # Mostrar solo los primeros 50 caracteres
            return context
        except FileNotFoundError:
            logger.error("Archivo context.txt no encontrado. Usando contexto vacío.")
            return ""

    # Obtiene el historial de conversación para un número de teléfono
    def get_conversation_history(self, phone_number):
        if phone_number not in self.conversations:
            self.conversations[phone_number] = []
        return self.conversations[phone_number]

    # Añade un mensaje al historial de conversación
    def add_to_conversation(self, phone_number, role, content):
        conversation = self.get_conversation_history(phone_number)
        conversation.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        # Limitar el historial para evitar exceder el límite de contexto
        if len(conversation) > 20:  # Mantener solo los últimos 20 mensajes
            self.conversations[phone_number] = conversation[-20:]

    # Prepara los mensajes para enviar al modelo LLM
    def prepare_messages(self, phone_number, user_message):
        messages = [{"role": "system", "content": self.context_prompt}]

        # Historial de conversación
        conversation = self.get_conversation_history(phone_number)

        # Agregar historial de conversación (solo últimos 2 mensajes para mayor velocidad)
        for msg in conversation[-2:]:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Añadir el mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})

        return messages

    # Genera una respuesta usando el modelo de IA LLM
    def generate_response(self, phone_number, user_message):
        try:
            # Preparar mensajes
            messages = self.prepare_messages(phone_number, user_message)

            # Llamar al modelo LLM con configuración ultra-optimizada para velocidad
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.1,  # Mínima creatividad para máxima velocidad
                    "top_p": 0.2,  # Limitar vocabulario para respuestas más rápidas
                    "max_tokens": 50,  # Respuestas muy cortas para WhatsApp
                    "num_predict": 50,  # Número de tokens a predecir
                    "top_k": 3,  # Solo las 3 opciones más probables
                    "num_ctx": 512,  # Contexto mínimo para mayor velocidad
                },
            )

            # Extraer el texto de la respuesta de Ollama
            assistant_message = response["message"]["content"]
            if assistant_message:
                assistant_message = assistant_message.strip()
            else:
                assistant_message = ""

            if not assistant_message:
                logger.error(f"{self.model_name} devolvió una respuesta vacía")
                return "Lo siento, no pude generar una respuesta en este momento. ¿Puedes intentar de nuevo?"

            # Guardar en el historial
            self.add_to_conversation(phone_number, "user", user_message)
            self.add_to_conversation(phone_number, "assistant", assistant_message)

            # Truncar si es muy largo para WhatsApp (límite ~1600 caracteres)
            if len(assistant_message) > 1500:
                assistant_message = (
                    assistant_message[:1500]
                    + "...\n\n(Respuesta truncada por límite de WhatsApp)"
                )

            return assistant_message

        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error procesando tu mensaje. Por favor, inténtalo de nuevo."
