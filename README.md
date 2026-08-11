# Roflo Pinterest Wallpaper

Тихо ставит случайную (ещё не показанную) картинку из твоей ленты/досок
Pinterest на рабочий стол Windows. Каждая картинка используется один раз
за цикл — без повторов, пока пул не исчерпается.

## Готовый .exe (без Python)

Не хочешь ставить Python и зависимости — скачай `RofloPinterest.exe` со
[страницы релизов](https://github.com/flexeykinDev/roflo-pinterest/releases)
и просто запусти его. Это трей-приложение "всё в одном":

1. Запусти `RofloPinterest.exe` — появится иконка в трее.
2. Правый клик по иконке → **"Войти в Pinterest"** — откроется браузер,
   залогинься, вернись и нажми ОК в диалоговом окне.
3. Правый клик → **"Обновить пул (scraper)"** — соберёт картинки из ленты
   (первый раз может занять пару минут — докачивается браузер Chromium,
   ~150 МБ, один раз).
4. Клик по иконке (или через меню) → **"Новые обои"** — ставит картинку.

Данные (сессия, кэш, лог) хранятся в `%LOCALAPPDATA%\RofloPinterest`.
Чтобы приложение запускалось при входе в Windows — просто закинь ярлык
на `RofloPinterest.exe` в папку автозагрузки
(`Win+R` → `shell:startup`).

Собрать .exe самому: `python scripts/build_exe.py` (см. [Сборка .exe](#сборка-exe)).

## Установка (из исходников, для разработки)

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

Иконка в трее: клик — новые обои, правый клик — меню (войти в Pinterest /
обновить пул / выход). Это то же самое меню, что и в готовом `.exe`.

## Сборка .exe

```powershell
.\venv\Scripts\Activate.ps1
pip install pyinstaller
python scripts/build_exe.py
```

Собирает `dist/RofloPinterest.exe` — трей-приложение (`tray.py`) в
режиме `--onefile --windowed`, с вкомпиленным Playwright-драйвером
(`--collect-all playwright`), так что конечному пользователю не нужен
ни Python, ни `pip install -r requirements.txt`. Браузер Chromium
(~150 МБ) в exe не зашит — его при первом запуске докачивает
`browser_setup.py` (то же самое, что делает `playwright install
chromium`), поэтому размер exe остаётся разумным (~60 МБ).

Иконка exe генерируется скриптом `scripts/make_icon.py` в
`assets/roflo.ico` из того же глифа, что рисует `tray.py` — перегенерь
его, если поменяешь дизайн иконки.

## Файлы проекта

| Файл | Назначение |
|---|---|
| `config.py` | все настройки в одном месте (в `.exe`-сборке данные хранятся в `%LOCALAPPDATA%\RofloPinterest`) |
| `cache.py` | пул URL картинок: добавление, устаревание, "использовано" |
| `wallpaper.py` | скачивание с валидацией + ретраями, установка обоев |
| `scraper.py` | сбор новых картинок через Playwright (медленный, запускать по расписанию) |
| `browser_setup.py` | докачивает Chromium для Playwright при первом запуске (нужно и для `.exe`) |
| `main.py` / `main_silent.pyw` | быстрая установка обоев из уже собранного кэша |
| `login.py` | сохранение сессии Pinterest (через терминал или, из трея, через диалоговое окно) |
| `tray.py` | иконка в трее — основная точка входа для `.exe` |
| `setup_task.py` | регистрация задач в Планировщике Windows |
| `scripts/build_exe.py` | сборка `RofloPinterest.exe` (PyInstaller) |
| `scripts/make_icon.py` | генерация `assets/roflo.ico` |

## Как работает пул без повторов

`pins_cache.json` хранит `{url: {added, used}}`. `main.py` берёт случайный
URL с `used: false`, скачивает, ставит, помечает `used: true`. Когда
неиспользованных не остаётся — пул автоматически сбрасывается (все снова
`false`) и цикл начинается заново. `scraper.py` добавляет новые URL, не
трогая уже отмеченные, и чистит записи старше `MAX_AGE_DAYS`, которые так
и не были показаны.

## Где хранятся данные

### Если используешь `.exe`

Всё — в одной папке: `%LOCALAPPDATA%\RofloPinterest\`
(то есть `C:\Users\<имя>\AppData\Local\RofloPinterest\`):

| Файл / папка | Что это |
|---|---|
| `pinterest_auth.json` | сессия/куки Pinterest — ключ от твоего аккаунта, храни как пароль |
| `pins_cache.json` | пул картинок: что ещё не показано, что уже показано |
| `roflo.log` (+ `roflo.log.1`, `.2`, `.3`) | лог работы и ошибок, с ротацией |
| `browsers\` | скачанный для Playwright Chromium (~150–300 МБ) |

### Если используешь исходники (venv)

`pinterest_auth.json`, `pins_cache.json`, `roflo.log` лежат прямо в
папке проекта, рядом с `main.py` (см. `config.py`). Chromium для
Playwright ставится не сюда, а в общий кэш `%LOCALAPPDATA%\ms-playwright\`
— он используется всеми Playwright-проектами на машине, не только этим.

## Как очистить / удалить

**Если используешь `.exe`:**

1. Выйди из приложения (правый клик по трею → «Выход»).
2. Удали `RofloPinterest.exe`.
3. Удали папку с данными — сотрёт сессию, кэш, лог и скачанный Chromium,
   после этого от программы на компьютере ничего не останется:
   ```powershell
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\RofloPinterest"
   ```
4. Если добавлял ярлык в автозагрузку (`Win+R` → `shell:startup`) —
   удали и его оттуда.

Не обязательно удалять всё: чтобы просто разлогиниться, удали только
`pinterest_auth.json` (при следующем запуске зайди заново через «Войти
в Pinterest»); чтобы сбросить историю показанных картинок и собрать
пул заново — удали только `pins_cache.json`.

**Если используешь исходники:**

1. Останови иконку трея / процесс.
2. Если регистрировал задачи через `setup_task.py` — удали их:
   ```powershell
   schtasks /Delete /TN RofloPinterestScraper /F
   schtasks /Delete /TN RofloPinterestWallpaper /F
   ```
3. Удали `pinterest_auth.json`, `pins_cache.json`, `roflo.log*` (или
   всю папку проекта).
4. Удали `venv\` — уберёт все Python-зависимости этого проекта.
5. (Опционально) `%LOCALAPPDATA%\ms-playwright\` — общий кэш браузеров
   Playwright, используется и другими проектами на машине, если такие
   есть; удаляй, только если он больше не нужен нигде:
   ```powershell
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\ms-playwright"
   ```

Сама картинка обоев, которая уже стоит на рабочем столе, ни от кого не
зависит — она лежит во временной папке Windows (`%TEMP%\pin_wallpaper.*`)
и убирается штатной чисткой временных файлов.

## Приватность

`pinterest_auth.json`, `pins_cache.json`, `roflo.log` — не коммить, они
уже в `.gitignore`. `pinterest_auth.json` — это ключ от твоей сессии,
не пересылай его никому.
