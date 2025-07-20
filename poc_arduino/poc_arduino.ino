// Mapeamento dos pinos
const int greenLedPins[] = {2, 3, 4, 5, 6};
const int yellowLedPins[] = {7, 8, 9, 10, 11};
const int numSectors = 5;

// Variáveis para a lógica de piscar (non-blocking)
unsigned long previousMillis[numSectors];
bool blinkingState[numSectors];
bool isBlinking[numSectors];
const long interval = 500; // Intervalo do pisca-pisca em ms

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);
  inputString.reserve(20);

  for (int i = 0; i < numSectors; i++) {
    pinMode(greenLedPins[i], OUTPUT);
    digitalWrite(greenLedPins[i], LOW);
    pinMode(yellowLedPins[i], OUTPUT);
    digitalWrite(yellowLedPins[i], LOW);
    isBlinking[i] = false; // Inicializa todos como não piscando
    blinkingState[i] = LOW;
    previousMillis[i] = 0;
  }
}

void loop() {
  // Lógica de comunicação serial
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Lógica para fazer os LEDs piscarem
  unsigned long currentMillis = millis();
  for (int i = 0; i < numSectors; i++) {
    if (isBlinking[i] && (currentMillis - previousMillis[i] >= interval)) {
      previousMillis[i] = currentMillis;
      blinkingState[i] = !blinkingState[i]; // Inverte o estado
      digitalWrite(greenLedPins[i], blinkingState[i]);
    }
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

void processCommand(String command) {
  command.trim();

  // Formato: S<setor>_<cor>_<estado> (ON, OFF, BLINK)
  int sectorIndex = command.charAt(1) - '1';
  if (sectorIndex < 0 || sectorIndex >= numSectors) return;

  int pinToControl = -1;
  bool isGreen = false;

  if (command.indexOf("GREEN") > 0) {
    pinToControl = greenLedPins[sectorIndex];
    isGreen = true;
  } else if (command.indexOf("YELLOW") > 0) {
    pinToControl = yellowLedPins[sectorIndex];
  }

  if (pinToControl == -1) return;

  if (command.endsWith("_BLINK") && isGreen) {
    isBlinking[sectorIndex] = true;
  } else if (command.endsWith("_ON")) {
    if(isGreen) isBlinking[sectorIndex] = false;
    digitalWrite(pinToControl, HIGH);
  } else if (command.endsWith("_OFF")) {
    if(isGreen) isBlinking[sectorIndex] = false;
    digitalWrite(pinToControl, LOW);
  }
} 