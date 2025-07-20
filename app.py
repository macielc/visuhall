import os
import re
import time
import serial
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, PickingOrder, OrderItem, Location, Product
from routing import sort_picking_list

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Configuração do Banco de Dados ---
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_name = os.getenv('POSTGRES_DB')
db_host = 'db'

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas no início
Base.metadata.create_all(bind=engine)

# --- Gerenciamento da Conexão Serial Persistente ---
ser = None  # Objeto serial global

def init_serial():
    """Inicializa a conexão serial e a mantém aberta."""
    global ser
    if ser and ser.is_open:
        return
    try:
        port = '/dev/ttyUSB0'
        if os.name == 'nt': port = 'COM3'
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)  # Espera o boot do Arduino, SÓ UMA VEZ.
        print(f"Conexão serial com {port} estabelecida.")
    except serial.SerialException as e:
        ser = None
        print(f"ALERTA: Não foi possível conectar ao Arduino. {e}")

# --- Dependência para obter a sessão do DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Comunicação Serial com Arduino ---
def send_commands_to_arduino(commands):
    """Envia uma lista de comandos através da conexão serial persistente."""
    global ser
    if not commands:
        return True
    
    if ser is None or not ser.is_open:
        print("Tentando reconectar ao Arduino...")
        init_serial() # Tenta reabrir a porta se estiver fechada
        if ser is None:
             print("Falha na reconexão. Comandos não enviados.")
             return False

    try:
        for command in commands:
            command_with_newline = f"{command}\n"
            ser.write(command_with_newline.encode())
            time.sleep(0.05)
        return True
    except serial.SerialException as e:
        print(f"Erro ao enviar comando para o Arduino: {e}. Fechando a porta.")
        ser.close()
        ser = None
        return False

# --- Rotas do Frontend ---
@app.route('/')
def serve_home():
    return send_from_directory('frontend', 'home.html')

@app.route('/picking')
def serve_picking_page():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path != 'picking' and os.path.exists(os.path.join('frontend', path)):
        return send_from_directory('frontend', path)
    # Fallback para a página de picking ou home, se necessário
    return send_from_directory('frontend', 'index.html')


# --- Rotas da API ---
@app.route('/api/picking_orders', methods=['GET'])
def get_picking_orders():
    status = request.args.get('status')
    db = SessionLocal()
    try:
        query = db.query(PickingOrder)
        if status:
            query = query.filter(PickingOrder.status == status)
        orders = query.order_by(PickingOrder.id.desc()).all()
        orders_data = [{
            "id": order.id, "status": order.status,
            "created_at": order.created_at.isoformat(),
            "item_count": len(order.items)
        } for order in orders]
        return jsonify(orders_data)
    finally:
        db.close()

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ok", "version": "1.1.0"})

@app.route('/api/arduino/commands', methods=['POST'])
def arduino_commands():
    data = request.get_json()
    commands = data.get('commands')
    if not commands or not isinstance(commands, list):
        return jsonify({"error": "Lista de comandos inválida."}), 400
    send_commands_to_arduino(commands)
    return jsonify({"message": f"{len(commands)} comandos enviados."})

@app.route('/api/arduino/reset', methods=['POST'])
def arduino_reset():
    reset_commands = [f"S{i}_{color}_OFF" for i in range(1, 6) for color in ["GREEN", "YELLOW"]]
    send_commands_to_arduino(reset_commands)
    return jsonify({"message": "Comandos de reset enviados."})


@app.route('/api/picking_orders/from_text', methods=['POST'])
def create_picking_order_from_text():
    db = SessionLocal()
    try:
        text = request.data.decode('utf-8')
        if not text:
            return jsonify({"error": "Texto não fornecido"}), 400

        print("--- RAW TEXT RECEIVED ---\n" + text + "\n--------------------------")

        enderecados = []
        try:
            materiais_section = text.split("Materiais")[1].split("Materiais não endereçados")[0]
            item_blocks = re.split(r'\s*(RUA\s*0\d\s*/)', materiais_section)
            
            for i in range(1, len(item_blocks), 2):
                block_text = item_blocks[i] + item_blocks[i+1]
                lines = [line.strip() for line in block_text.strip().split('\n') if line.strip()]
                if len(lines) < 4: continue
                
                address_match = re.search(r"RUA\s*(\d+)\s*/\s*Rack\s*(\d+)\s*/\s*(\d+)\s*/\s*([A-Z0-9]+)", lines[0])
                quantity_match = re.search(r'\d+', lines[1])
                
                if address_match and quantity_match:
                    enderecados.append({
                        "rua": int(address_match.group(1)), "rack": int(address_match.group(2)),
                        "linha": int(address_match.group(3)), "coluna": address_match.group(4),
                        "quantity": int(quantity_match.group()),
                        "sku": lines[2], "description": lines[3]
                    })
        except IndexError:
            return jsonify({"error": "Formato do PDF inesperado."}), 400

        if not enderecados:
            return jsonify({"error": "Nenhum item endereçado completo foi extraído"}), 400

        items_para_db = []
        for item_data in enderecados:
            location = db.query(Location).filter_by(rua=item_data['rua'], rack_number=item_data['rack'], linha=item_data['linha'], coluna=item_data['coluna']).first()
            if location and location.product:
                items_para_db.append(OrderItem(product_id=location.product_id, quantity=item_data['quantity'], status="pending", location_id=location.id))

        if not items_para_db:
            return jsonify({"error": "Nenhum dos itens corresponde a um local válido."}), 400

        # 1. Cria a ordem com os itens ainda não ordenados
        new_order = PickingOrder(status="pending", items=items_para_db)
        db.add(new_order)
        db.commit()
        db.refresh(new_order) # Garante que as relações (como .location) sejam carregadas

        # 2. Agora que os itens existem no DB, podemos ordená-los com segurança
        new_order.items = sort_picking_list(new_order.items)
        db.commit()


        return jsonify({"message": "Ordem de picking criada com sucesso.", "order_id": new_order.id}), 201
    finally:
        db.close()

