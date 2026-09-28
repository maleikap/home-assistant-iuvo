# IUVO RS-232 dla Home Assistant

<p align="center">
  <a href="https://buycoffee.to/homeon"><img src="https://img.shields.io/badge/BuyCoffee-Wesprzyj%20HomeOn-F6C344?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Wesprzyj HomeOn przez BuyCoffee"></a>
</p>

Integracja sterowników **IUVO** z Home Assistant przez RS-232. Komunikacja: **115200 baud, 8N1**, komendy zakończone CR LF.

Aktualna wersja: **0.2.0**.

## Funkcje

- wykrywanie do 32 adresów modułów;
- przekaźniki jako `switch`, lampki jako `light`, rolety jako `cover`;
- opcjonalne wyjścia chwilowe (np. bramy) jako `button`;
- osobne profile nazw i ról dla każdej instalacji;
- usługi `iuvo.rescan` i `iuvo.send_command`.

## Instalacja przez HACS

1. HACS → Integracje → Repozytoria niestandardowe.
2. Dodaj `https://github.com/maleikap/home-assistant-iuvo` jako Integrację.
3. Zainstaluj IUVO RS-232 i uruchom ponownie Home Assistant.
4. Dodaj integrację i wybierz stabilny port `/dev/serial/by-id/...`.

## Profile klientów

Bez profilu integracja tworzy neutralne nazwy, np. `Wyjście 1` i `Roleta 1`. Dane klienta nie są zapisane w kodzie integracji.

Utwórz plik, np. `/config/iuvo_profile.json`:

```json
{
  "switch_names": {"1": {"1": "Oświetlenie wejścia"}},
  "cover_names": {"5": {"1": "Roleta salon"}},
  "light_names": {},
  "momentary_outputs": {
    "1:5": {"name": "Brama wjazdowa", "pulse_seconds": 0.7}
  }
}
```

Następnie otwórz **Ustawienia → Urządzenia i usługi → IUVO RS-232 → Konfiguruj** i wpisz ścieżkę profilu. Plik leży poza katalogiem integracji, więc aktualizacja HACS go nie nadpisze. Ręczne nazwy encji w Home Assistant pozostają zachowane, ponieważ unikalne identyfikatory się nie zmieniają.

## Bezpieczeństwo

Nie podłączaj RS-232 bezpośrednio do GPIO Raspberry Pi. Użyj izolowanego konwertera USB–RS232. Komendy programujące `AT+key=` i `AT+Save=` są zablokowane.
