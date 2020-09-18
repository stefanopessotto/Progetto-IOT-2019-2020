# Progetto_IOT_2019-2020
Progetto per il corso di IOT nell'a.a. 2018/2019.
## Traccia del progetto:
1. Progettazione ed implementazione di framework per l'acquisizione di dati da sensori
Progettare e sviluppare in un linguaggio a scelta un software che consenta di acquisire dati da certe tipologie di sensori e/o canali predefiniti.
Ad esempio:
- da porte seriali;
- da sensori di temperatura/umidità (e.g., DHT11, DHT22 ecc.);
- da IMU (Inertial Measurement Unit);
- da sensori PIR (i.e., sensori di tipo Passive InfraRed);
- LIDAR;
...
Il numero di sensori e la loro tipologia devono essere specificabili mediante file di configurazione, letti al momento dell'avvio del software. Ai fini del progetto da presentare all'esame è sufficiente implementare tre tipologie, predisponendo l'architettura software in modo che sia estendibile rispetto a nuovi sensori.
Tutte le letture devono essere concorrenti, possibilmente con frequenze diverse e non devono ostacolarsi fra loro. Il servizio di lettura deve essere robusto e non fermarsi di fronte ad errori come la chiusura inattesa di un canale di comunicazione.
