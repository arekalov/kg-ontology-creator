# README.md

## 📋 Краткое описание проекта

**Тема:** Граф знаний для игры World of Tanks

**Цель:** Создание онтологии и графа знаний для анализа эффективности танков, игроков и выявления паттернов игры на основе реальных игровых данных.

**Результат:**
- OWL онтология с 18 классами и 75 свойствами
- Граф знаний из 970,140 триплетов
- 30,000 реальных боев с полной статистикой
- 20 примеров SPARQL запросов для анализа

---

## 🎯 Постановка задачи

### Зачем создаём граф знаний?

Граф знаний помогает решать следующие задачи:

1. **Выбор танка** исходя из пожеланий игрока и игровой меты
2. **Построение тактики** в бою исходя из состава команд и карты
3. **Анализ эффективности** танков на основе реальной статистики
4. **Рекомендательная система** для выбора техники
5. **Выявление imbalanced танков** для разработчиков
6. **Систематизация разрозненной информации** для удобства поиска

### Как граф будет использоваться?

- Игроки смогут запрашивать рекомендации по выбору танка
- Аналитики смогут выявлять проблемы баланса
- Новички получат помощь в изучении игры
- Разработчики смогут принимать решения на основе данных

---

## 📊 Описание предметной области

### Основные сущности:

1. **Tank (Танк)** - основная боевая единица
   - Подклассы: HeavyTank, MediumTank, LightTank, TankDestroyer, SelfPropelledGun
   - Свойства: название, уровень, HP, вес, цена, премиум-статус

2. **Nation (Нация)** - страна-производитель
   - Инстансы: СССР, Германия, США, Франция, UK, Китай и др.

3. **Battle (Бой)** - игровой матч
   - Свойства: время, продолжительность, победа/поражение, сторона

4. **BattlePerformance (Результат боя)** - связывает игрока, танк и бой
   - Свойства: урон, точность, фраги, засвет, опыт (33 показателя)

5. **Player (Игрок)**
   - Свойства: никнейм, статистика побед, средний урон

6. **Module (Модуль)**
   - Подклассы: Gun, Engine, Turret, Suspension, Radio
   - Свойства: характеристики модулей

### Связи между объектами:

- Tank → belongsToNation → Nation
- Tank → equipsWith → Module
- BattlePerformance → withTank → Tank
- BattlePerformance → achievedBy → Player
- BattlePerformance → inBattle → Battle

---

## 📁 Источники данных

### 1. tomato.csv (10 млн боев)
- **33 колонки** с детальной статистикой каждого боя
- Урон, точность, засвет, фраги, опыт
- Все игроки, танки, результаты
- **Использовано: 100% колонок**

### 2. wot_data.csv (~15K конфигураций)
- **31 колонка** с характеристиками танков
- HP, броня, скорость, вооружение
- Модули и их характеристики
- **Использовано: 87% колонок**

### Обработка данных:
- ✅ Очистка от некорректных записей
- ✅ Случайная выборка для разнообразия
- ✅ Нормализация значений
- ✅ Удаление дубликатов

---

## 🏗️ Структура онтологии

### Классы (18):
```
Thing
├── Tank
│   ├── HeavyTank       (Тяжелый танк)
│   ├── MediumTank      (Средний танк)
│   ├── LightTank       (Легкий танк)
│   ├── TankDestroyer   (ПТ-САУ)
│   └── SelfPropelledGun (САУ)
├── Module
│   ├── Gun             (Орудие)
│   ├── Engine          (Двигатель)
│   ├── Turret          (Башня)
│   ├── Suspension      (Подвеска)
│   └── Radio           (Радио)
├── Nation              (Нация)
├── Player              (Игрок)
├── Battle              (Бой)
├── BattlePerformance   (Результат боя)
├── TankCharacteristics (Характеристики)
└── TankRole            (Роль)
```

### Object Properties (18):
- belongsToNation, equipsWith, hasGun, hasEngine, hasTurret
- participatesIn, plays, achieves
- withTank, inBattle, achievedBy
- installedOn, compatibleWith

### Datatype Properties (57):
- Для Tank: tankId, tankName, tier, maxHP, weight, isPremium
- Для BattlePerformance: damage, shots_fired, frags, spots, baseXP
- Для Player: displayName, winRate, avgDamage
- И многие другие...

---

## 📈 Статистика созданного графа

### Граф знаний (wot_with_data.owl):
- **970,140 триплетов** (фактов)
- **708 танков** с полными характеристиками
- **437 танков** с игровой статистикой
- **30,000 боев** со всеми деталями
- **40 игроков** с историей
- **Размер файла:** 97.35 MB

### Временные затраты:
- Создание онтологии: ~2 секунды
- Импорт данных (30K боев): ~3 минуты
- Открытие в Protégé: ~30 секунд

---

## 🎯 Компетентностные вопросы (примеры)

### 1. Какие танки имеют лучший процент побед?
**Тип:** Анализ эффективности танков
**SPARQL:** См. запрос #2 в `queries/example_queries.sparql`

### 2. Какой средний урон наносят разные классы танков?
**Тип:** Сравнительный анализ
**SPARQL:** См. запрос #3

