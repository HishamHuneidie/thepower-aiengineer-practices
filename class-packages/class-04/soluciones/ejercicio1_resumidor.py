"""Solucion del Ejercicio 1 · Tu primer resumidor con LCEL: resumen en 3 vinetas."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama

prompt = ChatPromptTemplate.from_messages([
    ("system", "Resume el texto del usuario en EXACTAMENTE 3 viñetas breves en español. "
               "Una viñeta por línea, empezando por '- '. Sin introducción ni cierre."),
    ("human", "{texto}"),
])
# parser: texto -> lista de 3 viñetas limpias
tres_vinetas = RunnableLambda(lambda t: [l.strip().lstrip("-•* ").strip() for l in t.splitlines() if l.strip()][:3])
cadena = prompt | ChatOllama(model="llama3.1", temperature=0) | StrOutputParser() | tres_vinetas

textos = {
    "Texto 1 · teletrabajo": (
        "El teletrabajo se ha consolidado en muchas empresas tras la pandemia. Los empleados valoran ahorrar el "
        "tiempo de desplazamiento y organizar mejor su jornada, y muchas compañías han reducido costes de oficina. "
        "Sin embargo, también aparecen retos: la sensación de aislamiento, la dificultad para desconectar fuera del "
        "horario laboral y una comunicación menos espontánea entre equipos. Por eso muchas organizaciones apuestan "
        "por modelos híbridos, que combinan días en casa con días presenciales para mantener la cultura de empresa."),
    "Texto 2 · energía solar": (
        "La energía solar fotovoltaica es hoy una de las fuentes de electricidad más baratas del mundo. El precio de "
        "los paneles ha caído más de un 80% en la última década, lo que ha disparado las instalaciones tanto en "
        "grandes plantas como en tejados de viviendas. Su principal limitación es que solo produce cuando hay sol, "
        "por lo que el almacenamiento en baterías y la gestión inteligente de la red son claves para aprovecharla "
        "a cualquier hora. Muchos países la sitúan en el centro de sus planes para reducir emisiones."),
}
for nombre, texto in textos.items():
    vinetas = cadena.invoke({"texto": texto})
    print(f"── {nombre} ({len(texto.split())} palabras) ──")
    for v in vinetas:
        print(f"  • {v}")
    print()
