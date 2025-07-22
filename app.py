import os
import re
import time
# import serial <-- REMOVIDO
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import paho.mqtt.client as mqtt

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

# Criar tabelas foi movido para seed_db.py para ser um passo de setup
# Base.metadata.create_all(bind=engine)

# --- Configuração e Conexão MQTT ---
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'mqtt')
MQTT_PORT = 1883
MQTT_CLIENT_ID = "visuhall_backend_server"
TOTAL_RUAS_FISICAS = 2

mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120) # Define a reconexão automática

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao Broker MQTT com sucesso!")
        client.is_connected_flag = True
    else:
        print(f"Falha ao conectar ao MQTT Broker, código de erro: {rc}")
        client.is_connected_flag = False

def on_disconnect(client, userdata, rc):
    print(f"Desconectado do MQTT Broker com código: {rc}. Tentando reconectar...")
    client.is_connected_flag = False

def setup_mqtt():
    mqtt_client.is_connected_flag = False
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    try:
        mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"Iniciando conexão com MQTT Broker em {MQTT_BROKER_HOST}:{MQTT_PORT}...")
    except Exception as e:
        print(f"ERRO CRÍTICO ao iniciar MQTT: {e}")

# --- Comunicação com Atuadores (via MQTT) ---
def send_light_commands(commands):
    """Espera a conexão MQTT estar ativa e então publica os comandos."""
    # Espera até 5 segundos pela flag de conexão.
    timeout = 5
    start_time = time.time()
    while not mqtt_client.is_connected_flag and time.time() - start_time < timeout:
        print("Aguardando conexão MQTT...")
        time.sleep(0.5)

    if not mqtt_client.is_connected_flag:
        print("FALHA CRÍTICA: Conexão MQTT não estabelecida a tempo. Comandos não enviados.")
        return False
    
    print(f"Processando comandos de luz recebidos do frontend: {commands}")
    
    for command in commands:
        try:
            parts = command.split('_')
            rua_part = parts[0]
            light_command = "_".join(parts[1:])
            
            rua_id = int(re.findall(r'\d+', rua_part)[0])

            # AQUI ESTÁ A LÓGICA DE SEGURANÇA:
            # Só publica no tópico se a rua existir fisicamente.
            if rua_id <= TOTAL_RUAS_FISICAS:
                topic = f"visuhall/rua/{rua_id}/commands"
                mqtt_client.publish(topic, light_command)
                print(f"Publicado no tópico '{topic}': '{light_command}'")
            else:
                # Ignora silenciosamente o comando para ruas inexistentes.
                # Opcional: logar que foi ignorado, se necessário para debug.
                print(f"Comando '{command}' ignorado: Rua {rua_id} não possui atuador físico.")

        except (IndexError, ValueError) as e:
            print(f"Erro ao processar o comando '{command}': {e}")
            
    return True

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

# Rota para o frontend obter a lista de um pedido.
# Não envia mais comandos de luz, apenas retorna os dados.
@app.route('/api/picking_orders/<int:order_id>', methods=['GET'])
def get_picking_order(order_id: int):
    db = SessionLocal()
    try:
        order = db.query(PickingOrder).filter(PickingOrder.id == order_id).first()
        if not order:
            return jsonify({"error": "Ordem de picking não encontrada"}), 404
        
        order.items = sort_picking_list(order.items)
        items_data = [{
            "id": item.id, "product_sku": item.product.sku,
            "product_name": item.product.name, "quantity": item.quantity,
            "status": item.status, "location": item.location.get_address_str() if item.location else "N/A",
            "rua": item.location.rua if item.location else None
        } for item in order.items]
            
        return jsonify({
            "id": order.id, "status": order.status, "items": items_data
        })
    finally:
        db.close()

TOTAL_RUAS = 2 # O número de ruas físicas com ESPs.

# Rota para o frontend enviar comandos de luz.
# Renomeada para clareza. Apenas executa.
@app.route('/api/lights/commands', methods=['POST'])
def light_commands():
    data = request.get_json()
    commands = data.get('commands', [])
    if not isinstance(commands, list):
        return jsonify({"error": "Formato de comandos inválido. Esperava uma lista."}), 400

    # Apenas repassa os comandos para a função de envio,
    # que agora tem a lógica de segurança.
    send_light_commands(commands)
    
    return jsonify({"message": "Comandos processados."})

@app.route('/api/arduino/reset', methods=['POST'])
def light_reset():
    # Desliga apenas as ruas que realmente existem.
    reset_commands = [f"S{i}_OFF" for i in range(1, TOTAL_RUAS_FISICAS + 1)]
    send_light_commands(reset_commands)
    return jsonify({"message": "Comandos de reset enviados para todas as ruas físicas."})


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

# Rota para o frontend atualizar o status de um item no DB.
# Não envia mais comandos de luz. Apenas salva no banco.
@app.route('/api/order_items/<int:item_id>/<status>', methods=['PUT'])
def update_item_status(item_id: int, status: str):
    db = SessionLocal()
    try:
        if status not in ['picked', 'skipped']:
            return jsonify({"error": "Status inválido"}), 400

        item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not item: return jsonify({"error": "Item não encontrado"}), 404

        item.status = status
        db.commit()

        return jsonify({"message": f"Item {item_id} marcado como {status}."})
    finally:
        db.close()

if __name__ == '__main__':
    setup_mqtt() # Inicia a conexão MQTT ao iniciar o servidor
    app.run(host='0.0.0.0', port=8000, debug=True)
else:
    # Quando rodando com Gunicorn, a conexão deve ser iniciada aqui
    setup_mqtt() 