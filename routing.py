from models import OrderItem, Location

def get_corredor_group(rua):
    """
    Agrupa ruas em pares de corredores.
    Rua 1 é um caso especial.
    Ruas 2 e 3 estão no mesmo corredor, 4 e 5, etc.
    """
    if rua == 1:
        return 0  # Grupo especial para a Rua 1
    if rua % 2 == 0:
        return rua // 2 # Corredor 1 (Ruas 2,3), Corredor 2 (Ruas 4,5)
    else:
        return (rua + 1) // 2

def sort_picking_list(order_items):
    """
    Ordena uma lista de itens de pedido de acordo com a nova lógica
    da "Serpente" baseada nos corredores.
    """
    
    def get_sort_key(order_item: OrderItem):
        # Garante que o item tenha uma localização antes de tentar ordenar
        if not order_item.location:
            # Itens sem localização são colocados no final
            return (float('inf'),) 
            
        location = order_item.location
        
        corredor = get_corredor_group(location.rua)
        
        # Lógica de ordenação do rack dentro de um corredor
        # Sobe o corredor (ordem crescente de racks) para ruas de número menor (2, 4, 6...)
        # Desce o corredor (ordem decrescente de racks) para ruas de número maior (3, 5, 7...)
        rack_order = location.rack_number
        if location.rua > 1 and location.rua % 2 != 0: # Se a rua for ímpar (e não for a 1)
            rack_order = -location.rack_number

        # A tupla define a prioridade da ordenação:
        # 1. Grupo do Corredor (Rua 1 primeiro, depois corredor 2/3, etc.)
        # 2. Número da Rua (dentro do corredor, a menor vem primeiro)
        # 3. Ordem do Rack (crescente ou decrescente dependendo da rua)
        # 4. Linha (sempre crescente)
        # 5. Coluna (ordem alfabética)
        return (corredor, location.rua, rack_order, location.linha, location.coluna)

    return sorted(order_items, key=get_sort_key) 