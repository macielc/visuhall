#include <WiFi.h>
#include <PubSubClient.h>

// --- Configurações (Preencha com seus dados) ---
const char* WIFI_SSID = "SEU_WIFI_SSID";
const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";
const char* MQTT_BROKER_IP = "192.168.68.135"; // IP do seu Raspberry Pi
const int RUA_ID = 1; // <<-- MUDE PARA 2 NO SEGUNDO ESP32

// --- Constantes do Sistema ---
const int MQTT_PORT = 1883;
#define LED_BUILTIN 2 // A maioria das placas ESP32 usa o pino 2 para o LED embutido

// --- Variáveis Globais ---
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
unsigned long lastMsg = 0;
char msg[50];
int value = 0;

// Variáveis para o controle do LED piscando (sem usar delay)
bool ledBlinking = false;
unsigned long previousMillis = 0;
const long blinkInterval = 500; // Intervalo de 500ms (meio segundo)

// --- Funções de Conexão ---
void setupWifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());
  Serial.println("");
  Serial.println("WiFi conectado!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensagem recebida no tópico [");
  Serial.print(topic);
  Serial.print("] ");
  
  char message[length + 1];
  for (int i = 0; i < length; i++) {
    message[i] = (char)payload[i];
  }
  message[length] = '\0';
  Serial.println(message);

  // Lógica de controle do LED baseada na mensagem
  if (strcmp(message, "GREEN_BLINK") == 0) {
    ledBlinking = true;
  } else if (strcmp(message, "YELLOW_ON") == 0) {
    ledBlinking = false;
    digitalWrite(LED_BUILTIN, HIGH); // Acende o LED
  } else if (strcmp(message, "OFF") == 0) {
    ledBlinking = false;
    digitalWrite(LED_BUILTIN, LOW); // Apaga o LED
  }
}

void reconnect() {
  // Loop até reconectar
  while (!mqttClient.connected()) {
    Serial.print("Tentando conectar ao MQTT Broker...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("conectado!");
      
      // Assina o tópico específico para esta rua
      String topic = "visuhall/rua/" + String(RUA_ID) + "/commands";
      mqttClient.subscribe(topic.c_str());
      Serial.print("Assinado ao tópico: ");
      Serial.println(topic);

    } else {
      Serial.print("falhou, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" tentando novamente em 5 segundos");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); // Começa com o LED desligado
  Serial.begin(115200);
  
  setupWifi();
  mqttClient.setServer(MQTT_BROKER_IP, MQTT_PORT);
  mqttClient.setCallback(callback);
}

void loop() {
  // Verifica o status da conexão Wi-Fi e MQTT e reconecta se necessário
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Conexão WiFi perdida. Tentando reconectar...");
    setupWifi();
  }
  if (!mqttClient.connected()) {
    reconnect();
  }
  
  mqttClient.loop();

  // Lógica para piscar o LED sem bloquear o loop com delay()
  if (ledBlinking) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= blinkInterval) {
      previousMillis = currentMillis;
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN)); // Inverte o estado do LED
    }
  }
} 