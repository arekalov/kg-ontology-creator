#!/usr/bin/env python3
"""
Скрипт для работы с онтологией World of Tanks и выполнения SPARQL запросов
"""

from rdflib import Graph, Namespace
from pathlib import Path
import argparse
import time

class OntologyQueryEngine:
    def __init__(self, ontology_file):
        """Инициализация движка запросов"""
        self.g = Graph()
        self.ontology_file = Path(ontology_file)
        
        # Namespace
        self.WOT = Namespace("http://www.semanticweb.org/ontology/wot#")
        self.g.bind("wot", self.WOT)
        
        print("=" * 60)
        print("WORLD OF TANKS ONTOLOGY QUERY ENGINE")
        print("=" * 60)
        
        # Загружаем онтологию
        print(f"\n📂 Loading ontology: {self.ontology_file.name}")
        start_time = time.time()
        
        try:
            self.g.parse(str(self.ontology_file), format='xml')
            load_time = time.time() - start_time
            
            print(f"✅ Loaded successfully in {load_time:.2f} seconds")
            print(f"📊 Total triples: {len(self.g):,}")
            
        except Exception as e:
            print(f"❌ Error loading ontology: {e}")
            raise
    
    def execute_query(self, query, description=None):
        """Выполняет SPARQL запрос"""
        if description:
            print(f"\n{'=' * 60}")
            print(f"🔍 {description}")
            print(f"{'=' * 60}")
        
        try:
            start_time = time.time()
            results = self.g.query(query)
            query_time = time.time() - start_time
            
            result_list = list(results)
            print(f"\n⏱️  Query executed in {query_time:.3f} seconds")
            print(f"📋 Results: {len(result_list)} rows\n")
            
            return result_list
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return []
    
    def print_results(self, results, limit=None):
        """Печатает результаты запроса"""
        if not results:
            print("No results found.")
            return
        
        # Определяем ширину колонок
        if results:
            headers = list(results[0].labels)
            col_widths = {h: len(str(h)) for h in headers}
            
            # Вычисляем максимальную ширину для каждой колонки
            for row in results[:100]:  # Проверяем первые 100 строк
                for header in headers:
                    value = row[header]
                    if value:
                        value_str = self.format_value(value)
                        col_widths[header] = max(col_widths[header], len(value_str))
            
            # Ограничиваем ширину колонок
            for header in headers:
                col_widths[header] = min(col_widths[header], 50)
        
        # Печатаем заголовки
        header_line = " | ".join([h.ljust(col_widths[h]) for h in headers])
        print(header_line)
        print("-" * len(header_line))
        
        # Печатаем строки
        display_results = results[:limit] if limit else results
        for row in display_results:
            row_values = []
            for header in headers:
                value = row[header]
                value_str = self.format_value(value) if value else ""
                row_values.append(value_str.ljust(col_widths[header]))
            print(" | ".join(row_values))
        
        if limit and len(results) > limit:
            print(f"\n... and {len(results) - limit} more rows")
    
    def format_value(self, value):
        """Форматирует значение для вывода"""
        value_str = str(value)
        
        # Убираем namespace из URI
        if "http://www.semanticweb.org/ontology/wot#" in value_str:
            value_str = value_str.split("#")[-1]
        
        # Форматируем числа
        if value_str.replace('.', '').replace('-', '').isdigit():
            try:
                num = float(value_str)
                if num.is_integer():
                    return str(int(num))
                else:
                    return f"{num:.2f}"
            except:
                pass
        
        # Ограничиваем длину строки
        if len(value_str) > 50:
            return value_str[:47] + "..."
        
        return value_str
    
    def get_statistics(self):
        """Получает статистику по онтологии"""
        print("\n" + "=" * 60)
        print("📊 ONTOLOGY STATISTICS")
        print("=" * 60)
        
        # Количество классов
        class_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT (COUNT(DISTINCT ?class) AS ?count)
        WHERE {
          ?class rdf:type owl:Class .
        }
        """
        
        # Количество инстансов по классам
        instances_query = """
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?class (COUNT(?instance) AS ?count)
        WHERE {
          ?instance rdf:type ?class .
          FILTER(STRSTARTS(STR(?class), "http://www.semanticweb.org/ontology/wot#"))
        }
        GROUP BY ?class
        ORDER BY DESC(?count)
        """
        
        print("\n🎯 Instances by class:")
        results = self.execute_query(instances_query)
        self.print_results(results, limit=20)
    
    # ==================== ПРЕДОПРЕДЕЛЕННЫЕ ЗАПРОСЫ ====================
    
    def query_top_tanks_by_winrate(self, min_battles=50, limit=10):
        """Топ танков по проценту побед"""
        query = f"""
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        
        SELECT ?tankName 
               (COUNT(?perf) AS ?totalBattles)
               ((SUM(IF(?won, 1, 0)) * 100.0 / COUNT(?perf)) AS ?winRate)
        WHERE {{
          ?perf wot:withTank ?tank .
          ?perf wot:inBattle ?battle .
          ?battle wot:won ?won .
          ?tank wot:tankName ?tankName .
        }}
        GROUP BY ?tankName
        HAVING (COUNT(?perf) > {min_battles})
        ORDER BY DESC(?winRate)
        LIMIT {limit}
        """
        
        results = self.execute_query(query, f"Top {limit} Tanks by Win Rate (min {min_battles} battles)")
        self.print_results(results)
    
    def query_average_damage_by_class(self):
        """Средний урон по классам танков"""
        query = """
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
        """
        
        results = self.execute_query(query, "Average Damage by Tank Class")
        self.print_results(results)
    
    def query_best_players(self, limit=10):
        """Лучшие игроки по среднему урону"""
        query = f"""
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        
        SELECT ?playerName 
               (AVG(?damage) AS ?avgDamage)
               (AVG(?frags) AS ?avgFrags)
               (COUNT(?perf) AS ?battles)
        WHERE {{
          ?perf wot:achievedBy ?player .
          ?perf wot:damage ?damage .
          ?perf wot:frags ?frags .
          ?player wot:displayName ?playerName .
        }}
        GROUP BY ?playerName
        ORDER BY DESC(?avgDamage)
        LIMIT {limit}
        """
        
        results = self.execute_query(query, f"Top {limit} Players by Average Damage")
        self.print_results(results)
    
    def query_tanks_by_nation(self, nation):
        """Танки определенной нации"""
        query = f"""
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?tankName ?tier ?type
        WHERE {{
          ?tank wot:belongsToNation wot:{nation} .
          ?tank wot:tankName ?tankName .
          ?tank wot:tier ?tier .
          ?tank rdf:type ?type .
          FILTER(?type IN (wot:HeavyTank, wot:MediumTank, wot:LightTank, 
                          wot:TankDestroyer, wot:SelfPropelledGun))
        }}
        ORDER BY ?tier ?tankName
        """
        
        results = self.execute_query(query, f"Tanks of Nation: {nation}")
        self.print_results(results, limit=30)
    
    def query_spotting_masters(self, limit=10):
        """Танки лучшие для засвета"""
        query = f"""
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        
        SELECT ?tankName 
               (AVG(?spots) AS ?avgSpots)
               (AVG(?spottingAssist) AS ?avgSpottingDmg)
               (COUNT(?perf) AS ?battles)
        WHERE {{
          ?perf wot:withTank ?tank .
          ?perf wot:spots ?spots .
          ?perf wot:spottingAssist ?spottingAssist .
          ?tank wot:tankName ?tankName .
        }}
        GROUP BY ?tankName
        HAVING (AVG(?spots) > 0.5)
        ORDER BY DESC(?avgSpots)
        LIMIT {limit}
        """
        
        results = self.execute_query(query, f"Top {limit} Tanks for Spotting")
        self.print_results(results)
    
    def query_guns_with_highest_dpm(self, limit=10):
        """Орудия с максимальным DPM"""
        query = f"""
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        
        SELECT ?gunName ?dpm ?avgDamage ?fireRate
        WHERE {{
          ?gun rdf:type wot:Gun .
          ?gun wot:gunName ?gunName .
          ?gun wot:dpm ?dpm .
          OPTIONAL {{ ?gun wot:avgDamage ?avgDamage }}
          OPTIONAL {{ ?gun wot:fireRate ?fireRate }}
        }}
        ORDER BY DESC(?dpm)
        LIMIT {limit}
        """
        
        results = self.execute_query(query, f"Top {limit} Guns by DPM")
        self.print_results(results)
    
    def query_engines_by_power(self, limit=10):
        """Двигатели по мощности"""
        query = f"""
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?engine ?power
        WHERE {{
          ?engine rdf:type wot:Engine .
          ?engine wot:power ?power .
        }}
        ORDER BY DESC(?power)
        LIMIT {limit}
        """
        
        results = self.execute_query(query, f"Top {limit} Engines by Power")
        self.print_results(results)
    
    def query_nation_statistics(self):
        """Статистика по нациям"""
        query = """
        PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
        
        SELECT ?nationName
               (COUNT(?perf) AS ?battles)
               ((SUM(IF(?won, 1, 0)) * 100.0 / COUNT(?perf)) AS ?winRate)
               (AVG(?damage) AS ?avgDamage)
        WHERE {
          ?perf wot:withTank ?tank .
          ?perf wot:inBattle ?battle .
          ?perf wot:damage ?damage .
          ?battle wot:won ?won .
          ?tank wot:belongsToNation ?nation .
          ?nation wot:nationName ?nationName .
        }
        GROUP BY ?nationName
        ORDER BY DESC(?winRate)
        """
        
        results = self.execute_query(query, "Statistics by Nation")
        self.print_results(results)
    
    def interactive_mode(self):
        """Интерактивный режим для выполнения произвольных запросов"""
        print("\n" + "=" * 60)
        print("🎮 INTERACTIVE MODE")
        print("=" * 60)
        print("\nEnter SPARQL query (type 'exit' to quit, 'help' for examples):\n")
        
        while True:
            try:
                print("\n" + ">" * 60)
                lines = []
                while True:
                    line = input()
                    if line.strip().lower() == 'exit':
                        return
                    if line.strip().lower() == 'help':
                        self.show_help()
                        break
                    lines.append(line)
                    if line.strip().endswith('}') or line.strip().endswith(';'):
                        break
                
                if lines:
                    query = '\n'.join(lines)
                    results = self.execute_query(query)
                    self.print_results(results, limit=50)
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def show_help(self):
        """Показывает примеры запросов"""
        print("\n" + "=" * 60)
        print("📚 QUERY EXAMPLES")
        print("=" * 60)
        
        examples = {
            "All tanks": """
PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
SELECT ?tank ?name WHERE {
  ?tank wot:tankName ?name .
} LIMIT 10
            """,
            
            "Heavy tanks tier 10": """
PREFIX wot: <http://www.semanticweb.org/ontology/wot#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?name ?hp WHERE {
  ?tank rdf:type wot:HeavyTank .
  ?tank wot:tier 10 .
  ?tank wot:tankName ?name .
  OPTIONAL { ?tank wot:maxHP ?hp }
}
            """
        }
        
        for title, query in examples.items():
            print(f"\n### {title}:")
            print(query)


def main():
    parser = argparse.ArgumentParser(description='Query World of Tanks Ontology')
    parser.add_argument('--ontology', type=str, 
                       default='ontology/wot_with_data.owl',
                       help='Path to ontology file')
    parser.add_argument('--query', type=str, 
                       help='Predefined query to run')
    parser.add_argument('--interactive', action='store_true',
                       help='Start interactive mode')
    parser.add_argument('--stats', action='store_true',
                       help='Show ontology statistics')
    
    args = parser.parse_args()
    
    # Определяем путь к онтологии
    ontology_path = Path(__file__).parent.parent / args.ontology
    
    if not ontology_path.exists():
        print(f"❌ Ontology file not found: {ontology_path}")
        print("\nAvailable files:")
        ontology_dir = ontology_path.parent
        if ontology_dir.exists():
            for f in ontology_dir.glob("*.owl"):
                print(f"  - {f.name}")
        return
    
    # Создаем движок запросов
    engine = OntologyQueryEngine(ontology_path)
    
    # Статистика
    if args.stats:
        engine.get_statistics()
        return
    
    # Предопределенные запросы
    if args.query:
        query_map = {
            'top-tanks': lambda: engine.query_top_tanks_by_winrate(limit=10),
            'damage-by-class': lambda: engine.query_average_damage_by_class(),
            'best-players': lambda: engine.query_best_players(limit=10),
            'ussr-tanks': lambda: engine.query_tanks_by_nation('USSR'),
            'germany-tanks': lambda: engine.query_tanks_by_nation('Germany'),
            'spotting': lambda: engine.query_spotting_masters(limit=10),
            'guns': lambda: engine.query_guns_with_highest_dpm(limit=15),
            'engines': lambda: engine.query_engines_by_power(limit=15),
            'nations': lambda: engine.query_nation_statistics(),
        }
        
        if args.query in query_map:
            query_map[args.query]()
        else:
            print(f"❌ Unknown query: {args.query}")
            print("\nAvailable queries:")
            for key in query_map.keys():
                print(f"  - {key}")
        return
    
    # Интерактивный режим
    if args.interactive:
        engine.interactive_mode()
        return
    
    # По умолчанию - показываем несколько запросов
    print("\n" + "=" * 60)
    print("🚀 RUNNING SAMPLE QUERIES")
    print("=" * 60)
    
    engine.query_average_damage_by_class()
    engine.query_top_tanks_by_winrate(limit=5)
    engine.query_best_players(limit=5)
    
    print("\n" + "=" * 60)
    print("💡 TIP: Use --query <name> or --interactive for more options")
    print("   Run with --help to see all options")
    print("=" * 60)


if __name__ == "__main__":
    main()

