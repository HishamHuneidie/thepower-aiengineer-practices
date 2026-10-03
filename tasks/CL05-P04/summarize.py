"""
    This script summarize 2 long texts.
    Creates a 3 items list from a text.
    There are two examples below.
"""

from typing import List, Tuple
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# utils
def tab(txt: str) -> str:
    return '\t' + txt.replace('\n', '\n\t')

def colorize(txt: str, color: str) -> str:
    green = '\033[32m'
    red = '\033[31m'
    blue = '\033[34m'
    yellow = '\033[33m'
    reset_color = '\033[0m'
    
    selected_color = None
    
    if color == 'green': selected_color = green
    elif color == 'red': selected_color = red
    elif color == 'blue': selected_color = blue
    elif color == 'yellow': selected_color = yellow
    
    if selected_color is None:
        return txt
    
    return f"{selected_color}{txt}{reset_color}"

# Modelo
model = ChatOllama(model="llama3.2:1b", temperature=0)

# Prompt
template_messages: List[Tuple] = [
    ('system', 'Eres un experto de la literatura y generador de resumenes. Cualquier cosa que te piden resumir lo haces extremadamente breve, conciso y resumido. Siempre resumes creando ÚNICAMENTE 3 viñetas. NUNCA son más ni menos viñetas. SIEMPRE son 3 viñetas. Nunca usas titulos, introducciones, concluciones ni placeholders fuera de las 3 viñetas.'),
    ('human', '{question}'),
]
prompt = ChatPromptTemplate.from_messages(template_messages)

# parser
parser = StrOutputParser()

# chain
chain = prompt | model | parser


# 6. Crear un primer texto largo para probar el resumidor.
text1 = """
La inteligencia artificial está transformando la forma en que las empresas trabajan y toman decisiones.
Muchas organizaciones utilizan modelos de lenguaje para automatizar tareas repetitivas, analizar documentos y asistir a empleados en procesos cotidianos.
Sin embargo, estas herramientas también requieren supervisión humana, especialmente cuando manejan información sensible o generan respuestas que pueden contener errores.
Por ello, las empresas deben combinar automatización con controles de calidad, seguridad y revisión.
El objetivo no es sustituir completamente a las personas, sino permitir que dediquen más tiempo a tareas creativas, estratégicas y de mayor valor para la organización.
"""
text2 = """
La energía solar se ha convertido en una alternativa cada vez más utilizada para producir electricidad de forma sostenible.
Durante los últimos años, el precio de los paneles solares ha disminuido considerablemente, facilitando su instalación en hogares y empresas.
Además, las mejoras en baterías permiten almacenar energía para utilizarla cuando no hay suficiente luz solar.
Aun así, existen desafíos relacionados con la inversión inicial, el espacio disponible y la estabilidad de la red eléctrica.
Por eso, muchos países están desarrollando incentivos y nuevas infraestructuras para acelerar la transición hacia fuentes de energía más limpias.
"""

# Ask with chain first time
answer = chain.invoke({"question": text1})
print(colorize('First summary:', 'blue'))
print(colorize(tab(answer), 'yellow'))

# Ask with chain second time
answer = chain.invoke({"question": text2})
print(colorize('Second summary:', 'blue'))
print(colorize(tab(answer), 'yellow'))

