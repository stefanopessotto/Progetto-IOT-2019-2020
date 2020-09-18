int i;
int potentiometer = a5;
int value;

void setup() {
  // put your setup code here, to run once:
  serial.begin(9600);
  value = 0;
}

void loop() {
  // put your main code here, to run repeatedly:
  value = analogread(potentiometer);
  serial.print("{\"potentiometer\": ");
  serial.print(value);
  serial.println("}");
  delay(1000);
}
