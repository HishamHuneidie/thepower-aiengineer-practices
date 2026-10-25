"""
    Semantic search using cosine distance
"""

# imports

from connection import connect, enable_vectors, create_table_phrases_tenant, delete_tables
from transformer import transform
from tabulate import tabulate

# connect and activate pgvector

conn = connect(True)
enable_vectors(conn)
create_table_phrases_tenant(conn)

# examples

PHRASES: list[tuple[str,str]] = [
    ('1', 'La inteligencia artificial permite automatizar tareas complejas mediante algoritmos avanzados.'),
    ('2', 'Los modelos de aprendizaje automático pueden analizar datos y generar predicciones.'),
    ('1', 'Los desarrolladores utilizan redes neuronales para construir aplicaciones inteligentes.'),
    ('2', 'El machine learning ayuda a las empresas a optimizar procesos y tomar mejores decisiones.'),
    ('1', 'Los sistemas basados en IA pueden aprender patrones y mejorar su rendimiento con el tiempo.'),
    ('2', 'El próximo verano quiero viajar a Japón para conocer su cultura y gastronomía.'),
    ('1', 'Los ejercicios cardiovasculares ayudan a fortalecer el corazón y mejorar la resistencia física.'),
]

tenants = [tuple_phrase[0] for tuple_phrase in PHRASES]
contents = [tuple_phrase[1] for tuple_phrase in PHRASES]

print()
print('Dataset')
print(tabulate(PHRASES, headers=['Tenant', 'Answer'], tablefmt='rounded_grid'))
print()

# save in pg

with conn.cursor() as cursor:
    cursor.executemany('INSERT INTO phrases_tenant (tenant_id, content, embedding) VALUES (%s, %s, %s::VECTOR)', list(zip(tenants, contents, transform(contents).tolist())))

print()

# embedded questions

questions = [
    '¿Cómo puede la inteligencia artificial ayudar a las empresas a automatizar procesos y mejorar sus decisiones?',
    '¿De qué manera utilizan los desarrolladores las redes neuronales y el aprendizaje automático para crear aplicaciones inteligentes?',
]

# execute search

headers: list[str|float] = ['Question', '(tenant) Similar answers', 'Distance']
results_table: list[list[str|float]] = []

owners = list(set(tenants))
for tenant in owners:
    for question in questions:
        embedding = transform(question)
        
        results = conn.execute('SELECT tenant_id, content, embedding <=> %s AS distance FROM phrases_tenant WHERE tenant_id = %s ORDER BY 3 ASC LIMIT 2', (embedding,tenant))

        contents = []
        distances = []
        for tenant_id, content, distance in results:
            contents.append(f'· ({tenant_id}) {content}')
            distances.append(f'· {distance:.2f}')

        results_table.append([question, '\n'.join(contents), '\n'.join(distances)])

# show results

print('Cosine distance:')
print(tabulate(results_table, headers=headers, tablefmt='rounded_grid'))

# Clean all

delete_tables(conn)