/*
  Lecteur RFID de la Salle N377 — Arduino Nano 33 IoT + RC522
  Lit l'UID d'une carte, le soumet à l'API Django (POST /api/acces/)
  puis ouvre la gâche (servomoteur) si la réponse est 200.

  Bibliothèques (Gestionnaire de bibliothèques) :
    WiFiNINA, ArduinoHttpClient, MFRC522 (GithubCommunity), Servo

  Branchements (RC522 en 3,3 V uniquement) :
    RC522 SDA -> D10   SCK -> D13   MOSI -> D11   MISO -> D12
    RC522 RST -> D9    3.3V -> 3.3V GND -> GND
    Servo signal -> D3 (alimentation 5 V externe, GND commun)
    DEL verte -> D5    DEL rouge -> D6   Avertisseur -> D7 (avec résistances)
*/
#include <SPI.h>
#include <MFRC522.h>
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <Servo.h>
#include "arduino_secrets.h"

const int PIN_SS = 10, PIN_RST = 9, PIN_SERVO = 3;
const int PIN_VERT = 5, PIN_ROUGE = 6, PIN_BUZZER = 7;
const int ANGLE_FERME = 0, ANGLE_OUVERT = 90;

MFRC522 rfid(PIN_SS, PIN_RST);
WiFiClient wifi;
HttpClient http(wifi, SERVEUR_IP, SERVEUR_PORT);
Servo gache;

void connecterWifi() {
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connexion Wi-Fi a ");
    Serial.println(SECRET_SSID);
    WiFi.begin(SECRET_SSID, SECRET_PASS);
    delay(5000);
  }
  Serial.print("Connecte, IP : ");
  Serial.println(WiFi.localIP());
}

// Transforme l'UID lu (4 ou 7 octets) en texte hexadecimal : "A35F129C"
String lireUid() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

void signaler(int pin, int bips) {
  for (int i = 0; i < bips; i++) {
    digitalWrite(pin, HIGH);
    tone(PIN_BUZZER, pin == PIN_VERT ? 2000 : 400, 150);
    delay(250);
    digitalWrite(pin, LOW);
    delay(100);
  }
}

// Envoie l'UID au serveur. Retourne la duree d'ouverture en secondes (0 = refuse).
int demanderAcces(const String& uid) {
  String corps = "{\"porte\":" + String(PORTE_ID) + ",\"uid\":\"" + uid + "\"}";
  http.beginRequest();
  http.post("/api/acces/");
  http.sendHeader("Content-Type", "application/json");
  http.sendHeader("Content-Length", corps.length());
  http.sendHeader("Authorization", String("Token ") + SECRET_JETON);
  http.beginBody();
  http.print(corps);
  http.endRequest();

  int statut = http.responseStatusCode();
  String reponse = http.responseBody();
  Serial.print("HTTP ");
  Serial.print(statut);
  Serial.print(" : ");
  Serial.println(reponse);

  if (statut != 200) return 0;
  // Lecture simple de "ouvrir_secondes": N dans la reponse JSON
  int pos = reponse.indexOf("\"ouvrir_secondes\":");
  return pos < 0 ? 5 : reponse.substring(pos + 18).toInt();
}

void setup() {
  Serial.begin(9600);
  pinMode(PIN_VERT, OUTPUT);
  pinMode(PIN_ROUGE, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  gache.attach(PIN_SERVO);
  gache.write(ANGLE_FERME);
  SPI.begin();
  rfid.PCD_Init();
  connecterWifi();
  Serial.println("Presentez un badge...");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connecterWifi();
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  String uid = lireUid();
  Serial.print("Badge lu : ");
  Serial.println(uid);

  int secondes = demanderAcces(uid);
  if (secondes > 0) {
    signaler(PIN_VERT, 1);
    gache.write(ANGLE_OUVERT);        // ouverture
    delay(secondes * 1000UL);
    gache.write(ANGLE_FERME);         // refermeture automatique
  } else {
    signaler(PIN_ROUGE, 3);           // refus : 3 bips graves
  }
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000);                        // evite les lectures en double
}
