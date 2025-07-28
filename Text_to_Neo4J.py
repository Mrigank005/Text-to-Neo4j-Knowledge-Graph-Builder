import os
import glob
import json
import re
from typing import List, Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_ollama.chat_models import ChatOllama

# --- Configuration ---
# Load environment variables (optional)
# load_dotenv()

# Neo4j credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"  # 🔁 Replace this with your actual Neo4j password

# Ollama config
OLLAMA_MODEL = "llama3.2:1b"
OLLAMA_BASE_URL = "http://localhost:11434"

# --- Pydantic Models ---

class Node(BaseModel):
    id: str = Field(description="Unique identifier for the node, usually the entity name.")
    type: str = Field(description="Type/category of the node (e.g., Person, Technology).")

class Relationship(BaseModel):
    source: str = Field(description="ID of source node.")
    target: str = Field(description="ID of target node.")
    type: str = Field(description="Type of relationship in UPPERCASE_SNAKE_CASE format.")

class Graph(BaseModel):
    nodes: Optional[List[Node]] = Field(default_factory=list)
    relationships: Optional[List[Relationship]] = Field(default_factory=list)

# --- Neo4j Connection ---
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("✅ Successfully connected to Neo4j.")
except Exception as e:
    print(f"❌ Failed to connect to Neo4j: {e}")
    exit()

# --- Store Graph ---
def store_graph_in_neo4j(graph: Graph):
    if not graph or (not graph.nodes and not graph.relationships):
        print("⚠️ Graph is empty. Nothing to store.")
        return

    with driver.session() as session:
        # Store nodes
        for node in graph.nodes:
            label = ''.join(filter(str.isalnum, node.type.title().replace(" ", "")))
            if not label: continue
            query = f"""
            MERGE (n:{label} {{id: $id}})
            SET n.name = $id, n:Entity
            """
            session.run(query, id=node.id)

        # Store relationships
        for rel in graph.relationships:
            rel_type = re.sub(r'[^A-Z_]', '', rel.type.upper().replace(" ", "_"))
            if not rel_type: continue
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            """
            session.run(query, source_id=rel.source, target_id=rel.target)

# --- Extract Graph from Text using Ollama ---
def extract_graph_with_ollama(text_chunk: str) -> Optional[Graph]:
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.0
    ).with_structured_output(Graph)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are an expert in knowledge graph extraction. Your task is to analyze the provided text and identify all distinct entities and the relationships between them.

- Nodes: Have an 'id' (entity's name) and 'type' (e.g., Person, Technology).
- Relationships: Must include 'source', 'target', and a 'type' (verb phrase in UPPERCASE_SNAKE_CASE).

Output must be a JSON object with 'nodes' and 'relationships'.
"""),
        ("human", "Here is the text to analyze:\n\n{input_text}")
    ])

    chain = prompt | llm

    try:
        print("🔹 Invoking Ollama model for graph extraction...")
        result = chain.invoke({"input_text": text_chunk})
        return result
    except Exception as e:
        print(f"❌ Error invoking Ollama: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(script_dir, 'Input')
    txt_files = glob.glob(os.path.join(input_folder, '*.txt'))

    if not txt_files:
        print("❌ No .txt files found in 'Input' folder.")
        exit()

    print("ℹ️  Suggestion: Clear your Neo4j DB with 'MATCH (n) DETACH DELETE n' for a clean slate.\n")

    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)

    for txt_path in txt_files:
        print(f"\n📄 Processing file: {txt_path}")
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"❌ Error reading file {txt_path}: {e}")
            continue

        chunks = splitter.split_text(text)
        print(f"📄 Text split into {len(chunks)} chunk(s).")

        for i, chunk in enumerate(chunks):
            print(f"\n--- Processing Chunk {i + 1}/{len(chunks)} ---")
            extracted_graph = extract_graph_with_ollama(chunk)

            if extracted_graph and (extracted_graph.nodes or extracted_graph.relationships):
                print(f"✅ Extracted: {len(extracted_graph.nodes)} nodes, {len(extracted_graph.relationships)} relationships")
                store_graph_in_neo4j(extracted_graph)
                print("🧠 Stored successfully.")
            else:
                print("⚠️ Nothing extracted.")

    driver.close()
    print("\n🎉 All files processed. Graph construction complete.")
