from typing import Optional, Dict, List, Any
from neo4j import GraphDatabase
from collections import defaultdict
import os
import spacy  # For NLP processing
from spacy.cli import download  # For model download if needed

class Neo4jExplorer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        # Load the English language model for spaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy language model...")
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
    
    def close(self):
        self.driver.close()
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        with self.driver.session() as session:
            return {
                "node_count": session.run("MATCH (n) RETURN count(n)").single()[0],
                "rel_count": session.run("MATCH ()-[r]->() RETURN count(r)").single()[0],
                "labels": session.run("""
                    MATCH (n)
                    UNWIND labels(n) as label
                    RETURN label, count(*) as count
                    ORDER BY count DESC
                """).data(),
                "relationships": session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(*) as count
                    ORDER BY count DESC
                """).data()
            }
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node details by ID"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $node_id})
                RETURN n.id as id, labels(n) as labels, properties(n) as properties
            """, node_id=node_id).single()
            return dict(result) if result else None
    
    def search_nodes(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for nodes by ID"""
        with self.driver.session() as session:
            return session.run("""
                MATCH (n)
                WHERE toLower(n.id) CONTAINS toLower($term)
                RETURN n.id as id, labels(n) as labels
                LIMIT $limit
            """, term=search_term, limit=limit).data()
    
    def get_node_relationships(self, node_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all relationships for a node, grouped by type"""
        with self.driver.session() as session:
            rels = session.run("""
                MATCH (a {id: $node_id})-[r]-(b)
                RETURN type(r) as type, 
                       startNode(r).id as source, 
                       endNode(r).id as target,
                       labels(b) as target_labels
                ORDER BY type
            """, node_id=node_id).data()
            
            rel_dict = defaultdict(list)
            for rel in rels:
                rel_dict[rel["type"]].append({
                    "target": rel["target"],
                    "target_labels": rel["target_labels"],
                    "direction": "out" if rel["source"] == node_id else "in"
                })
            
            return dict(rel_dict)
    
    def find_paths(self, source_id: str, target_id: str, max_length: int = 3) -> List[Dict[str, Any]]:
        """Find paths between two nodes"""
        with self.driver.session() as session:
            return session.run(f"""
                MATCH path = shortestPath((a {{id: $source_id}})-[*..{max_length}]-(b {{id: $target_id}}))
                RETURN [node in nodes(path) | {{id: node.id, labels: labels(node)}}] as nodes,
                       [rel in relationships(path) | {{type: type(rel), source: startNode(rel).id, target: endNode(rel).id}}] as relationships
            """, source_id=source_id, target_id=target_id).data()
    
    def get_duplicate_relationships(self) -> List[Dict[str, Any]]:
        """Find potential duplicate relationships"""
        with self.driver.session() as session:
            return session.run("""
                MATCH (a)-[r]->(b)
                WITH a.id as source, b.id as target, type(r) as type, count(*) as count
                WHERE count > 1
                RETURN source, target, type, count
                ORDER BY count DESC
            """).data()
    
    def extract_search_terms(self, query: str) -> List[str]:
        """Extract relevant search terms from natural language query"""
        doc = self.nlp(query.lower())
        
        # Extract nouns, proper nouns, and adjectives as potential search terms
        search_terms = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop:
                # For multi-word entities (like "New York"), combine them
                if token.ent_type_ and token.ent_iob_ == "B":
                    span = doc[token.i:token.ent.end]
                    search_terms.append(" ".join([t.text for t in span]))
                else:
                    search_terms.append(token.lemma_)
        
        # Remove duplicates while preserving order
        seen = set()
        return [term for term in search_terms if not (term in seen or seen.add(term))]
    
    def semantic_search_nodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for nodes using natural language query"""
        search_terms = self.extract_search_terms(query)
        if not search_terms:
            return []
        
        with self.driver.session() as session:
            # Create a query that searches across multiple properties
            query = """
                MATCH (n)
                WHERE ANY(term IN $terms WHERE 
                    toLower(n.id) CONTAINS term OR
                    ANY(prop IN keys(n) WHERE 
                        toLower(prop) CONTAINS term OR
                        toLower(toString(n[prop])) CONTAINS term
                    )
                )
                RETURN DISTINCT n.id as id, labels(n) as labels, 
                       [term IN $terms WHERE 
                        toLower(n.id) CONTAINS term OR
                        ANY(prop IN keys(n) WHERE 
                            toLower(prop) CONTAINS term OR
                            toLower(toString(n[prop])) CONTAINS term
                        ) | term] as matched_terms
                ORDER BY size(matched_terms) DESC
                LIMIT $limit
            """
            return session.run(query, terms=search_terms, limit=limit).data()

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_node(node: Dict[str, Any]):
    """Display node information"""
    print(f"\n📌 Node: {node['id']}")
    print(f"🏷️  Labels: {', '.join(node['labels'])}")
    print("🔍 Properties:")
    for key, value in node['properties'].items():
        print(f"  - {key}: {value}")

def display_relationships(relationships: Dict[str, List[Dict[str, Any]]]):
    """Display relationships for a node"""
    print("\n🔗 Relationships:")
    for rel_type, targets in relationships.items():
        print(f"\n[{rel_type}]")
        for target in targets:
            direction = "→" if target["direction"] == "out" else "←"
            print(f"  {direction} {target['target']} ({', '.join(target['target_labels'])})")

def display_path(path: Dict[str, Any]):
    """Display a path between nodes"""
    print("\n🛣️ Path:")
    for i, node in enumerate(path["nodes"]):
        print(f"{i+1}. {node['id']} ({', '.join(node['labels'])})")
        if i < len(path["relationships"]):
            rel = path["relationships"][i]
            print(f"   --[{rel['type']}]-->")

def display_search_results(results: List[Dict[str, Any]]):
    """Display search results with matched terms"""
    if not results:
        print("\nNo nodes found matching your search.")
        return
    
    print("\n🔍 Search Results:")
    for i, node in enumerate(results, 1):
        matched_terms = node.get('matched_terms', [])
        term_info = f" (matched: {', '.join(matched_terms)})" if matched_terms else ""
        print(f"{i}. {node['id']} ({', '.join(node['labels'])}){term_info}")

def main_menu(explorer: Neo4jExplorer):
    """Main interactive menu"""
    while True:
        clear_screen()
        print("""
        🌐 Neo4j Knowledge Graph Explorer
        ================================
        1. View Graph Summary
        2. Search for Nodes
        3. Explore Node Details
        4. Find Paths Between Nodes
        5. Check for Duplicate Relationships
        6. Natural Language Search
        0. Exit
        """)
        
        choice = input("Enter your choice (0-6): ").strip()
        
        if choice == "0":
            break
            
        elif choice == "1":
            clear_screen()
            print("\n📊 Graph Summary")
            stats = explorer.get_graph_summary()
            print(f"\nTotal Nodes: {stats['node_count']}")
            print(f"Total Relationships: {stats['rel_count']}")
            
            print("\n🏷️ Node Labels (Count):")
            for label in stats["labels"]:
                print(f"- {label['label']}: {label['count']}")
            
            print("\n🔗 Relationship Types (Count):")
            for rel in stats["relationships"]:
                print(f"- {rel['type']}: {rel['count']}")
            
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            clear_screen()
            print("\nSearch options:")
            print("1. Exact ID search")
            print("2. Natural language search")
            search_choice = input("Choose search type (1-2): ").strip()
            
            if search_choice == "1":
                search_term = input("\nEnter search term: ").strip()
                if not search_term:
                    continue
                    
                results = explorer.search_nodes(search_term)
                display_search_results(results)
                
            elif search_choice == "2":
                query = input("\nEnter your natural language query: ").strip()
                if not query:
                    continue
                    
                print(f"\nExtracted search terms: {explorer.extract_search_terms(query)}")
                results = explorer.semantic_search_nodes(query)
                display_search_results(results)
            else:
                input("\nInvalid choice. Press Enter to continue...")
                continue
            
            input("\nPress Enter to continue...")
            
        elif choice == "3":
            clear_screen()
            node_id = input("\nEnter node ID: ").strip()
            if not node_id:
                continue
                
            node = explorer.get_node(node_id)
            if not node:
                print(f"\nNode '{node_id}' not found.")
            else:
                display_node(node)
                rels = explorer.get_node_relationships(node_id)
                display_relationships(rels)
            
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            clear_screen()
            source_id = input("\nEnter source node ID: ").strip()
            target_id = input("Enter target node ID: ").strip()
            if not source_id or not target_id:
                continue
                
            paths = explorer.find_paths(source_id, target_id)
            if not paths:
                print(f"\nNo path found between {source_id} and {target_id}")
            else:
                for path in paths:
                    display_path(path)
            
            input("\nPress Enter to continue...")
            
        elif choice == "5":
            clear_screen()
            duplicates = explorer.get_duplicate_relationships()
            if not duplicates:
                print("\nNo duplicate relationships found.")
            else:
                print("\n⚠️ Potential Duplicate Relationships:")
                for dup in duplicates:
                    print(f"\n{dup['source']} --[{dup['type']}]--> {dup['target']}")
                    print(f"Count: {dup['count']}")
            
            input("\nPress Enter to continue...")
            
        elif choice == "6":
            clear_screen()
            query = input("\nEnter your natural language query: ").strip()
            if not query:
                continue
                
            print(f"\nExtracted search terms: {explorer.extract_search_terms(query)}")
            results = explorer.semantic_search_nodes(query)
            display_search_results(results)
            
            input("\nPress Enter to continue...")
            
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # Configuration - Update these with your Neo4j credentials
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "password"  # Replace with your actual password
    
    try:
        explorer = Neo4jExplorer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        print("✅ Successfully connected to Neo4j")
        main_menu(explorer)
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'explorer' in locals():
            explorer.close()
        print("\nGoodbye!")