def calculate_led_state_map(order):
    """
    Calcula um mapa do estado de cada LED para a ordem atual.
    Retorna um dicionário como {led_number: state}, onde state é 'GREEN_BLINK', 'YELLOW_ON', ou 'OFF'.
    """
    state_map = {i: 'OFF' for i in range(1, 6)}
    pending_items = [item for item in order.items if item.status == 'pending' and item.location]
    
    if not pending_items:
        return state_map

    pending_ruas = sorted(list(set(item.location.rua for item in pending_items)))
    active_rua = pending_ruas[0]

    for rua in pending_ruas:
        led_number = ((rua - 1) % 5) + 1
        if rua == active_rua:
            state_map[led_number] = 'GREEN_BLINK'
        else:
            state_map[led_number] = 'YELLOW_ON'
    return state_map

def map_to_commands(state_map):
    """Converte um mapa de estado em uma lista de comandos de LED."""
    commands = []
    for led, state in state_map.items():
        if state == 'GREEN_BLINK': commands.append(f"S{led}_GREEN_BLINK")
        elif state == 'YELLOW_ON': commands.append(f"S{led}_YELLOW_ON")
    return commands

@app.route('/api/picking_orders/<int:order_id>', methods=['GET'])
def get_picking_order(order_id: int):
    db = SessionLocal()
    try:
        order = db.query(PickingOrder).filter(PickingOrder.id == order_id).first()
        if not order:
            return jsonify({"error": "Ordem de picking não encontrada"}), 404

        state_map = calculate_led_state_map(order)
        led_commands = map_to_commands(state_map)
        
        order.items = sort_picking_list(order.items)

        items_data = [{
            "id": item.id, "product_sku": item.product.sku,
            "product_name": item.product.name, "quantity": item.quantity,
            "status": item.status, "location": item.location.get_address_str() if item.location else "N/A"
        } for item in order.items]
            
        return jsonify({
            "id": order.id, "status": order.status, "items": items_data,
            "initial_led_commands": led_commands 
        })
    finally:
        db.close()

@app.route('/api/order_items/<int:item_id>/<status>', methods=['PUT'])
def update_item_status(item_id: int, status: str):
    db = SessionLocal()
    try:
        if status not in ['picked', 'skipped']:
            return jsonify({"error": "Status inválido"}), 400

        item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not item: return jsonify({"error": "Item não encontrado"}), 404

        order = item.order
        
        # 1. Captura o estado dos LEDs ANTES da atualização
        state_map_before = calculate_led_state_map(order)

        # 2. ATUALIZA O STATUS DO ITEM
        item.status = status
        db.commit()
        db.refresh(order)

        # 3. Captura o estado dos LEDs DEPOIS da atualização
        state_map_after = calculate_led_state_map(order)
        
        # 4. Compara os mapas para gerar a lista MÍNIMA de comandos
        led_commands_off, led_commands_on = [], []
        for led_num in range(1, 6):
            state_before = state_map_before.get(led_num, 'OFF')
            state_after = state_map_after.get(led_num, 'OFF')

            if state_before != state_after:
                # Se mudou, primeiro desliga o estado anterior (se não era OFF)
                if state_before == 'GREEN_BLINK': led_commands_off.append(f"S{led_num}_GREEN_OFF")
                elif state_before == 'YELLOW_ON': led_commands_off.append(f"S{led_num}_YELLOW_OFF")
                
                # Depois, liga o novo estado (se não for OFF)
                if state_after == 'GREEN_BLINK': led_commands_on.append(f"S{led_num}_GREEN_BLINK")
                elif state_after == 'YELLOW_ON': led_commands_on.append(f"S{led_num}_YELLOW_ON")

        print(f"--- INTELLIGENT TRANSITION (item {item_id}) ---")
        print(f"Commands OFF: {led_commands_off}")
        print(f"Commands ON: {led_commands_on}")
        print("---------------------------------")

        return jsonify({
            "message": f"Item {item_id} marcado como {status}.",
            "led_commands_off": led_commands_off,
            "led_commands_on": led_commands_on
        })
    finally:
        db.close()

if __name__ == '__main__':
    init_serial() # Inicializa a porta serial ao iniciar o servidor
    app.run(host='0.0.0.0', port=8000, debug=True) 