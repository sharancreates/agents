import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

# Load environment variables from the .env file
load_dotenv()

def init_db():
    try:
        # Connect to the PostgreSQL container running in Docker
        connection = psycopg2.connect(os.getenv("DATABASE_URL"))
        cursor = connection.cursor()
        
        # 1. Initialize the pgvector extension inside the database
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        connection.commit()
        print("✅ Success: pgvector extension is active!")
        
        # 2. Register pgvector with psycopg2 so Python understands vector types
        register_vector(connection)
        
        # 3. Create a test table for code snippet embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_embeddings (
                id SERIAL PRIMARY KEY,
                file_path TEXT NOT NULL,
                function_name TEXT,
                embedding vector(3) -- Creating a simple 3-dimensional vector for testing
            );
        """)
        connection.commit()
        print("✅ Success: code_embeddings table created!")
        
        # Close connection
        cursor.close()
        connection.close()
        
    except Exception as error:
        print(f"❌ Error connecting to the database: {error}")

if __name__ == "__main__":
    init_db()