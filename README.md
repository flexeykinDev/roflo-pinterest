# Roflo Pinterest Wallpaper

Тихо ставит случайную (ещё не показанную) картинку из твоей ленты/досок
Pinterest на рабочий стол Windows. Каждая картинка используется один раз
за цикл — без повторов, пока пул не исчерпается.

## Установка

```powershell
py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
# если ругается на execution policy:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

pip install -r requirements.txt
playwright install chromium
```

## Первый запуск

1. **Авторизация** (один раз, пока не истечёт сессия):
   ```powershell
   python login.py
   ```
   Откроется браузер — залогинься в Pinterest, вернись в терминал, нажми Enter.

2. **(Опционально)** Впиши свои доски в `config.py` → `BOARD_URLS`,
   если хочешь скрапить не только ленту, а конкретные доски.

3. **Собери первый пул картинок**:
   ```powershell
   python scraper.py
   ```

4. **Поставь обои**:
   ```powershell
   python main.py
   ```

## Тихий (silent) запуск

Используй `main_silent.pyw` — двойной клик или `pythonw.exe main_silent.pyw`
запустит без окна консоли. Ошибки пишутся в `roflo.log`, а не в консоль.

## Автоматизация

```powershell
python setup_task.py                 # ежедневный scraper в 09:00
python setup_task.py --with-logon    # + новые обои при каждом входе в систему
```

Задачи создаются через `schtasks`, ничего кликать в GUI не нужно.
Удалить: `schtasks /Delete /TN RofloPinterestScraper /F` (аналогично для второй).

## Трей-иконка (опционально)

```powershell
pythonw.exe tray.py
```

Иконка в трее: клик — новые обои, правый клик — меню (обновить пул / выход).

## Файлы проекта

| Файл | Назначение |
|---|---|
| `config.py` | все настройки в одном месте |
| `cache.py` | пул URL картинок: добавление, устаревание, "использовано" |
| `wallpaper.py` | скачивание с валидацией + ретраями, установка обоев |
| `scraper.py` | сбор новых картинок через Playwright (медленный, запускать по расписанию) |
| `main.py` / `main_silent.pyw` | быстрая установка обоев из уже собранного кэша |
| `login.py` | одноразовое сохранение сессии Pinterest |
| `tray.py` | иконка в трее (опционально) |
| `setup_task.py` | регистрация задач в Планировщике Windows |

## Как работает пул без повторов

`pins_cache.json` хранит `{url: {added, used}}`. `main.py` берёт случайный
URL с `used: false`, скачивает, ставит, помечает `used: true`. Когда
неиспользованных не остаётся — пул автоматически сбрасывается (все снова
`false`) и цикл начинается заново. `scraper.py` добавляет новые URL, не
трогая уже отмеченные, и чистит записи старше `MAX_AGE_DAYS`, которые так
и не были показаны.

## Приватность

`pinterest_auth.json`, `pins_cache.json`, `roflo.log` — не коммить, они
уже в `.gitignore`. `pinterest_auth.json` — это ключ от твоей сессии,
не пересылай его никому.
