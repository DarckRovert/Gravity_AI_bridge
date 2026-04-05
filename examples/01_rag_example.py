"""
Ejemplo de uso de RAG (Retrieval-Augmented Generation) sobre documentación local con Gravity AI Bridge.
"""
from session_manager import SessionManager

def main():
    session = SessionManager()
    doc_path = "./documents/manual.pdf"
    context = session.load_rag(doc_path)
    pregunta = "¿Cuál es la arquitectura general de Gravity AI Bridge?"
    respuesta = session.query_with_rag(pregunta, context)
    print("Respuesta:", respuesta)

if __name__ == "__main__":
    main()