#!/usr/bin/env python3
"""
Скрипт для импорта данных из CSV в RDF граф знаний
Поддерживает ограничение количества записей для оптимизации
"""

import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from rdflib.namespace import XSD
from pathlib import Path
from datetime import datetime
import argparse

class DataImporter:
    def __init__(self, ontology_file):
        """Инициализация импортера"""
        # Загружаем существующую онтологию
        self.g = Graph()
        print(f"Loading ontology from {ontology_file}...")
        self.g.parse(ontology_file, format='xml')
        print(f"  Loaded {len(self.g)} triples from ontology")
        
        # Namespace
        self.WOT = Namespace("http://www.semanticweb.org/ontology/wot#")
        self.g.bind("wot", self.WOT)
        
        # Счетчики
        self.tank_counter = {}
        self.map_counter = {}
        self.battle_counter = 0
        self.gun_counter = {}
        self.engine_counter = {}
        self.turret_counter = {}
        self.suspension_counter = {}
        self.radio_counter = {}
        
        # Пути к данным
        self.data_dir = Path(__file__).parent.parent / "data"
        self.ontology_dir = Path(__file__).parent.parent / "ontology"
    
    def normalize_tank_id(self, tank_id):
        """Создает URI для танка"""
        return self.WOT[f"Tank_{tank_id}"]

    def normalize_battle_id(self, index):
        """Создает URI для боя"""
        return self.WOT[f"Battle_{index}"]
    
    def normalize_performance_id(self, index):
        """Создает URI для результата боя"""
        return self.WOT[f"Performance_{index}"]
    
    def map_class_to_type(self, tank_class):
        """Маппинг класса танка в тип онтологии"""
        mapping = {
            'HT': 'HeavyTank',
            'MT': 'MediumTank',
            'LT': 'LightTank',
            'TD': 'TankDestroyer',
            'SPG': 'SelfPropelledGun',
        }
        return self.WOT[mapping.get(tank_class, 'Tank')]
    
    def map_nation_to_uri(self, nation_code):
        """Маппинг кода нации в URI"""
        mapping = {
            'USSR': 'USSR',
            'Germany': 'Germany',
            'USA': 'USA',
            'France': 'France',
            'UK': 'UK',
            'China': 'China',
            'Japan': 'Japan',
            'Czech': 'Czech',
            'Sweden': 'Sweden',
            'Poland': 'Poland',
            'Italy': 'Italy',
        }
        return self.WOT[mapping.get(nation_code, nation_code)]
    
    def create_module_instance(self, module_id, module_type, module_name=None, **properties):
        """Создает инстанс модуля"""
        if not module_id or pd.isna(module_id):
            return None
        
        module_uri = self.WOT[f"{module_type}_{module_id}"]
        
        # Проверяем, не создавали ли уже этот модуль
        counter_map = {
            'Gun': self.gun_counter,
            'Engine': self.engine_counter,
            'Turret': self.turret_counter,
            'Suspension': self.suspension_counter,
            'Radio': self.radio_counter
        }
        
        counter = counter_map.get(module_type, {})
        
        if module_uri not in counter:
            # Создаем новый инстанс модуля
            self.g.add((module_uri, RDF.type, self.WOT[module_type]))
            
            # Добавляем название если есть
            if module_name and pd.notna(module_name):
                prop_name = f"{module_type.lower()}Name"
                self.g.add((module_uri, self.WOT[prop_name], Literal(str(module_name), datatype=XSD.string)))
            
            # Добавляем дополнительные свойства
            for prop, value in properties.items():
                if pd.notna(value):
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            self.g.add((module_uri, self.WOT[prop], Literal(float(value), datatype=XSD.float)))
                        else:
                            self.g.add((module_uri, self.WOT[prop], Literal(int(value), datatype=XSD.integer)))
                    else:
                        self.g.add((module_uri, self.WOT[prop], Literal(str(value), datatype=XSD.string)))
            
            counter[module_uri] = 0
        
        counter[module_uri] += 1
        return module_uri
    
    def get_role_name_from_type(self, tank_type):
        """Определяет роль танка на основе его типа"""
        role_mapping = {
            'heavyTank': 'HeavyAssault',
            'mediumTank': 'Support',
            'lightTank': 'Scout',
            'AT-SPG': 'Sniper',
            'SPG': 'Artillery'
        }
        return role_mapping.get(tank_type, None)
    
    def normalize_uri_part(self, text):
        """Нормализует текст для использования в URI"""
        if not text:
            return ""
        # Заменяем пробелы и спецсимволы на подчеркивания
        text = str(text).replace(' ', '_').replace('.', '_').replace('-', '_')
        # Удаляем все не-ASCII символы
        text = ''.join(c if ord(c) < 128 else '_' for c in text)
        # Убираем множественные подчеркивания
        while '__' in text:
            text = text.replace('__', '_')
        return text
    
    def import_tanks_from_wot_data(self, limit=None):
        """Импортирует данные о танках из wot_data.csv"""
        print("\n" + "=" * 60)
        print("IMPORTING TANK DATA FROM wot_data.csv")
        print("=" * 60)
        
        wot_data_file = self.data_dir / "wot_data.csv"
        if not wot_data_file.exists():
            print(f"⚠️  File not found: {wot_data_file}")
            return
        
        # Читаем данные
        df = pd.read_csv(wot_data_file, sep=';', nrows=limit)
        print(f"Loaded {len(df)} tank configurations")
        
        # НЕ группируем - используем все конфигурации для создания модулей
        print(f"Processing all {len(df)} configurations to extract modules...")
        
        # Сначала создаем все модули из всех конфигураций
        for idx, row in df.iterrows():
            # Создаем Gun
            if pd.notna(row.get('gun')) and pd.notna(row.get('gun.name')):
                gun_uri = self.create_module_instance(
                    module_id=row['gun'],
                    module_type='Gun',
                    module_name=row.get('gun.name'),
                    avgPenetration=row.get('ammo.avg_penetration'),
                    avgDamage=row.get('ammo.avg_damage'),
                    fireRate=row.get('gun.fire_rate'),
                    aimTime=row.get('gun.aim_time'),
                    dpm=row.get('dpm')
                )
            
            # Создаем Engine
            if pd.notna(row.get('engine')) and pd.notna(row.get('engine.power')):
                engine_uri = self.create_module_instance(
                    module_id=row['engine'],
                    module_type='Engine',
                    power=row.get('engine.power')
                )
            
            # Создаем Turret
            if pd.notna(row.get('turret')):
                turret_uri = self.create_module_instance(
                    module_id=row['turret'],
                    module_type='Turret'
                )
            
            # Создаем Suspension
            if pd.notna(row.get('suspension')):
                suspension_uri = self.create_module_instance(
                    module_id=row['suspension'],
                    module_type='Suspension'
                )
            
            # Создаем Radio
            if pd.notna(row.get('radio')):
                radio_uri = self.create_module_instance(
                    module_id=row['radio'],
                    module_type='Radio'
                )
            
            if (idx + 1) % 1000 == 0:
                print(f"  Processed {idx + 1}/{len(df)} configurations for modules")
        
        print(f"\n📦 Created module instances:")
        print(f"   Guns: {len(self.gun_counter)}")
        print(f"   Engines: {len(self.engine_counter)}")
        print(f"   Turrets: {len(self.turret_counter)}")
        print(f"   Suspensions: {len(self.suspension_counter)}")
        print(f"   Radios: {len(self.radio_counter)}")
        
        # Теперь создаем танки (группируем для уникальности)
        print(f"\n🚜 Creating tank instances...")
        tanks_unique = df.groupby('name').first().reset_index()
        print(f"Unique tanks: {len(tanks_unique)}")
        
        # Счетчики для характеристик и ролей
        characteristics_counter = {}
        roles_counter = {}
        
        for idx, row in tanks_unique.iterrows():
            tank_name = row['name'].strip()
            
            # Используем tank_id если есть, иначе генерируем
            tank_id = row.get('tank_id', f"wot_{idx}")
            tank_uri = self.normalize_tank_id(tank_id)
            
            # Определяем тип танка
            tank_type = self.map_class_to_type(row.get('type', 'Tank'))
            self.g.add((tank_uri, RDF.type, tank_type))
            
            # Базовые свойства
            self.g.add((tank_uri, self.WOT.tankName, Literal(tank_name, datatype=XSD.string)))
            
            if pd.notna(row.get('short_name')):
                self.g.add((tank_uri, self.WOT.shortName, Literal(row['short_name'], datatype=XSD.string)))
            
            if pd.notna(row.get('tier')):
                self.g.add((tank_uri, self.WOT.tier, Literal(int(row['tier']), datatype=XSD.integer)))
            
            # Нация
            if pd.notna(row.get('nation')):
                nation_uri = self.map_nation_to_uri(row['nation'].capitalize())
                self.g.add((tank_uri, self.WOT.belongsToNation, nation_uri))
            
            # Создаем TankCharacteristics для танка
            has_characteristics = False
            char_uri = self.WOT[f"Characteristics_{self.normalize_uri_part(tank_name)}"]
            
            if pd.notna(row.get('hp')):
                self.g.add((tank_uri, self.WOT.maxHP, Literal(int(row['hp']), datatype=XSD.integer)))
                self.g.add((char_uri, self.WOT.hp, Literal(int(row['hp']), datatype=XSD.integer)))
                has_characteristics = True
            
            if pd.notna(row.get('hull_hp')):
                self.g.add((char_uri, self.WOT.hullHP, Literal(int(row['hull_hp']), datatype=XSD.integer)))
                has_characteristics = True
            
            if pd.notna(row.get('hull_weight')):
                self.g.add((char_uri, self.WOT.hullWeight, Literal(int(row['hull_weight']), datatype=XSD.integer)))
                has_characteristics = True
            
            if pd.notna(row.get('weight')):
                self.g.add((tank_uri, self.WOT.weight, Literal(int(row['weight']), datatype=XSD.integer)))
            
            if pd.notna(row.get('speed_forward')):
                self.g.add((tank_uri, self.WOT.speedForward, Literal(int(row['speed_forward']), datatype=XSD.integer)))
                self.g.add((char_uri, self.WOT.speedForward, Literal(int(row['speed_forward']), datatype=XSD.integer)))
                has_characteristics = True
            
            if pd.notna(row.get('speed_backward')):
                self.g.add((tank_uri, self.WOT.speedBackward, Literal(int(row['speed_backward']), datatype=XSD.integer)))
                self.g.add((char_uri, self.WOT.speedBackward, Literal(int(row['speed_backward']), datatype=XSD.integer)))
                has_characteristics = True
            
            # Если есть характеристики, создаем инстанс и связываем с танком
            if has_characteristics:
                self.g.add((char_uri, RDF.type, self.WOT.TankCharacteristics))
                self.g.add((tank_uri, self.WOT.hasCharacteristics, char_uri))
                characteristics_counter[char_uri] = characteristics_counter.get(char_uri, 0) + 1
            
            # Создаем TankRole на основе типа танка
            role_name = self.get_role_name_from_type(row.get('type', 'Tank'))
            if role_name:
                role_uri = self.WOT[f"Role_{role_name}"]
                if role_uri not in roles_counter:
                    self.g.add((role_uri, RDF.type, self.WOT.TankRole))
                    self.g.add((role_uri, self.WOT.roleName, Literal(role_name, datatype=XSD.string)))
                    
                    # Описание роли
                    role_descriptions = {
                        'HeavyAssault': 'Breakthrough and frontline assault tank',
                        'Support': 'Medium range support and flanking',
                        'Scout': 'Reconnaissance and spotting',
                        'Sniper': 'Long range fire support',
                        'Artillery': 'Indirect fire support'
                    }
                    if role_name in role_descriptions:
                        self.g.add((role_uri, self.WOT.roleDescription, 
                                   Literal(role_descriptions[role_name], datatype=XSD.string)))
                
                self.g.add((tank_uri, self.WOT.hasRole, role_uri))
                roles_counter[role_uri] = roles_counter.get(role_uri, 0) + 1
            
            # Премиум статус
            if pd.notna(row.get('is_premium')):
                self.g.add((tank_uri, self.WOT.isPremium, Literal(bool(row['is_premium']), datatype=XSD.boolean)))
            
            if pd.notna(row.get('is_wheeled')):
                self.g.add((tank_uri, self.WOT.isWheeled, Literal(bool(row['is_wheeled']), datatype=XSD.boolean)))
            
            if pd.notna(row.get('is_gift')):
                self.g.add((tank_uri, self.WOT.isGift, Literal(bool(row['is_gift']), datatype=XSD.boolean)))
            
            # Цены
            if pd.notna(row.get('price_credit')) and row['price_credit'] != 0:
                self.g.add((tank_uri, self.WOT.priceCredit, Literal(int(row['price_credit']), datatype=XSD.integer)))
            
            if pd.notna(row.get('price_gold')) and row['price_gold'] != 0:
                self.g.add((tank_uri, self.WOT.priceGold, Literal(int(row['price_gold']), datatype=XSD.integer)))
            
            # Связи с модулями
            if pd.notna(row.get('gun')):
                gun_uri = self.WOT[f"Gun_{row['gun']}"]
                if gun_uri in self.gun_counter:
                    self.g.add((tank_uri, self.WOT.hasGun, gun_uri))
                    self.g.add((tank_uri, self.WOT.equipsWith, gun_uri))
            
            if pd.notna(row.get('engine')):
                engine_uri = self.WOT[f"Engine_{row['engine']}"]
                if engine_uri in self.engine_counter:
                    self.g.add((tank_uri, self.WOT.hasEngine, engine_uri))
                    self.g.add((tank_uri, self.WOT.equipsWith, engine_uri))
            
            if pd.notna(row.get('turret')):
                turret_uri = self.WOT[f"Turret_{row['turret']}"]
                if turret_uri in self.turret_counter:
                    self.g.add((tank_uri, self.WOT.hasTurret, turret_uri))
                    self.g.add((tank_uri, self.WOT.equipsWith, turret_uri))
            
            if pd.notna(row.get('suspension')):
                suspension_uri = self.WOT[f"Suspension_{row['suspension']}"]
                if suspension_uri in self.suspension_counter:
                    self.g.add((tank_uri, self.WOT.hasSuspension, suspension_uri))
                    self.g.add((tank_uri, self.WOT.equipsWith, suspension_uri))
            
            if pd.notna(row.get('radio')):
                radio_uri = self.WOT[f"Radio_{row['radio']}"]
                if radio_uri in self.radio_counter:
                    self.g.add((tank_uri, self.WOT.hasRadio, radio_uri))
                    self.g.add((tank_uri, self.WOT.equipsWith, radio_uri))
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(tanks_unique)} tanks")
        
        print(f"✅ Imported {len(tanks_unique)} tanks with module connections")
        print(f"   Tank Characteristics: {len(characteristics_counter)}")
        print(f"   Tank Roles: {len(roles_counter)}")
    
    def clean_data(self, df):
        """Очистка данных от некорректных значений"""
        print("\n🧹 Cleaning data...")
        initial_count = len(df)
        
        # Удаляем записи с пустыми критическими полями
        df = df.dropna(subset=['tank_id', 'name', 'display_name'])
        
        # Удаляем записи с нулевым или отрицательным уроном (некорректные бои)
        df = df[df['damage'] >= 0]
        
        # Удаляем записи с нулевым временем боя
        df = df[df['duration'] > 0]
        
        # Удаляем дубликаты (если есть)
        df = df.drop_duplicates()
        
        # Заменяем NaN на 0 для числовых полей
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        # Исправляем некорректные значения
        df['shots_fired'] = df['shots_fired'].clip(lower=0)
        df['direct_hits'] = df['direct_hits'].clip(lower=0, upper=df['shots_fired'])
        df['penetrations'] = df['penetrations'].clip(lower=0, upper=df['direct_hits'])
        
        cleaned_count = len(df)
        removed = initial_count - cleaned_count
        
        print(f"  ✅ Cleaned: {initial_count} → {cleaned_count} records")
        if removed > 0:
            print(f"  🗑️  Removed {removed} invalid records ({removed/initial_count*100:.1f}%)")
        
        return df
    
    def import_battles_from_tomato(self, limit=10000, random_sample=True):
        """Импортирует данные о боях из tomato.csv"""
        print("\n" + "=" * 60)
        print(f"IMPORTING BATTLE DATA FROM tomato.csv")
        print(f"  Limit: {limit}")
        print(f"  Random sampling: {random_sample}")
        print("=" * 60)
        
        tomato_file = self.data_dir / "tomato.csv"
        if not tomato_file.exists():
            print(f"⚠️  File not found: {tomato_file}")
            return
        
        # Читаем данные
        if random_sample:
            # Сначала узнаем общее количество строк
            print("Counting total battles...")
            total_lines = sum(1 for _ in open(tomato_file)) - 1  # -1 для заголовка
            print(f"  Total battles in file: {total_lines:,}")
            
            if limit >= total_lines:
                print(f"  Loading all {total_lines:,} battles...")
                df = pd.read_csv(tomato_file)
            else:
                # Генерируем случайные индексы
                print(f"  Selecting {limit:,} random battles...")
                import numpy as np
                np.random.seed(42)  # Для воспроизводимости
                skip_idx = np.random.choice(range(1, total_lines + 1), 
                                           size=total_lines - limit, 
                                           replace=False)
                df = pd.read_csv(tomato_file, skiprows=skip_idx)
        else:
            # Берем первые N записей
            print(f"Loading first {limit:,} battles...")
            df = pd.read_csv(tomato_file, nrows=limit)
        
        print(f"  Loaded {len(df):,} battle records")
        
        # Очищаем данные
        df = self.clean_data(df)
        
        # Показываем статистику по игрокам и танкам
        print(f"\n📊 Data statistics:")
        print(f"  Unique players: {df['display_name'].nunique()}")
        print(f"  Unique tanks: {df['tank_id'].nunique()}")
        print(f"  Nations: {', '.join(df['nation'].unique())}")
        print(f"  Classes: {', '.join(df['class'].unique())}")
        print(f"  Avg damage: {df['damage'].mean():.0f}")
        print(f"  Win rate: {df['won'].mean()*100:.1f}%")
        
        for idx, row in df.iterrows():
            # Создаем объекты
            battle_uri = self.normalize_battle_id(idx)
            perf_uri = self.normalize_performance_id(idx)
            tank_uri = self.normalize_tank_id(row['tank_id'])
            map_name = row.get('display_name')  # В этом поле реально хранится карта

            # === Battle ===
            self.g.add((battle_uri, RDF.type, self.WOT.Battle))

            # Время боя, длительность, победа, сторона, взвод — как раньше...
            if pd.notna(row.get('battle_time')):
                try:
                    battle_time = pd.to_datetime(row['battle_time'])
                    self.g.add((battle_uri, self.WOT.battleTime,
                                Literal(battle_time, datatype=XSD.dateTime)))
                except:
                    pass

            if pd.notna(row.get('duration')):
                self.g.add((battle_uri, self.WOT.duration,
                            Literal(int(row['duration']), datatype=XSD.integer)))

            if pd.notna(row.get('won')):
                self.g.add((battle_uri, self.WOT.won,
                            Literal(bool(row['won']), datatype=XSD.boolean)))

            if pd.notna(row.get('spawn')):
                self.g.add((battle_uri, self.WOT.spawn,
                            Literal(int(row['spawn']), datatype=XSD.integer)))

            if pd.notna(row.get('platoon')):
                self.g.add((battle_uri, self.WOT.platoon,
                            Literal(int(row['platoon']), datatype=XSD.integer)))

            # Новое: сохраняем карту как Battle.onMap (datatype string)
            if pd.notna(map_name):
                self.g.add((battle_uri, self.WOT.onMap,
                            Literal(str(map_name), datatype=XSD.string)))
                self.map_counter[map_name] = self.map_counter.get(map_name, 0) + 1

            # === Tank === (как раньше, если не был создан)
            if tank_uri not in self.tank_counter:
                tank_type = self.map_class_to_type(row.get('class', 'Tank'))
                self.g.add((tank_uri, RDF.type, tank_type))
                self.g.add((tank_uri, self.WOT.tankName,
                            Literal(row['name'], datatype=XSD.string)))
                if pd.notna(row.get('tier')):
                    self.g.add((tank_uri, self.WOT.tier,
                                Literal(int(row['tier']), datatype=XSD.integer)))
                if pd.notna(row.get('nation')):
                    nation_uri = self.map_nation_to_uri(row['nation'])
                    self.g.add((tank_uri, self.WOT.belongsToNation, nation_uri))
                if pd.notna(row.get('max_health')):
                    self.g.add((tank_uri, self.WOT.maxHP,
                                Literal(int(row['max_health']), datatype=XSD.integer)))
                self.tank_counter[tank_uri] = 0

            self.tank_counter[tank_uri] += 1

            # === BattlePerformance ===
            self.g.add((perf_uri, RDF.type, self.WOT.BattlePerformance))

            # Связи (без achievedBy):
            self.g.add((perf_uri, self.WOT.inBattle, battle_uri))
            self.g.add((perf_uri, self.WOT.withTank, tank_uri))
            self.g.add((battle_uri, self.WOT.hasPerformance, perf_uri))
            
            # Урон
            for field in ['damage', 'sniperDamage', 'damageReceived', 
                         'damageReceivedFromInvisible', 'potentialDamageReceived', 
                         'damageBlocked']:
                snake_field = ''.join(['_'+c.lower() if c.isupper() else c for c in field]).lstrip('_')
                if pd.notna(row.get(snake_field)):
                    self.g.add((perf_uri, self.WOT[field], 
                              Literal(int(row[snake_field]), datatype=XSD.integer)))
            
            # Стрельба
            for field in ['shotsFired', 'directHits', 'penetrations', 'hitsReceived', 
                         'penetrationsReceived', 'splashHitsReceived']:
                snake_field = ''.join(['_'+c.lower() if c.isupper() else c for c in field]).lstrip('_')
                if pd.notna(row.get(snake_field)):
                    self.g.add((perf_uri, self.WOT[field], 
                              Literal(int(row[snake_field]), datatype=XSD.integer)))
            
            # Действия
            for field in ['spots', 'frags', 'trackingAssist', 'spottingAssist']:
                snake_field = ''.join(['_'+c.lower() if c.isupper() else c for c in field]).lstrip('_')
                if pd.notna(row.get(snake_field)):
                    self.g.add((perf_uri, self.WOT[field], 
                              Literal(int(row[snake_field]), datatype=XSD.integer)))
            
            # База
            for field in ['baseDefensePoints', 'baseCapturePoints']:
                snake_field = ''.join(['_'+c.lower() if c.isupper() else c for c in field]).lstrip('_')
                if pd.notna(row.get(snake_field)):
                    self.g.add((perf_uri, self.WOT[field], 
                              Literal(int(row[snake_field]), datatype=XSD.integer)))
            
            # Прочее
            if pd.notna(row.get('life_time')):
                self.g.add((perf_uri, self.WOT.lifeTime, 
                          Literal(int(row['life_time']), datatype=XSD.integer)))
            
            if pd.notna(row.get('distance_traveled')):
                self.g.add((perf_uri, self.WOT.distanceTraveled, 
                          Literal(int(row['distance_traveled']), datatype=XSD.integer)))
            
            if pd.notna(row.get('base_xp')):
                self.g.add((perf_uri, self.WOT.baseXP, 
                          Literal(int(row['base_xp']), datatype=XSD.integer)))
            
            # Прогресс
            if (idx + 1) % 1000 == 0:
                print(f"  Processed {idx + 1}/{len(df)} battles")
        
        self.battle_counter = len(df)
        
        print(f"✅ Imported {len(df)} battles")
        print(f"   Unique tanks: {len(self.tank_counter)}")
    
    def save_graph(self, output_name="wot_with_data"):
        """Сохраняет граф в OWL файл"""
        print("\n" + "=" * 60)
        print("SAVING KNOWLEDGE GRAPH")
        print("=" * 60)
        
        # Сохраняем только в OWL формат (RDF/XML)
        filename = f'{output_name}.owl'
        filepath = self.ontology_dir / filename
        
        print(f"Saving {filename}...")
        self.g.serialize(destination=str(filepath), format='xml')
        file_size = filepath.stat().st_size / (1024 * 1024)  # MB
        print(f"  ✅ Saved: {filepath}")
        print(f"  📦 File size: {file_size:.2f} MB")
        
        print(f"\n📊 Final statistics:")
        print(f"   Total triples: {len(self.g):,}")
        print(f"   Tanks: {len(self.tank_counter)}")
        print(f"   Maps: {len(self.map_counter)}")
        print(f"   Battles: {self.battle_counter if hasattr(self, 'battle_counter') else 'N/A'}")
        print(f"   Guns: {len(self.gun_counter)}")
        print(f"   Engines: {len(self.engine_counter)}")
        print(f"   Turrets: {len(self.turret_counter)}")
        print(f"   Suspensions: {len(self.suspension_counter)}")
        print(f"   Radios: {len(self.radio_counter)}")


