const int relayPin = 7;  // Pin connected to relay module for LED
const int relayPinWiFi = 12;   // Pin connected to relay module for WiFi handling

void setup() {
  Serial.begin(9600);          // Initialize serial communication at 9600 baud
  pinMode(relayPin, OUTPUT);   // Set the relay pin as an output
  pinMode(relayPinWiFi, OUTPUT);   // Set the relay pin as an output
  digitalWrite(relayPin, LOW); // Turn off relay pin 7 initially (Power not available)
  digitalWrite(relayPinWiFi, LOW); // Turn on relay pin 8 initially (Power available)
}

void loop() {
  if (Serial.available() > 0) {  // Check if there is any data in the serial buffer
    char command = Serial.read(); // Read the incoming byte

    if (command == '1') {         // If the command is '1'
      digitalWrite(relayPin, HIGH); // Turn relay on (connect COM and NO)
      Serial.println("Relay turned ON"); //Power ON
      Serial.println("Light turned ON");
    } else if (command == '0') {   // If the command is '0'
      digitalWrite(relayPin, LOW);  // Turn relay off (disconnect COM and NO)
      Serial.println("Relay turned OFF"); //Power OFF
      Serial.println("Light turned OFF");
    } else if (command == '2') {   // If the command is '2'
      digitalWrite(relayPinWiFi, LOW);  // Turn relay off (disconnect COM and NO)
      Serial.println("Relay turned OFF"); //Power ON
      Serial.println("Router turned OFF");
    } else if (command == '3') {   // If the command is '3'
      digitalWrite(relayPinWiFi, HIGH);  // Turn relay on (connect COM and NO)
      Serial.println("Relay turned ON"); //Power OFF
      Serial.println("Router turned ON");
    }
  }
}
