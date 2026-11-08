"""
Inference. Use LLM + LoRA adapter
"""

# imports


from transformers import AutoTokenizer, PreTrainedTokenizerBase
from utils import load_model
from colorize import colorize
import shutil


# pre-configs


LORA_FOLDER = './results/lora'
LORA_FOLDER_FINAL = './results/lora/adapters'
PERFORMANCE_FOLDER = './results/performance'
ADAPTER_FOLDER = './results/lora/adapters/20261108_003826'
OPEN_MODEL_ID = 'Qwen/Qwen3-0.6B'
TERMINAL_WIDTH: int = shutil.get_terminal_size().columns


# load models


tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(OPEN_MODEL_ID)
original_model = load_model()
trained_model = load_model(ADAPTER_FOLDER)
models = [original_model, trained_model]

questions = [
    {'role': 'user', 'content': '¿Puedo llamar a la academia un lunes a las 8:30?'},
    {'role': 'user', 'content': '¿Nube abre algún sábado por la mañana?'},
    {'role': 'user', 'content': '¿Cuál es el coste total de inscribirse en el curso básico?'},
    {'role': 'user', 'content': '¿Aceptan pago con tarjeta de crédito para el curso básico?'},
    {'role': 'user', 'content': '¿Tengo clase del curso básico los miércoles?'},
    {'role': 'user', 'content': '¿Cuántos minutos tengo que reservar para cada sesión del curso?'},
    {'role': 'user', 'content': '¿Las clases se dan de forma presencial o a través de alguna plataforma?'},
    {'role': 'user', 'content': '¿Puedo descargar el material para leerlo sin conexión? ¿En qué formato viene?'},
    {'role': 'user', 'content': '¿Podré ver la grabación de una clase dentro de dos meses?'},
    {'role': 'user', 'content': '¿A qué email escribo si CampusNube no me carga el vídeo de la clase?'},
    {'role': 'user', 'content': 'Envié una consulta a soporte ayer, ¿cuándo debería tener respuesta como muy tarde?'},
    {'role': 'user', 'content': 'Si falto a 3 de cada 10 clases, ¿puedo obtener el certificado?'},
    {'role': 'user', 'content': '¿Tengo que pedir que me envíen el certificado por correo postal?'},
    {'role': 'user', 'content': 'Quiero darme de baja el próximo lunes, ¿a qué correo escribo y con cuánto margen?'},
    {'role': 'user', 'content': 'No me acuerdo de mi clave de CampusNube, ¿qué tengo que hacer para entrar?'},
]

responses_by_model = {
    'original_model': [],
    'trained_model': [],
}


for key, model in zip(responses_by_model.keys(), models):
    for question in questions:
        """Test two models (width and without LoRA adapter)"""

        messages = [question]

        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors='pt',
            return_dict=True,
        ).to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
        )

        prompt_length = inputs['input_ids'].shape[1]
        new_tokens = outputs[0][prompt_length:]

        responses_by_model[key].append(tokenizer.decode(new_tokens, skip_special_tokens=True))


for i, question in enumerate(questions):
    print(colorize('Pregunta: ', 'purple') + question['content'])
    print(colorize('Respuesta del modelo original: ', 'purple') + responses_by_model['original_model'][i])
    print(colorize('Respuesta del modelo+adaptador: ', 'purple') + responses_by_model['trained_model'][i])
    print()
    print('-' * TERMINAL_WIDTH)
    print()