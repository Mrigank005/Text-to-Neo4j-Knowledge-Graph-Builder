# Text to Neo4j Knowledge Graph Builder

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Neo4j](https://img.shields.io/badge/Neo4j-4.4%2B-green)
![Ollama](https://img.shields.io/badge/Ollama-3.1:8B-orange)
![LangChain](https://img.shields.io/badge/LangChain-Latest-red)

A Python script that extracts entities and relationships from text files using Ollama's LLM and builds a knowledge graph in Neo4j.

## Features

- 📄 Processes multiple `.txt` files from an `Input` folder
- 🧠 Uses Ollama's LLM (llama3.1:8B by default) for intelligent entity and relationship extraction
- 🗃️ Stores extracted knowledge as nodes and relationships in Neo4j
- 🔄 Handles large documents with smart text chunking using LangChain
- 🏷️ Automatic node labeling with sanitized types and relationship typing
- 🔗 Structured output using Pydantic models for reliable data extraction
- 🔍 Includes Neo4j data explorer with NLP capabilities (in `Neo4j_Data_Retrival_NLP.py`)

## Project Structure

```
Text-to-Neo4j-Knowledge-Graph-Builder/
├── Text_to_Neo4J.py          # Main data entry script
├── Neo4j_Data_Retrival_NLP.py # Interactive graph explorer with NLP
├── Input/                    # Place your .txt files here
│   ├── document1.txt
│   ├── document2.txt
│   └── ...
├── requirements.txt          # Python dependencies
├── LICENSE
└── README.md
```

## Prerequisites

### Required Software
- **Python 3.8+**
- **[Neo4j Desktop](https://neo4j.com/download/) or Neo4j Community Server** running locally on port 7687
- **[Ollama](https://ollama.ai/)** running locally on port 11434
- **llama3.1:8B model** (or your preferred model) downloaded in Ollama

### Required Python Packages
```bash
pip install -r requirements.txt
```

## Installation

1. **Clone or download the project:**
   ```bash
   git clone https://github.com/Mrigank005/Text-to-Neo4j-Knowledge-Graph-Builder.git
   cd Text-to-Neo4j-Knowledge-Graph-Builder
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Set up Neo4j:**
   - Start your Neo4j database
   - Note your password (default user is `neo4j`)

4. **Set up Ollama:**
   ```bash
   # Install and pull the model
   ollama pull llama3.2:1b
   ```

5. **Configure the scripts:**
   Edit the configuration variables in both scripts:
   ```python
   NEO4J_PASSWORD = "your_actual_password_here"  # Replace with your Neo4j password
   OLLAMA_MODEL = "llama3.2:1b"  # Or your preferred model
   ```

6. **Create the Input folder:**
   ```bash
   mkdir Input
   ```

## Usage

### 1. Data Entry (Text_to_Neo4J.py)
1. **Place your text files** in the `Input` folder
2. **Run the script:**
   ```bash
   python Text_to_Neo4J.py
   ```

### 2. Graph Exploration (Neo4j_Data_Retrival_NLP.py)
```bash
python Neo4j_Data_Retrival_NLP.py
```

Features:
- 🌐 Interactive graph statistics
- 🔍 Node search by ID or natural language
- 🛣️ Path finding between nodes
- 🔗 Relationship visualization
- 🧠 NLP-powered semantic search

## Example Queries

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

## Configuration Options

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.1:8B` |
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

## License

MIT License - Feel free to use and modify as needed.
