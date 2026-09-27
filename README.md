# IUVO RS-232 dla Home Assistant

<p align="center">
  <a href="https://buycoffee.to/homeon">
    <img src="https://img.shields.io/badge/BuyCoffee-Wesprzyj%20HomeOn-F6C344?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Wesprzyj HomeOn przez BuyCoffee">
  </a>
</p>

Lokalna integracja sterowników **IUVO** z Home Assistant przez port RS-232. Odczytuje stany modułów oraz udostępnia wyjścia, lampki i rolety jako encje Home Assistant. Komunikacja działa z prędkością **115200 baud, 8N1**; komendy tekstowe kończą się `CR LF`.

Aktualna wersja w `manifest.json`: **0.1.10**. To integracja rozwijana i testowana na rzeczywistej instalacji. Przed użyciem sterowania roletami i bramami sprawdź przypisanie kanałów do fizycznych urządzeń.

## Obsługiwane funkcje

- Wykrywanie modułów pod adresami 1–32 (limit można zmienić w opcjach).
- Wyjścia przekaźnikowe jako `switch`, lampki jako `light`, rolety jako `cover`.
- Dwa skonfigurowane wyjścia bramowe jako przyciski chwilowe `button`: moduł 1 / wyjście 5 oraz moduł 2 / wyjście 6. Impuls trwa 0,7 s.
- Wejścia są udostępniane jako `binary_sensor`; można je ukryć w interfejsie, jeśli nie są potrzebne.
- Przycisk ponownego wykrycia modułów i czujnik czasu ostatniej odpowiedzi.
- Odczyt stanów cyklicznie co **5 sekund** domyślnie; zakres ustawienia to 2–60 sekund. Po wysłaniu komendy integracja żąda dodatkowego odświeżenia. Zmiana fizycznego przycisku będzie więc zwykle widoczna przy następnym odczycie, zależnie od czasu odpowiedzi magistrali.
- Usługi `iuvo.rescan` i `iuvo.send_command` do diagnostyki. Komendy rozpoczynające się od `AT+key=` i `AT+Save=` są blokowane.

Integracja rozpoznaje typ modułu z odpowiedzi magistrali. Encje rolet powstają dla modułów typu **Roller Shutter**; przekaźniki i lampki dla pozostałych modułów. Nazwy części kanałów i dwa wyjścia bramowe są obecnie zapisane w `custom_components/iuvo/project_profile.py` dla projektu Knop. Nazwy encji można dostosować w Home Assistant.

## Wymagany sprzęt

- Home Assistant z dostępem do portu szeregowego, np. Raspberry Pi z Home Assistant OS.
- Izolowany konwerter USB–RS232 i odpowiedni przewód do systemu IUVO.

Nie podłączaj RS-232 bezpośrednio do GPIO Raspberry Pi: poziomy napięć są niezgodne.

## Instalacja i konfiguracja

1. W HACS otwórz **Integracje → menu → Repozytoria niestandardowe**.
2. Dodaj `https://github.com/maleikap/home-assistant-iuvo` jako typ **Integracja**.
3. Zainstaluj **IUVO RS-232** i uruchom ponownie Home Assistant.
4. Wybierz **Ustawienia → Urządzenia i usługi → Dodaj integrację → IUVO RS-232**.
5. Wpisz ścieżkę portu szeregowego; stabilna ścieżka `/dev/serial/by-id/...` jest lepsza niż `/dev/ttyUSB0`. Ustaw limit skanowanych modułów (domyślnie 32).

W **Opcjach** integracji można zmienić limit modułów (1–32), odstęp odczytu (2–60 s, domyślnie 5 s) i limit czasu odpowiedzi (0,1–3 s, domyślnie 0,35 s). Zmiana opcji przeładowuje integrację.

## Pierwszy test

1. Sprawdź wykryte moduły oraz encje `Ostatnia odpowiedź`.
2. Użyj jednego zwykłego wyjścia i potwierdź zmianę na urządzeniu oraz w Home Assistant.
3. Testuj roletę przy fizycznym nadzorze, sprawdzając osobno otwieranie, zamykanie i zatrzymanie.
4. Dla bramy użyj przycisku chwilowego tylko po sprawdzeniu właściwego modułu i kanału.

Stan rolety w protokole nie podaje potwierdzonej pozycji procentowej, dlatego integracja udostępnia otwieranie, zamykanie i zatrzymanie bez suwaka procentowego. Wyjścia `switch` używają komendy przełączającej i przed zmianą sprawdzają ostatni odczyt stanu; przy opóźnionym lub błędnym odczycie trzeba zweryfikować stan fizyczny.

## Diagnostyka

Odczyt stanów całej magistrali używa komend `AT+StanOut=0`, `AT+StanIn=0`, `AT+StanLamp=0` i `AT+StanRol=0`. Usługę `iuvo.rescan` można wywołać po zmianie połączenia modułów. Usługa `iuvo.send_command` służy do świadomej diagnostyki; nie należy używać jej do programowania pamięci modułów.

## Ważne

Projekt nie jest produktem firmy IUVO ani oficjalnie przez nią wspieraną integracją. Zrób kopię projektu w IUVO Expert przed pracami przy instalacji. Ta integracja dotyczy wyłącznie IUVO; wideodomofon Dahua VTO jest osobną integracją Home Assistant.

Rozwój projektu możesz wesprzeć przez [BuyCoffee](https://buycoffee.to/homeon).
