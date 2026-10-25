#include <Wire.h>
#include <MPU6050.h>
#include <Servo.h>

Servo servo;
MPU6050 mpu;

const int GREEN_LED = 4; // Green LED for Access Granted (Pin 4)[cite: 4]
const int RED_LED = 3;   // Red LED for Access Denied (Pin 3)[cite: 4]
const int SERVO_PIN = 9; // Servo motor (Pin 9)[cite: 4]

void setup() {
  Serial.begin(9600);
  Wire.begin();
  mpu.initialize();
  
  servo.attach(SERVO_PIN);
  servo.write(90); // Default locked position (90°)
  
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  
  // Default state: Locked (Red LED ON, Green LED OFF)[cite: 4]
  digitalWrite(RED_LED, HIGH);
  digitalWrite(GREEN_LED, LOW);
}

void loop() {
  // 1. Continuous stream of MPU6050 accelerometer data
  int ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  
  Serial.print("MPU:");
  Serial.print(ax); Serial.print(",");
  Serial.print(ay); Serial.print(",");
  Serial.println(az);
  
  // 2. Read commands from Python ('A' = Access Granted, 'D' = Access Denied)[cite: 5]
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'A') {
      servo.write(180);              // Unlock servo (180°)[cite: 5]
      digitalWrite(GREEN_LED, HIGH); // Turn ON Green LED[cite: 5]
      digitalWrite(RED_LED, LOW);    // Turn OFF Red LED
    } else if (cmd == 'D') {
      servo.write(90);               // Lock servo (90°)[cite: 5]
      digitalWrite(GREEN_LED, LOW);  // Turn OFF Green LED[cite: 5]
      digitalWrite(RED_LED, HIGH);   // Turn ON Red LED[cite: 5]
    }
  }
  
  delay(100);
}