def main():
    parser = argparse.ArgumentParser(description='Import WoT data to RDF Knowledge Graph')
    parser.add_argument('--battles', type=int, default=30000,
                       help='Number of battles to import (default: 30000)')
    parser.add_argument('--tanks', type=int, default=None, 
                       help='Number of tank configs to import (default: all)')
    parser.add_argument('--output', type=str, default='wot_with_data', 
                       help='Output filename prefix (default: wot_with_data)')
    parser.add_argument('--no-random', action='store_true',
                       help='Disable random sampling (take first N battles)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WORLD OF TANKS KNOWLEDGE GRAPH - DATA IMPORTER")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Battles to import: {args.battles:,}")
    print(f"  Tanks to import: {args.tanks if args.tanks else 'all'}")
    print(f"  Random sampling: {not args.no_random}")
    print(f"  Output filename: {args.output}")
    
    # Находим онтологию
    ontology_file = Path(__file__).parent.parent / "ontology" / "wot_ontology.owl"
    
    if not ontology_file.exists():
        print(f"\n❌ Ontology not found: {ontology_file}")
        print("Please run create_ontology.py first!")
        return
    
    # Создаем импортер
    importer = DataImporter(ontology_file)
    
    # Импортируем данные о танках
    importer.import_tanks_from_wot_data(limit=args.tanks)
    
    # Импортируем данные о боях
    # importer.import_battles_from_tomato(limit=args.battles, random_sample=not args.no_random)
    
    # Сохраняем
    importer.save_graph(output_name=args.output)
    
    print("\n" + "=" * 60)
    print("✅ DATA IMPORT COMPLETED!")
    print("=" * 60)
    print(f"\nYou can now:")
    print(f"  1. Open {args.output}.owl in Protégé")
    print(f"  2. Run SPARQL queries")
    print(f"  3. Analyze the knowledge graph")


if __name__ == "__main__":
    main()

