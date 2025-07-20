// Pinos dos LEDs
const int ledVerdePin = 8;
const int ledAmareloPin = 9;
const int ledVermelhoPin = 10;

void setup() {
  // Inicia a comunicação serial a 9600 bps
  Serial.begin(9600);

  // Define os pinos dos LEDs como saída
  pinMode(ledVerdePin, OUTPUT);
  pinMode(ledAmareloPin, OUTPUT);
  pinMode(ledVermelhoPin, OUTPUT);

  // Garante que todos os LEDs comecem desligados
  digitalWrite(ledVerdePin, LOW);
  digitalWrite(ledAmareloPin, LOW);
  digitalWrite(ledVermelhoPin, LOW);
}

void loop() {
  // Verifica se há dados disponíveis na porta serial
  if (Serial.available() > 0) {
    // Lê o caractere recebido
    char command = Serial.read();

    // Tira o LED do pino especificado do estado HIGH por 5 segundos
    switch (command) {
      case '1': // Comando para acender o LED verde
        digitalWrite(ledVerdePin, HIGH);
        delay(5000);
        digitalWrite(ledVerdePin, LOW);
        break;
      case '2': // Comando para acender o LED amarelo
        digitalWrite(ledAmareloPin, HIGH);
        delay(5000);
        digitalWrite(ledAmareloPin, LOW);
        break;
      case '3': // Comando para acender o LED vermelho
        digitalWrite(ledVermelhoPin, HIGH);
        delay(5000);
        digitalWrite(ledVermelhoPin, LOW);
        break;
    }
  }
} 