### 3. Кто лучшие игроки по среднему урону?
**Тип:** Ранжирование игроков
**SPARQL:** См. запрос #4

### 4. Какие танки лучше всего для засвета?
**Тип:** Рекомендации по роли
**SPARQL:** См. запрос #6

### 5. Есть ли дисбаланс между сторонами карты?
**Тип:** Анализ баланса игры
**SPARQL:** См. запрос #9

**Всего:** 50 компетентностных вопросов в документации

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd ontology-creator

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Подготовка данных

Создайте директорию для данных:
```bash
mkdir -p data
```

Скачайте датасеты:

1. **Датасет боев (tomato.csv)** - 10 миллионов реальных боев  
   📥 Скачать: [Kaggle - World of Tanks Battles from Tomato.gg](https://www.kaggle.com/datasets/goldflag/10-million-world-of-tanks-battles-from-tomato-gg)
   - Нажмите "Download" на странице Kaggle
   - Распакуйте `tomato.csv` в директорию `data/`

2. **Датасет танков (wot_data.csv)** - характеристики всех танков  
   📥 Скачать: [GitHub - wot_tank_data](https://github.com/GuilleHoardings/wot_tank_data/blob/main/wot_data.csv)
   - Нажмите "Raw" и сохраните файл
   - Поместите `wot_data.csv` в директорию `data/`

Структура директории должна быть:
```
ontology-creator/
├── data/
│   ├── tomato.csv      # 10M боев (~2GB)
│   └── wot_data.csv    # ~15K конфигураций танков
├── scripts/
├── ontology/
└── ...
```

> **Примечание:** Директория `data/` находится в `.gitignore`, поэтому датасеты не загружаются в репозиторий

### 3. Создание онтологии

```bash
# Создаем базовую структуру онтологии (классы, свойства)
python scripts/create_ontology.py
```

Результат: `ontology/wot_ontology.owl` (~47 KB)

### 4. Импорт данных

```bash
# Импортируем данные о танках и боях
python scripts/import_data_to_rdf.py --battles 30000 --output wot_with_data

# Опции:
#   --battles N     - количество боев для импорта (по умолчанию 30000)
#   --tanks N       - ограничение по танкам (по умолчанию все)
#   --no-random     - не использовать случайную выборку
#   --output NAME   - имя выходного файла
```

Результат: `ontology/wot_with_data.owl` (~100 MB, ~1M триплетов)

⏱️ Время импорта: ~3 минуты для 30K боев

### 5. Работа с онтологией в Protégé

1. Скачайте Protégé: https://protege.stanford.edu/
2. Откройте файл: `File → Open → ontology/wot_with_data.owl`
3. Исследуйте:
   - **Classes** - просмотр иерархии классов
   - **Object Properties** - связи между объектами
   - **Data Properties** - атрибуты объектов
   - **Individuals** - инстансы (танки, игроки, бои)
   - **DL Query** - запросы на языке описания логики

### 6. Выполнение SPARQL запросов

#### Из кода Python:

```bash
# Показать статистику
python scripts/query_ontology.py --stats

# Предопределенные запросы
python scripts/query_ontology.py --query top-tanks
python scripts/query_ontology.py --query damage-by-class
python scripts/query_ontology.py --query best-players
python scripts/query_ontology.py --query nations

# Список всех запросов
python scripts/query_ontology.py --help
```

#### Интерактивный режим:

```bash
python scripts/query_ontology.py --interactive
```

#### В Protégé:

1. Перейдите на вкладку **Window → Tabs → SPARQL Query**
2. Скопируйте запрос из `queries/example_queries.sparql`
3. Нажмите **Execute**

---

## 📝 Примеры SPARQL запросов

### Запрос 1: Топ танков по винрейту

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

### Запрос 2: Средний урон по классам

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

**Больше примеров:** см. файл `queries/example_queries.sparql` (20 запросов)

---

## 🛠️ Технологии

- **Python 3.x** - основной язык
- **RDFLib** - работа с RDF графами
- **Pandas** - обработка CSV данных
- **OWL 2** - язык описания онтологий
- **SPARQL 1.1** - язык запросов
- **Protégé 5.x** - редактор онтологий

---

## 📚 Структура проекта

```
ontology-creator/
├── data/                    # Исходные датасеты (не в git)
│   ├── tomato.csv
│   └── wot_data.csv
├── scripts/                 # Python скрипты
│   ├── create_ontology.py   # Создание структуры онтологии
│   ├── import_data_to_rdf.py # Импорт данных
│   └── query_ontology.py    # Выполнение SPARQL запросов
├── ontology/                # OWL файлы
│   ├── wot_ontology.owl     # Базовая онтология
│   └── wot_with_data.owl    # С данными
├── queries/                 # Примеры SPARQL запросов
│   └── example_queries.sparql
├── requirements.txt         # Python зависимости
└── README.md               # Этот файл
```

---

## 📊 Статистика импорта

После выполнения `import_data_to_rdf.py`:

```
Total triples: 993,375
Tanks: 437
Players: 40
Battles: 30,000
Guns: 805
Engines: 739
Turrets: 747
Suspensions: 1,080
Radios: 237
TankCharacteristics: 708
TankRole: 5
```
