# Text to Neo4j Knowledge Graph Builder

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Neo4j](https://img.shields.io/badge/Neo4j-4.4%2B-green)
![Ollama](https://img.shields.io/badge/Ollama-3.2:1B-orange)
![LangChain](https://img.shields.io/badge/LangChain-Latest-red)

A Python script that extracts entities and relationships from text files using Ollama's LLM and builds a knowledge graph in Neo4j.

## Features

- 📄 Processes multiple `.txt` files from an `Input` folder
- 🧠 Uses Ollama's LLM (llama3.2:1b by default) for intelligent entity and relationship extraction
- 🗃️ Stores extracted knowledge as nodes and relationships in Neo4j
- 🔄 Handles large documents with smart text chunking using LangChain
- 🏷️ Automatic node labeling with sanitized types and relationship typing
- 🔗 Structured output using Pydantic models for reliable data extraction

## Prerequisites

### Required Software
- **Python 3.8+**
- **[Neo4j Desktop](https://neo4j.com/download/) or Neo4j Community Server** running locally on port 7687
- **[Ollama](https://ollama.ai/)** running locally on port 11434
- **llama3.2:1b model** (or your preferred model) downloaded in Ollama

### Required Python Packages
```bash
pip install neo4j python-dotenv langchain langchain-core langchain-ollama
```

## Installation

1. **Clone or download the project:**
   ```bash
   # Create project directory
   mkdir text-to-neo4j
   cd text-to-neo4j
   ```

2. **Install Python dependencies:**
   ```bash
   pip install neo4j python-dotenv langchain langchain-core langchain-ollama
   ```

3. **Set up Neo4j:**
   - Start your Neo4j database
   - Note your password (default user is `neo4j`)

4. **Set up Ollama:**
   ```bash
   # Install and pull the model
   ollama pull llama3.2:1b
   ```

5. **Configure the script:**
   Edit `Text_to_Neo4J.py` and update these variables:
   ```python
   NEO4J_PASSWORD = "your_actual_password_here"  # Replace with your Neo4j password
   OLLAMA_MODEL = "llama3.2:1b"  # Or your preferred model
   ```

6. **Create the Input folder:**
   ```bash
   mkdir Input
   ```

## Project Structure

```
text-to-neo4j/
├── Text_to_Neo4J.py          # Main script
├── Input/                    # Place your .txt files here
│   ├── document1.txt
│   ├── document2.txt
│   └── ...
└── README.md
```

## Usage

1. **Place your text files** in the `Input` folder (only `.txt` files are processed)

2. **Run the script:**
   ```bash
   python Text_to_Neo4J.py
   ```

3. **View your knowledge graph** in Neo4j Browser at `http://localhost:7474`

4. **Query your graph** using Cypher. Try these example queries:
   ```cypher
   // View all nodes and relationships
   MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50
   
   // View all entities
   MATCH (n:Entity) RETURN n LIMIT 25
   
   // Find specific entity types
   MATCH (n:Person) RETURN n.name
   
   // Explore relationships of a specific entity
   MATCH (n {id: "EntityName"})-[r]-(connected) 
   RETURN n, r, connected
   ```

5. **Optional: Clear existing data** before running (as suggested by the script):
   ```cypher
   MATCH (n) DETACH DELETE n
   ```

## How It Works

1. **Text Processing**: Files are split into chunks of 512 characters with 50-character overlap
2. **Entity Extraction**: Each chunk is processed by Ollama to identify entities and relationships
3. **Graph Storage**: Extracted data is stored in Neo4j with:
   - Nodes labeled by sanitized entity types
   - Relationships with UPPERCASE_SNAKE_CASE types
   - All nodes also labeled as `:Entity` for easy querying

## Input/Output Example

**Input text (example.txt):**
```
Elon Musk founded SpaceX in 2002. Tesla, another company he leads, develops electric vehicles.
```

**Resulting Neo4j Graph:**
- **Nodes:**
  - `Elon Musk` (Person, Entity)
  - `SpaceX` (Company, Entity)  
  - `Tesla` (Company, Entity)
  - `Electric Vehicles` (Technology, Entity)

- **Relationships:**
  - `(Elon Musk)-[:FOUNDED]->(SpaceX)`
  - `(Elon Musk)-[:LEADS]->(Tesla)`
  - `(Tesla)-[:DEVELOPS]->(Electric Vehicles)`

## Configuration Options

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.2:1b` |
| `OLLAMA_BASE_URL` | Ollama service URL | `http://localhost:11434` |
| `chunk_size` | Text chunk size for processing | `512` |
| `chunk_overlap` | Overlap between text chunks | `50` |

## Troubleshooting

### Common Issues

- **❌ Failed to connect to Neo4j**: 
  - Verify Neo4j is running on port 7687
  - Check your username/password in the script
  - Ensure bolt connector is enabled

- **❌ No .txt files found**: 
  - Make sure you have an `Input` folder in the same directory as the script
  - Verify your files have `.txt` extension

- **❌ Error invoking Ollama**: 
  - Ensure Ollama is running: `ollama serve`
  - Check if your model is available: `ollama list`
  - Try pulling the model again: `ollama pull llama3.2:1b`

- **⚠️ Nothing extracted**: 
  - Try a larger/different Ollama model
  - Adjust chunk size for your text type
  - Check if your text contains clear entities and relationships

### Performance Tips

- Use smaller models (like `llama3.2:1b`) for faster processing
- Adjust chunk sizes based on your document structure
- For large datasets, consider processing files in batches

## Dependencies

The script uses these key libraries:
- `neo4j`: Neo4j Python driver
- `langchain`: Text splitting and LLM integration
- `langchain-ollama`: Ollama integration for LangChain
- `python-dotenv`: Environment variable loading (optional)

## License

MIT License - Feel free to use and modify as needed.
