import random

from faker.providers import DynamicProvider

lista_teste = [1, 2, 3, 4, 5]

print(lista_teste)

works_provider = DynamicProvider(
    provider_name="painel_works",
    elements=lista_teste,
)
print(works_provider.elements)

for _ in range(10):
    lista_teste.append(random.randint(0, 100))

print(lista_teste)
print(works_provider.elements)
