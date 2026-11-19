# Спецификация требований — Auto Clicker Pro 1.1.0

Восстановлена по коду коммита `a7140ba` (2026-09-06). Описывает то, что код
делает, а не то, что он должен был бы делать. Каждое требование ссылается на
строку, где оно реализовано, и на тест, который его проверяет, если такой есть.
Сводка по проекту и инструкции по запуску — в [`docs/README.md`](docs/README.md).

<!-- jira-sync:start -->
Jira: KAN-147

## Tasks

This list is one ticket in Jira project KAN, [KAN-147](https://igorsvolohovs.atlassian.net/browse/KAN-147). Each line is a checkbox there: tick it in Jira and the sync ticks it here; add a checkbox there and it is appended here. Done items are the features described in section 3; open items are what the project declares but the code does not do yet.

- [x] Настройки и их проверка (section 3.1) <!-- spec-675d65c086 -->
- [x] Файл пресета (section 3.2) <!-- spec-38e0b8b602 -->
- [x] Решения на каждом клике (section 3.3) <!-- spec-9e3e8078e4 -->
- [x] Окно (section 3.4) <!-- spec-f5988fe08a -->
- [x] Запуск и вспомогательные скрипты проекта (section 3.5) <!-- spec-793b2eb29f -->
- [x] Известные расхождения кода с требованиями (section 3.6) <!-- spec-28fab7690e -->
- [ ] `estimate_run`, `format_duration` (FR-17, FR-18) нигде в `src/` не вызываются; (declared, not implemented) <!-- spec-estimaterun-formatduration-fr-17-fr-18-src -->
- [ ] Захват координат щелчком по окну: (declared, not implemented) <!-- spec-7028347edb -->
- [ ] `hotkeys_to_string` и `self.key_inputs` не используются (`gui.py:190`, (declared, not implemented) <!-- spec-hotkeystostring-self-keyinputs-gui-py-190 -->
- [ ] `README.md`: (declared, not implemented) <!-- spec-readme-md -->
- [ ] `CHANGELOG.md` 1.1.0: (declared, not implemented) <!-- spec-changelog-md-1-1-0 -->
- [ ] `pyproject.toml:15`: (declared, not implemented) <!-- spec-pyproject-toml-15 -->

<!-- jira-sync:end -->

## 1. Назначение и границы

Программа нажимает кнопку мыши с заданным интервалом и параметрами, управляется
из окна PyQt6 и глобальными горячими клавишами, хранит настройки в JSON-пресетах
(`README.md`, `src/autoclicker/gui.py`).

Входит в границы:

- расчёт интервала, точки клика и условия остановки (`src/autoclicker/core.py`);
- модель настроек, их проверка, формат файла пресета (`src/autoclicker/settings.py`);
- окно, поток кликов, поток горячих клавиш, работа с файлами пресетов
  (`src/autoclicker/gui.py`);
- запуск (`run_autoclicker.py`), генерация скриншотов
  (`scripts/capture_usage_screenshots.py`).

Не входит:

- запись и воспроизведение последовательностей действий, клавиатурный ввод,
  распознавание изображения — в коде этого нет;
- сетевое взаимодействие — в коде нет сетевых вызовов;
- общий инструментарий стандарта repo-quality-template (CI, политики веток,
  SBOM) — одно требование FR-31.

## 2. Контекст

| Участник | Роль | Источник |
| --- | --- | --- |
| Пользователь | Задаёт параметры в окне, запускает и останавливает клики, сохраняет пресеты. Читает по-русски | `src/autoclicker/gui.py`, `docs/decisions.md` («Point 12») |
| ОС: мышь | Получает перемещения и нажатия через `pyautogui` | `gui.py:84-96`, `gui.py:363` |
| ОС: клавиатура | Глобальные сочетания через `keyboard.add_hotkey`, перехват снимается `keyboard.unhook_all` | `gui.py:48-52`, `gui.py:185` |
| Файловая система | `configs/*.json`, `last_config.json` в текущем рабочем каталоге | `gui.py:176-177` |

Среда выполнения: Python `>=3.10` (`pyproject.toml:10`), PyQt6, `pyautogui`,
`keyboard` (`pyproject.toml:19`). Готовая сборка выпускается только для Windows
(`.github/workflows/release.yml`); в комментариях там же сказано, что `keyboard`
требует root на Linux, а `pyautogui` — дисплей.

## 3. Функциональные требования

### 3.1 Настройки и их проверка

**FR-1.** Система должна переводить интервал в секунды: при `interval_unit == "s"` значение берётся как секунды, при любом другом — как миллисекунды и делится на 1000.
Источник: `src/autoclicker/settings.py:205-206`. Проверка: `test_seconds_and_milliseconds_are_both_understood`.

**FR-2.** Система должна принимать интервал, число кликов, длительность перетаскивания, координаты и диапазоны разброса только как целые числа (после `strip()`) и при ошибке поднимать `SettingsError` с именем поля.
Источник: `settings.py:191-195`, `settings.py:205`, `settings.py:224-245`. Проверка: `test_a_field_that_is_not_a_number_names_itself`.

**FR-3.** Система должна отклонять подпись кнопки мыши или типа клика, которой нет в таблицах `BUTTON_LABELS` / `CLICK_TYPE_LABELS`, перечисляя допустимые значения.
Источник: `settings.py:42-52`, `settings.py:208-220`. Проверка: `test_an_unknown_label_says_what_was_expected`.

**FR-4.** Система должна игнорировать координаты, смещение и разброс интервала, если соответствующий флаг `*_enabled` выключен (позиция `None`, смещение и разброс `0`).
Источник: `settings.py:222-238`. Проверка: `test_disabled_options_do_not_leak_their_values`.

**FR-5.** Система должна отклонять интервал `<= 0`.
Источник: `settings.py:85-86`. Проверка: `test_a_zero_interval_is_refused`.

**FR-6.** Система должна отклонять отрицательные число кликов, длительность перетаскивания, смещение и разброс интервала.
Источник: `settings.py:87-94`. Проверка: `test_negative_values_are_refused`.

**FR-7.** Система должна отклонять разброс интервала (мс), превышающий сам интервал, и допускать равный ему.
Источник: `settings.py:96-107`. Проверка: `test_jitter_wider_than_the_interval_is_refused_rather_than_clamped`.

**FR-8.** Система должна считать `click_count == 0` запуском без ограничения числа кликов.
Источник: `settings.py:109-111`, `core.py:61-65`. Проверка: `test_a_count_of_zero_never_stops_on_its_own`.

### 3.2 Файл пресета

**FR-9.** Система должна читать пресет как JSON в UTF-8 и отклонять файл, корень которого не объект.
Источник: `settings.py:177-181`. Проверка: `test_a_broken_preset_file_is_reported_not_guessed`.

**FR-10.** Система должна дополнять отсутствующие в файле поля значениями по умолчанию, в том числе `hotkeys` = `F6`/`F7`/`F8`, и приводить значения полей к строкам (флаги — к `bool`).
Источник: `settings.py:57`, `settings.py:133-156`. Проверка: `test_an_old_preset_without_hotkeys_gets_the_defaults`.

**FR-11.** Система должна записывать пресет в UTF-8 с отступом 4, без экранирования не-ASCII символов и с переводом строки в конце.
Источник: `settings.py:158-174`, `settings.py:184-188`. Проверка: `test_a_preset_survives_a_round_trip`.

**FR-12.** Система должна загружать пресет формата v1.0.0, поставляемый в `configs/Dota2Pudge.json`.
Источник: `settings.py:1-15` (docstring), `configs/Dota2Pudge.json`. Проверка: `test_the_preset_that_ships_with_the_repository_still_loads`.

### 3.3 Решения на каждом клике

**FR-13.** Система должна при нулевом разбросе возвращать интервал без изменений.
Источник: `core.py:33-34`. Проверка: `test_without_jitter_the_interval_is_exactly_what_was_asked_for`.

**FR-14.** Система должна при ненулевом разбросе возвращать `interval + uniform(-r, r) / 1000` секунд, но не меньше 0,001 с, используя переданный генератор `random.Random`.
Источник: `core.py:22`, `core.py:36-39`. Проверка: `test_jitter_stays_inside_the_range_it_was_given`, `test_the_same_seed_gives_the_same_sequence`, `test_the_interval_never_goes_below_the_floor`.

**FR-15.** Система должна брать точку клика из фиксированной позиции, а без неё — из переданной точки курсора, и при смещении `n > 0` прибавлять к каждой координате `randint(-n, n)`.
Источник: `core.py:42-58`. Проверка: `test_without_an_offset_the_position_is_left_alone`, `test_without_a_fixed_position_the_cursor_is_the_starting_point`, `test_the_offset_applies_with_or_without_a_fixed_position`, `test_the_offset_can_reach_every_corner_of_its_square`.

**FR-16.** Система должна считать запуск законченным, когда число сделанных кликов `>= click_count` (для ограниченного запуска).
Источник: `core.py:61-65`. Проверка: `test_a_run_stops_on_the_click_it_was_asked_for`.

**FR-17.** Система должна оценивать длительность ограниченного запуска (ожидаемую, минимальную и максимальную, с учётом длительности перетаскивания) и возвращать `None` для неограниченного.
Источник: `core.py:68-99`. Проверка: `test_an_unlimited_run_has_no_estimate`, `test_the_estimate_brackets_the_run`, `test_a_drag_costs_its_own_duration_on_every_click`.

**FR-18.** Система должна форматировать длительность как `N ms` (< 1 с), `N.N s` (< 60 с), `M min S s` (< 60 мин) или `H h M min`.
Источник: `core.py:102-112`. Проверка: `test_durations_are_written_for_a_person`.

### 3.4 Окно

**FR-19.** Система должна показывать окно «Auto Clicker Pro» 500×600 с группами «Настройки клика», «Случайные настройки», «Горячие клавиши», «Управление конфигурациями», кнопками «Сохранить настройки», «Загрузить файл», «Старт», «Стоп», надписью «Сделано кликов: N» и строкой состояния.
Источник: `gui.py:115-119`, `gui.py:199-337`. Проверка: no test (визуально — `docs/screenshots/main-window.png`).

**FR-20.** Система должна включать поле длительности перетаскивания только для типа «Перетаскивание», поля X/Y и флаг смещения — только при отмеченном «Фиксированном положении», поля диапазонов — только при отмеченных флагах.
Источник: `gui.py:342-357`. Проверка: no test.

**FR-21.** Система должна регистрировать глобальные сочетания `start`, `stop`, `get_pos` (по умолчанию F6, F7, F8) в отдельном потоке и снимать все перехваты при закрытии окна.
Источник: `gui.py:39-52`, `gui.py:184-197`. Проверка: no test.

**FR-22.** Система должна по `get_pos` записывать текущие координаты курсора (`pyautogui.position()`) в поля X и Y и показывать их в строке состояния 3 с.
Источник: `gui.py:359-366`. Проверка: no test.

**FR-23.** Система должна перед запуском проверять настройки окна тем же преобразованием, что и файл (`preset_to_settings`), и при ошибке показывать «Ошибка ввода» с текстом `SettingsError`, не запуская клики.
Источник: `gui.py:381-387`, `gui.py:399-430`. Проверка: no test (само преобразование — тесты FR-1…FR-7).

**FR-24.** Система должна в потоке кликов на каждой итерации: получить точку (FR-15), переместить мышь, если задана фиксированная позиция или смещение, выполнить одиночный клик, двойной клик или `mouseDown` — пауза `drag_duration` — `mouseUp` выбранной кнопкой, увеличить счётчик и передать его в окно, проверить остановку (FR-16), уснуть на интервал (FR-13, FR-14).
Источник: `gui.py:76-109`. Проверка: no test. В `a7140ba` поток не создаётся — см. D-1.

**FR-25.** Система должна останавливать клики кнопкой «Стоп», сочетанием `stop` или по окончании ограниченного запуска, дожидаться завершения потока и возвращать кнопки в исходное состояние.
Источник: `gui.py:396`, `gui.py:432-442`. Проверка: no test.

**FR-26.** Система должна показывать в выпадающем списке имена файлов `configs/*.json` (или «Нет сохраненных файлов»), создавая каталог `configs/` при необходимости, и загружать выбранный файл кнопкой «Загрузить».
Источник: `gui.py:447-455`, `gui.py:475-479`. Проверка: no test.

**FR-27.** Система должна сохранять текущие настройки через диалог в выбранный JSON-файл (FR-11), запоминать его путь и обновлять список; при `OSError` — показывать «Ошибка сохранения».
Источник: `gui.py:481-494`. Проверка: no test.

**FR-28.** Система должна загружать пресет из диалога или по пути в поля окна, применять `hotkeys` из файла с перерегистрацией сочетаний, запоминать путь и показывать «Ошибка загрузки» при любой ошибке.
Источник: `gui.py:496-535`. Проверка: no test. См. D-2, D-3.

**FR-29.** Система должна при запуске загружать пресет, путь к которому записан в `last_config.json`.
Источник: `gui.py:181`, `gui.py:457-473`. Проверка: no test.

### 3.5 Запуск и вспомогательные скрипты проекта

**FR-30.** Система должна запускаться командой `python run_autoclicker.py`, которая добавляет `src/` в `sys.path` и завершает процесс кодом возврата `QApplication.exec()`.
Источник: `run_autoclicker.py:21-26`, `gui.py:538-544`. Проверка: no test.

**FR-31.** Репозиторий должен следовать стандарту repo-quality-template ревизии 2 с настройками из `[tool.repo-quality]` и сборкой релиза только для Windows; скрипт `scripts/capture_usage_screenshots.py` должен снимать окно с заглушками `keyboard`/`pyautogui` в `docs/screenshots/main-window.png` и `preset-loaded.png`.
Источник: `README.md` (раздел «Качество»), `pyproject.toml:74-90`, `.github/workflows/release.yml`, `scripts/capture_usage_screenshots.py:42-116`. Проверка: CI (`.github/workflows/*.yml`); для скриншотов — no test.

### 3.6 Известные расхождения кода с требованиями

| ID | Что | Источник |
| --- | --- | --- |
| D-1 | `start_clicking` создаёт `ClickerThread(settings)`, а `__init__` требует `settings` и `cursor` без значения по умолчанию. Вызов поднимает `TypeError`, FR-24 и FR-25 из окна недостижимы. Установлено разбором AST, окно не запускалось. Появилось в `40b4b0c` | `gui.py:66`, `gui.py:394` |
| D-2 | Окно читает пресет `open(file_path)` без кодировки и сырым `json.load`, мимо FR-9/FR-10. Файл из FR-11 (UTF-8, кириллица без экранирования) при кодировке cp1252 не декодируется, при cp1251 подписи читаются другими строками (проверено декодированием байтов; поведение окна — вывод) | `gui.py:503-521`, `settings.py:184-188` |
| D-3 | Каждая загрузка пресета с `hotkeys` создаёт новый `HotkeyThread`, прежние обработчики не снимаются (вывод из кода) | `gui.py:192-197`, `gui.py:523-528` |
| D-4 | Счётчик увеличивается и после исключения `pyautogui`, которое лишь печатается в stdout | `gui.py:97-101` |

### 3.7 Заявлено, но не реализовано или не подключено

- `estimate_run`, `format_duration` (FR-17, FR-18) нигде в `src/` не вызываются;
  в окне оценки длительности нет (`grep` по `src/`).
- Захват координат щелчком по окну: `mousePressEvent` проверяет
  `is_getting_position`, который нигде не становится `True`
  (`gui.py:175`, `gui.py:368-379`).
- `hotkeys_to_string` и `self.key_inputs` не используются (`gui.py:190`,
  `gui.py:339-340`); редактирования горячих клавиш в окне нет — поля только для
  чтения (`gui.py:279,284,289`).
- `README.md`: «Папка создается автоматически при первом сохранении настроек» —
  каталог создаётся при каждом запуске (`gui.py:182`, `gui.py:448`).
- `README.md`: случайное смещение «работает только при включенном
  Фиксированном положении» — ядро применяет его и к курсору (FR-15).
- `CHANGELOG.md` 1.1.0: неверная настройка отклоняется «when it is entered» —
  проверка выполняется только при старте (FR-23).
- `pyproject.toml:15`: `Development Status :: 5 - Production/Stable` — при D-1.

## 4. Интерфейсы

### 4.1 Командная строка

| Команда | Аргументы | Источник |
| --- | --- | --- |
| `python run_autoclicker.py` | собственных нет; `sys.argv` передаётся в `QApplication` | `run_autoclicker.py`, `gui.py:540` |
| `python scripts/capture_usage_screenshots.py` | `--offscreen` — `QT_QPA_PLATFORM=offscreen` | `scripts/capture_usage_screenshots.py:77-90` |
| `python scripts/build_release_artifact.py` | `--version` (по умолчанию `v0.0.0-dev`), `--skip-exe` | `scripts/build_release_artifact.py:113-123` |

### 4.2 Горячие клавиши

| Действие | По умолчанию | Сигнал → слот | Источник |
| --- | --- | --- | --- |
| Старт | F6 | `start_signal` → `start_clicking` | `gui.py:49,189,194` |
| Стоп | F7 | `stop_signal` → `stop_clicking` | `gui.py:50,189,195` |
| Получить позицию | F8 | `get_pos_signal` → `get_position` | `gui.py:51,189,196` |

### 4.3 Вызовы библиотек ввода

| Вызов | Когда | Источник |
| --- | --- | --- |
| `pyautogui.moveTo(x, y)` | есть фиксированная позиция или смещение | `gui.py:84-85` |
| `pyautogui.click(button=…)` | «Один клик» | `gui.py:89-90` |
| `pyautogui.doubleClick(button=…)` | «Двойной клик» | `gui.py:91-92` |
| `pyautogui.mouseDown` / `mouseUp` с паузой | «Перетаскивание» | `gui.py:93-96` |
| `pyautogui.position()` | захват координат | `gui.py:363` |
| `keyboard.add_hotkey`, `keyboard.wait`, `keyboard.unhook_all` | горячие клавиши | `gui.py:49-52,185` |

Значения кнопок для `pyautogui`: `left`, `right`, `middle` (`settings.py:26-31`).

### 4.4 Формат пресета (`configs/*.json`)

| Поле | Тип в файле | По умолчанию | Источник |
| --- | --- | --- | --- |
| `interval` | строка, целое | `"100"` | `settings.py:118` |
| `interval_unit` | `"ms"` \| `"s"` | `"ms"` | `settings.py:119` |
| `click_count` | строка, целое, `0` — без ограничения | `"0"` | `settings.py:120` |
| `mouse_button` | `"Левая"` \| `"Правая"` \| `"Средняя"` | `"Левая"` | `settings.py:42-46,121` |
| `click_type` | `"Один клик"` \| `"Двойной клик"` \| `"Перетаскивание"` | `"Один клик"` | `settings.py:48-52,122` |
| `drag_duration` | строка, целое, мс | `"500"` | `settings.py:123` |
| `fixed_pos_enabled` | bool | `false` | `settings.py:124` |
| `coord_x`, `coord_y` | строка, целое | `""` | `settings.py:125-126` |
| `random_offset_enabled` | bool | `false` | `settings.py:127` |
| `random_offset_range` | строка, целое, px | `"5"` | `settings.py:128` |
| `random_interval_enabled` | bool | `false` | `settings.py:129` |
| `random_interval_range` | строка, целое, мс | `"10"` | `settings.py:130` |
| `hotkeys` | объект `{start, stop, get_pos}` | `F6`, `F7`, `F8` | `settings.py:57,131` |

Версии формата в файле нет (`docs/decisions.md`, «The preset format was not
modernised»).

### 4.5 `last_config.json`

Текстовый файл с одной строкой — путём к пресету; несмотря на расширение, не
JSON. Пишется при сохранении и загрузке, читается при запуске
(`gui.py:457-473`, `gui.py:490`, `gui.py:530`).

## 5. Данные

| Сущность | Что это | Источник |
| --- | --- | --- |
| `MouseButton`, `ClickType` | Перечисления `left/right/middle`, `single/double/drag` | `settings.py:26-38` |
| `BUTTON_LABELS`, `CLICK_TYPE_LABELS` | Соответствие русских подписей перечислениям; единственное место ниже окна с русскими строками | `settings.py:40-55` |
| `ClickSettings` | Неизменяемый (`frozen`) проверенный набор параметров запуска; проверка в `__post_init__` | `settings.py:64-111` |
| `Preset` | Файл пресета как есть: строки и флаги | `settings.py:114-174` |
| `RunEstimate` | Число кликов и три оценки длительности в секундах | `core.py:68-75` |

Хранилище — только локальные файлы: `configs/*.json` (UTF-8 при записи через
`save_preset`), `last_config.json` (кодировка по умолчанию платформы,
`gui.py:459`, `gui.py:467`). Скрипты пишут `docs/screenshots/*.png` и
`release/` (`scripts/capture_usage_screenshots.py:39`,
`scripts/build_release_artifact.py:26`).

## 6. Нефункциональные требования

**NFR-1.** `core.py` и `settings.py` не должны импортировать Qt, `pyautogui` и `keyboard`. Источник: `core.py:14-17`, `settings.py:19-23`, `docs/architecture.md`.

**NFR-2.** Случайность в ядре должна идти только через переданный `random.Random`, чтобы последовательность воспроизводилась по seed. Источник: `core.py:25,42`; проверка `test_the_same_seed_gives_the_same_sequence`.

**NFR-3.** Параметры запуска не должны меняться во время работы потока: `ClickSettings` объявлен `frozen=True`. Источник: `settings.py:64`.

**NFR-4.** Покрытие ветвей пакета `autoclicker` без `gui.py` — не ниже 85 %. Источник: `pyproject.toml:114-126`.

**NFR-5.** Цикломатическая сложность функции — не выше 10 (кроме `gui.py`, `tests/`). Источник: `pyproject.toml:51`, `per-file-ignores` там же.

**NFR-6.** `core.py` и `settings.py` проходят `mypy --strict`. Источник: `pyproject.toml:97-101`.

**NFR-7.** Доменные тесты выполняются без дисплея на Ubuntu и Windows, Python 3.10 и 3.12. Источник: `.github/workflows/ci.yml` (job `test`), `pyproject.toml:110`.

**NFR-8.** Стоимость решений на клик измеряется бенчмарками в CI; порога, при котором сборка падает, нет. Источник: `benchmarks/test_performance.py`, `.github/workflows/ci.yml` (job `benchmark`). Замеры автора — в `docs/quality-iso25010.md`, здесь не перепроверялись.

**NFR-9.** Пресеты формата v1.0.0 должны продолжать загружаться. Источник: `settings.py:5-7` (docstring), тест `test_the_preset_that_ships_with_the_repository_still_loads`.

**NFR-10.** Сообщения об ошибках настроек называют поле или оба конфликтующих числа. Источник: `settings.py:101-107`, `settings.py:191-195`.

**NFR-11.** Интерфейс на русском языке; код, комментарии и документация репозитория — на английском. Источник: `docs/decisions.md` («Point 12»).

## 7. Ограничения и зависимости

| Зависимость | Версия | Источник |
| --- | --- | --- |
| Python | `>=3.10` | `pyproject.toml:10` |
| PyQt6 | `>=6.6`, не зафиксирована | `pyproject.toml:19` |
| pyautogui | `>=0.9.54`, не зафиксирована | `pyproject.toml:19` |
| keyboard | `>=0.13.5`, не зафиксирована | `pyproject.toml:19` |
| setuptools (сборка пакета) | `>=68` | `pyproject.toml:2` |
| pyinstaller (релиз) | `>=6.0`, в lock-файле нет | `pyproject.toml:31` |
| pytest / pytest-cov / pytest-benchmark | `==9.1.1` / `==7.1.0` / `==5.3.0` | `requirements-dev.lock` |
| ruff / mypy / radon / pre-commit | `==0.16.6` / `==2.3.1` / `==6.0.1` / `==4.6.2` | `requirements-dev.lock` |

Прочие ограничения из кода: значения настроек — целые числа (FR-2), нижняя
граница интервала 1 мс (`core.py:22`), пути `configs/` и `last_config.json`
относительно рабочего каталога (`gui.py:176-177`). Лицензия MIT (`LICENSE`).

## 8. Приёмка

1. `pytest` — все тесты проходят. На `a7140ba` (Python 3.13.3):
   `python -m pytest -p no:cacheprovider -o addopts= -q` → `56 passed`. Это
   проверяет FR-1…FR-18 и NFR-2, NFR-9.
2. `pytest --cov` — не ниже 85 % (NFR-4); `ruff check .`, `ruff format --check .`,
   `python -m mypy` — без замечаний (NFR-5, NFR-6). Здесь не запускалось.
3. Ручная проверка окна на Windows (FR-19…FR-30), автоматических тестов нет:
   - значения по умолчанию, «Количество кликов» = 5, «Старт» → счётчик доходит
     до 5, кнопки возвращаются (FR-24, FR-25). На `a7140ba` не выполняется (D-1);
   - F8 заполняет X/Y (FR-22); F6/F7 работают без фокуса на окне (FR-21);
   - сохранить пресет с «Правая» кнопкой, перезапустить без UTF-8 режима Python,
     убедиться, что пресет подхватился и кнопка — «Правая» (FR-27, FR-29, D-2);
   - разброс 200 мс при интервале 50 мс → предупреждение «Ошибка ввода» (FR-7, FR-23).
4. `python scripts/capture_usage_screenshots.py` пишет два PNG в
   `docs/screenshots/` (FR-31).

## 9. Открытые вопросы

1. Кто пользователи и для чего программа. Есть только «читают по-русски» и
   «file with four users» (`docs/decisions.md`); назначение пресета
   `Dota2Pudge.json` не описано.
2. Как должен вести себя запуск со смещением без фиксированной позиции:
   комментарий говорит, что точка курсора берётся один раз при старте
   (`gui.py:69-70`), но вызов эту точку не передаёт (D-1). Было ли это
   намерением или v1.0.0-поведение «кликать там, где курсор» должно остаться?
3. Код не задаёт `pyautogui.PAUSE` и `pyautogui.FAILSAFE` (поиск по `src/`
   пуст). По документации `pyautogui` (в этой среде библиотека не установлена,
   не проверено) после каждого вызова по умолчанию есть пауза 0,1 с, а курсор в
   углу экрана поднимает исключение. Если так, фактический интервал не меньше
   примерно 0,1 с при любых настройках, а заявленный в бенчмарках расчёт про
   «1 мс» к реальному ритму не относится. Требуется замер на Windows.
4. Поддерживаются ли macOS и Linux: `README.md` описывает установку там, а
   релиз и комментарии CI ограничивают программу Windows.
5. Целевой ритм кликов и допустимая погрешность нигде не заданы; бенчмарки
   без порога (NFR-8).
6. ~~Был ли опубликован релиз `v1.1.0` и из какого кода.~~ Ответ: да.
   GitHub API (`repos/…/releases`) показывает релиз `v1.1.0`, не черновик,
   опубликован 2026-09-06T13:39:49Z; его собрал прогон `release.yml`
   34036657133 по тегу `v1.1.0` → `a7140ba`, то есть из кода с D-1 (проверено
   при сверке документа через `gh`).
7. `docs/decisions.md` требует документацию на английском (NFR-11), а
   `README.md` и эти документы — на русском. Какой язык считать правилом для
   `docs/`?
