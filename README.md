# IUVO RS-232 dla Home Assistant

<p align="center"><a href="https://buycoffee.to/homeon"><img src="https://img.shields.io/badge/BuyCoffee-Wesprzyj%20HomeOn-F6C344?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Wesprzyj HomeOn przez BuyCoffee"></a></p>

Integracja sterowników **IUVO** z Home Assistant przez RS-232. Aktualna wersja: **0.2.0**.

## Funkcje

- wykrywanie do 32 adresów modułów;
- przekaźniki jako `switch`, lampki jako `light`, rolety jako `cover`;
- wyjścia chwilowe, np. bramy, jako `button`;
- osobny profil nazw i ról dla każdej instalacji.

## Instalacja

Dodaj `https://github.com/maleikap/home-assistant-iuvo` w HACS jako repozytorium niestandardowe typu **Integracja**. Po instalacji uruchom ponownie Home Assistant i wybierz stabilną ścieżkę portu `/dev/serial/by-id/...`.

## Profile klientów

Bez profilu integracja używa neutralnych nazw. Dane konkretnego klienta nie są zapisane w publicznym kodzie. Utwórz np. `/config/iuvo_profile.json`:

```json
{
  "switch_names": {"1": {"1": "Oświetlenie wejścia"}},
  "cover_names": {"5": {"1": "Roleta salon"}},
  "light_names": {},
  "momentary_outputs": {"1:5": {"name": "Brama wjazdowa", "pulse_seconds": 0.7}}
}
```

W opcjach integracji wpisz ścieżkę profilu. Plik znajduje się poza katalogiem integracji, więc HACS go nie nadpisze. Ręcznie nadane nazwy encji zostają zachowane, ponieważ ich unikalne identyfikatory się nie zmieniają.

## Bezpieczeństwo

Nie podłączaj RS-232 bezpośrednio do GPIO Raspberry Pi. Użyj izolowanego konwertera USB–RS232. Komendy programujące `AT+key=` i `AT+Save=` są zablokowane.
