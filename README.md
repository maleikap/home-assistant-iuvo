# IUVO RS-232 for Home Assistant

Lokalna integracja systemu automatyki **IUVO** z Home Assistantem przez RS-232.

Projekt powstał na podstawie analizy programu IUVO Expert 2.23. Komunikacja jest
tekstowa, pracuje z prędkością **115200 baud, 8N1**, a komendy są zakończone
znakami `CR LF`.

## Stan projektu

Wersja `0.1.0` jest wersją terenową do pierwszego testu z prawdziwą instalacją.
Odczyt stanów i wykrywanie modułów są bezpieczne (tylko odczyt). Programowanie
pamięci modułów jest celowo zablokowane do czasu potwierdzenia protokołu.

## Funkcje

- automatyczne wykrywanie do 32 adresów modułów;
- obsługa `IUVO Controller0806`, `Controller0806T/RTC` i `Roller Shutter0804`;
- wejścia jako `binary_sensor`;
- wyjścia jako `switch`;
- lampki jako `light`;
- rolety jako `cover`;
- diagnostyka ostatniej odpowiedzi;
- konfiguracja portu i parametrów odpytywania z interfejsu HA;
- bezpieczna usługa diagnostyczna do wysyłania komend AT;
- blokada komend `AT+key` i `AT+Save`.

## Sprzęt

- Raspberry Pi z Home Assistant OS;
- izolowany konwerter USB–RS232 (zalecany FTDI);
- odpowiedni przewód RS-232 do systemu IUVO.

Nie podłączaj RS-232 bezpośrednio do GPIO Raspberry Pi. Poziomy napięć są
niezgodne i mogą uszkodzić komputer.

## Instalacja przez HACS

1. HACS → Integracje → trzy kropki → Repozytoria niestandardowe.
2. Dodaj `https://github.com/maleikap/home-assistant-iuvo` jako Integrację.
3. Zainstaluj **IUVO RS-232** i uruchom ponownie Home Assistanta.
4. Ustawienia → Urządzenia i usługi → Dodaj integrację → IUVO RS-232.
5. Podaj stabilną ścieżkę portu, najlepiej `/dev/serial/by-id/...`.

## Bezpieczny pierwszy test

1. Przed podłączeniem wykonaj kopię obecnego projektu w IUVO Expert.
2. Dodaj integrację z limitem 32 modułów.
3. Sprawdź logi i encje diagnostyczne.
4. Najpierw testuj jedno światło, później jedną roletę.
5. Nie używaj usługi `send_command` do programowania modułów.

## Znane komendy

```text
AT+StanOut=1
AT+StanIn=1
AT+StanLamp=1
AT+StanRol=1
AT+SetOut=1,3,0,0,0,0,0
AT+SetLamp=1,1,0,0,0,0,0,0,0
AT+SetRol=1,30,1,0,0,0
```

## Plan rozwoju

- potwierdzenie formatów odpowiedzi na instalacji;
- edycja nazw kanałów z panelu integracji;
- kopia i odtworzenie konfiguracji modułów;
- bezpieczne odtworzenie funkcji IUVO Expert w Home Assistant;
- import dotychczasowych projektów XML.

## Ważne

Integracja nie jest produktem firmy IUVO i nie jest przez nią wspierana.
Programowanie modułów przed testami terenowymi może zmienić logikę wejść,
wyjść lub rolet.
