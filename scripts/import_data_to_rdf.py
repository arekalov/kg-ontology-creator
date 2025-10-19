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
        self.player_counter = {}
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
    
    def normalize_player_name(self, display_name):
        """Создает URI для игрока"""
        # Заменяем пробелы и спецсимволы
        safe_name = display_name.replace(" ", "_").replace("-", "_")
        return self.WOT[f"Player_{safe_name}"]
    
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
        
        for idx, row in tanks_unique.iterrows():
            tank_name = row['name']
            
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
            
            # Характеристики
            if pd.notna(row.get('hp')):
                self.g.add((tank_uri, self.WOT.maxHP, Literal(int(row['hp']), datatype=XSD.integer)))
            
            if pd.notna(row.get('weight')):
                self.g.add((tank_uri, self.WOT.weight, Literal(int(row['weight']), datatype=XSD.integer)))
            
            # Премиум статус
            if pd.notna(row.get('is_premium')):
                self.g.add((tank_uri, self.WOT.isPremium, Literal(bool(row['is_premium']), datatype=XSD.boolean)))
            
            if pd.notna(row.get('is_wheeled')):
                self.g.add((tank_uri, self.WOT.isWheeled, Literal(bool(row['is_wheeled']), datatype=XSD.boolean)))
            
            # Цены
            if pd.notna(row.get('price_credit')):
                self.g.add((tank_uri, self.WOT.priceCredit, Literal(int(row['price_credit']), datatype=XSD.integer)))
            
            if pd.notna(row.get('price_gold')):
                self.g.add((tank_uri, self.WOT.priceGold, Literal(int(row['price_gold']), datatype=XSD.integer)))
            
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(tanks_unique)} tanks")
        
        print(f"✅ Imported {len(tanks_unique)} tanks")
    
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
            player_uri = self.normalize_player_name(row['display_name'])
            
            # === Battle ===
            self.g.add((battle_uri, RDF.type, self.WOT.Battle))
            
            # Время боя
            if pd.notna(row.get('battle_time')):
                try:
                    battle_time = pd.to_datetime(row['battle_time'])
                    self.g.add((battle_uri, self.WOT.battleTime, 
                              Literal(battle_time, datatype=XSD.dateTime)))
                except:
                    pass
            
            # Продолжительность
            if pd.notna(row.get('duration')):
                self.g.add((battle_uri, self.WOT.duration, 
                          Literal(int(row['duration']), datatype=XSD.integer)))
            
            # Победа
            if pd.notna(row.get('won')):
                self.g.add((battle_uri, self.WOT.won, 
                          Literal(bool(row['won']), datatype=XSD.boolean)))
            
            # Сторона
            if pd.notna(row.get('spawn')):
                self.g.add((battle_uri, self.WOT.spawn, 
                          Literal(int(row['spawn']), datatype=XSD.integer)))
            
            # Взвод
            if pd.notna(row.get('platoon')):
                self.g.add((battle_uri, self.WOT.platoon, 
                          Literal(int(row['platoon']), datatype=XSD.integer)))
            
            # === Player (если еще не создан) ===
            if player_uri not in self.player_counter:
                self.g.add((player_uri, RDF.type, self.WOT.Player))
                self.g.add((player_uri, self.WOT.displayName, 
                          Literal(row['display_name'], datatype=XSD.string)))
                self.player_counter[player_uri] = 0
            
            self.player_counter[player_uri] += 1
            
            # === Tank (обновляем данные из tomato если танка нет) ===
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
            
            # Связи
            self.g.add((perf_uri, self.WOT.inBattle, battle_uri))
            self.g.add((perf_uri, self.WOT.withTank, tank_uri))
            self.g.add((perf_uri, self.WOT.achievedBy, player_uri))
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
        print(f"   Unique players: {len(self.player_counter)}")
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
        print(f"   Players: {len(self.player_counter)}")
        print(f"   Tanks: {len(self.tank_counter)}")
        print(f"   Battles: {self.battle_counter if hasattr(self, 'battle_counter') else 'N/A'}")


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
    importer.import_battles_from_tomato(limit=args.battles, random_sample=not args.no_random)
    
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

