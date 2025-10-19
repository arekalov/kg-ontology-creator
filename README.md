# 🎮 Граф знаний World of Tanks

Проект по созданию графа знаний для игры "Мир Танков" с использованием онтологии OWL и SPARQL запросов.

## 📊 О проекте

Граф знаний содержит:
- **970,140 триплетов** - фактов о танках, боях и игроках
- **708 танков** - с полными характеристиками
- **30,000 боев** - реальная игровая статистика
- **40 игроков** - с детальной статистикой

### Данные включают:
- Танки (характеристики, классы, нации, модули)
- Бои (результаты, продолжительность, карты)
- Игроки (статистика, предпочтения)
- Результаты боев (урон, точность, засвет, опыт)

## 📁 Структура проекта

```
ontology-creator/
├── data/                          # Исходные данные
│   ├── tomato.csv                # 10M боев
│   └── wot_data.csv              # Характеристики танков
├── scripts/                       # Python скрипты
│   ├── create_ontology.py        # Создание схемы онтологии
│   └── import_data_to_rdf.py     # Импорт данных в граф
├── ontology/                      # OWL файлы
│   ├── wot_ontology.owl          # Схема онтологии (пустая)
│   └── wot_with_data.owl         # Полный граф с данными
├── queries/                       # SPARQL запросы
│   └── example_queries.sparql    # 20 примеров запросов
├── ONTOLOGY_DESIGN.md            # Дизайн онтологии
├── TOMATO_QUESTIONS.md           # Компетентностные вопросы
└── requirements.txt               # Зависимости
```

## Установка

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate  # На macOS/Linux
# или
venv\Scripts\activate  # На Windows

# Установите зависимости
pip install -r requirements.txt
```

## Получение API ключа

Для работы с API World of Tanks вам нужен `application_id`:

1. Зарегистрируйтесь на https://developers.lesta.ru/ (для RU региона)
   или https://developers.wargaming.net/ (для других регионов)
2. Создайте приложение
3. Скопируйте ваш `application_id`
4. Укажите его в `scripts/fetch_tanks_data.py` или используйте переменную окружения `WOT_APPLICATION_ID`

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Создание онтологии (опционально)

Онтология уже создана, но можно пересоздать:

```bash
python scripts/create_ontology.py
```

Результат: `ontology/wot_ontology.owl` (~46 KB, 517 триплетов)

### 3. Импорт данных

```bash
# Импорт 30,000 случайных боев (рекомендуется)
python scripts/import_data_to_rdf.py --battles 30000

# Быстрый импорт (10,000 боев, ~30 MB)
python scripts/import_data_to_rdf.py --battles 10000

# Больше данных (50,000 боев, ~150 MB)
python scripts/import_data_to_rdf.py --battles 50000
```

Результат: `ontology/wot_with_data.owl`

**⏱️ Время импорта:**
- 10,000 боев: ~1 минута
- 30,000 боев: ~3 минуты
- 50,000 боев: ~5 минут

### 4. Открытие в Protégé

1. Скачайте и установите [Protégé](https://protege.stanford.edu/)
2. Откройте Protégé
3. `File` → `Open` → выберите `ontology/wot_with_data.owl`
4. Дождитесь загрузки (10-60 секунд в зависимости от размера)

### 5. Запуск SPARQL запросов

В Protégé:
1. Перейдите в вкладку `Window` → `Tabs` → `SPARQL Query`
2. Скопируйте запрос из `queries/example_queries.sparql`
3. Нажмите `Execute`

## 📝 Примеры SPARQL запросов

### Топ 10 танков по проценту побед

```sparql
PREFIX wot: <http://www.semanticweb.org/ontology/wot#>

SELECT ?tankName 
       (COUNT(?perf) AS ?totalBattles)
       ((SUM(IF(?won, 1, 0)) * 100.0 / COUNT(?perf)) AS ?winRate)
WHERE {
  ?perf wot:withTank ?tank .
  ?perf wot:inBattle ?battle .
  ?battle wot:won ?won .
  ?tank wot:tankName ?tankName .
}
GROUP BY ?tankName
HAVING (COUNT(?perf) > 50)
ORDER BY DESC(?winRate)
LIMIT 10
```

### Средний урон по классам

```sparql
PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?tankType 
       (AVG(?damage) AS ?avgDamage) 
       (COUNT(?perf) AS ?battles)
WHERE {
  ?perf wot:withTank ?tank .
  ?perf wot:damage ?damage .
  ?tank rdf:type ?tankType .
  FILTER(?tankType IN (wot:HeavyTank, wot:MediumTank, wot:LightTank, 
                       wot:TankDestroyer, wot:SelfPropelledGun))
}
GROUP BY ?tankType
ORDER BY DESC(?avgDamage)
```

**Больше запросов:** см. `queries/example_queries.sparql` (20 примеров)

## 🎯 Компетентностные вопросы

Граф знаний может отвечать на следующие вопросы:

### Анализ танков:
- Какие танки имеют лучший процент побед?
- Какой средний урон по классам танков?
- Какие танки лучше всего блокируют урон бронёй?
- Какие танки наиболее эффективны для засвета?

### Анализ игроков:
- Кто лучшие игроки по среднему урону?
- Какие игроки предпочитают играть на тяжелых танках?
- Кто чаще всего играет в взводе?

### Мета-анализ:
- Есть ли дисбаланс между сторонами?
- Какие танки переигрывают (overpowered)?
- Какая нация имеет лучшую статистику?

**Полный список:** см. `TOMATO_QUESTIONS.md` (30 вопросов с SPARQL запросами)

## 📚 Документация

- **ONTOLOGY_DESIGN.md** - Полное описание структуры онтологии
  - Классы и иерархия
  - Объектные и дата-свойства
  - Связи между объектами
  - 50 компетентностных вопросов

- **TOMATO_QUESTIONS.md** - Вопросы специально для датасета tomato.csv
  - 30 аналитических вопросов
  - SPARQL запросы с примерами
  - Анализ результатов

## 📊 Статистика проекта

### Онтология (схема):
- **18 классов** (Tank + подклассы, Module + подклассы, и др.)
- **18 объектных свойств** (связи между объектами)
- **57 дата-свойств** (атрибуты объектов)
- **11 инстансов наций** (СССР, Германия, США и т.д.)

### Данные (30K боев):
- **970,140 триплетов**
- **708 уникальных танков**
- **437 танков с игровой статистикой**
- **40 игроков**
- **30,000 боев**

### Покрытие данных:
- **100% колонок из tomato.csv** (33/33)
- **87% колонок из wot_data.csv** (27/31)

## 🛠️ Технологии

- **Python 3.13** - язык программирования
- **rdflib 7.0.0** - работа с RDF графами
- **pandas 2.3** - обработка CSV данных
- **Protégé** - визуализация и работа с онтологией
- **SPARQL** - язык запросов к графу знаний
- **OWL** - язык описания онтологий

## 📖 Источники данных

- **tomato.csv** - 10 миллионов реальных боев из World of Tanks
- **wot_data.csv** - Характеристики ~15,000 конфигураций танков
- Документация:
  - API Wargaming: https://developers.wargaming.net/
  - API Lesta: https://developers.lesta.ru/
  - Wiki Lesta: https://wiki.lesta.ru/ru/Мир_танков

## 👥 Авторы

Проект выполнен в рамках курса "Графы знаний" ИТМО, 2025

## 📄 Лицензия

Данные World of Tanks © Wargaming.net / Lesta Games

