#include <SoftwareSerial.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

#define MQ135_PIN A0

#define LED_VERDE 3
#define LED_AMARILLO 4
#define LED_ROJO 5
#define BUZZER 6

SoftwareSerial BT(7, 8); // RX, TX

unsigned long previousBuzzerMillis = 0;
const long buzzerInterval = 200; // Tiempo entre encendido/apagado del buzzer y LED rojo
bool buzzerState = false;
bool buzzerActive = false;

unsigned long previousSensorMillis = 0;
const long sensorInterval = 2000; // Leer sensores cada 2 segundos

void setup() {
  Serial.begin(9600);
  BT.begin(9600);
  dht.begin();

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_AMARILLO, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_AMARILLO, LOW);
  digitalWrite(LED_ROJO, LOW);
  digitalWrite(BUZZER, LOW);
}

void loop() {
  unsigned long currentMillis = millis();

  // alerta
  if (buzzerActive && (currentMillis - previousBuzzerMillis >= buzzerInterval)) {
    previousBuzzerMillis = currentMillis;
    buzzerState = !buzzerState;
    digitalWrite(BUZZER, buzzerState);
    digitalWrite(LED_ROJO, buzzerState);
  }

  // Lectura de sensores y envío por blutu
  if (currentMillis - previousSensorMillis >= sensorInterval) {
    previousSensorMillis = currentMillis;

    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    int mq135_raw = analogRead(MQ135_PIN);

    String calidad;

    // Reiniciar estado de todo
    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_AMARILLO, LOW);
    digitalWrite(LED_ROJO, LOW);
    digitalWrite(BUZZER, LOW);
    buzzerState = false;
    buzzerActive = false;

    if (mq135_raw < 250) {
      calidad = "Buena";
      digitalWrite(LED_VERDE, HIGH);
    } else if (mq135_raw < 350) {
      calidad = "Moderada";
      digitalWrite(LED_AMARILLO, HIGH);
    } else {
      calidad = "Mala";
      buzzerActive = true; // Activar alerta
      previousBuzzerMillis = currentMillis;
    }

    String datos = "Temp:" + String(temp) +
                   ",Hum:" + String(hum) +
                   ",MQ135:" + String(mq135_raw) +
                   ",Calidad:" + calidad;

    Serial.println(datos);
    BT.println(datos);
  }
}
