import os
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("OriginalityDBClient")

class DatabaseManager:
    """
    A thread-safe Database Manager for PostgreSQL featuring pgvector integration,
    connection pooling, and robust context management.
    """
    _pool = None

    @classmethod
    def initialize_pool(cls):
        """Initializes the connection pool using DATABASE_URL from .env."""
        if cls._pool is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable is not set.")
            
            try:
                # ThreadedConnectionPool is safe for multi-threaded applications
                cls._pool = pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=20,
                    dsn=database_url
                )
                logger.info("[DB] Connection pool initialized successfully.")
            except Exception as e:
                logger.error(f"[DB] Failed to initialize connection pool: {e}")
                raise

    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Context manager to acquire a connection from the pool,
        register pgvector, and return it back to the pool safely.
        """
        if cls._pool is None:
            cls.initialize_pool()

        conn = None
        try:
            conn = cls._pool.getconn()
            # Register pgvector type handler on the checked-out connection
            register_vector(conn)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"[DB] Database transaction error: {e}")
            raise
        finally:
            if conn and cls._pool:
                cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def get_cursor(cls, cursor_factory=None):
        """
        Context manager to get a cursor from a pooled connection.
        Yields the cursor, commits on success, and rolls back on error.
        """
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cursor:
                yield cursor

    @classmethod
    def setup_schema(cls, vector_dim: int = 1536):
        """
        Ensures the pgvector extension is active, creates the schema,
        and establishes optimal B-tree and HNSW indexes.
        """
        logger.info(f"[DB] Setting up database schema (vector dimension = {vector_dim})...")
        
        # 1. Enable extension and create table
        create_table_query = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        
        CREATE TABLE IF NOT EXISTS originality_embeddings (
            id SERIAL PRIMARY KEY,
            file_path TEXT NOT NULL,
            function_name VARCHAR(255) NOT NULL,
            signature TEXT,
            cleaned_source TEXT NOT NULL,
            embedding vector({vector_dim}) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_file_function UNIQUE (file_path, function_name)
        );
        """
        
        # 2. Build B-tree indexes for metadata filters
        create_btree_indexes = """
        CREATE INDEX IF NOT EXISTS idx_embeddings_file_path ON originality_embeddings (file_path);
        CREATE INDEX IF NOT EXISTS idx_embeddings_func_name ON originality_embeddings (function_name);
        """

        # 3. Build HNSW index for vector cosine similarity search (<=>)
        # HNSW is chosen for high recall, dynamic insertions, and fast search.
        # m = 16 (max connections per node), ef_construction = 64 (accuracy during index build)
        create_hnsw_cosine_index = f"""
        CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine 
        ON originality_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """

        # 4. Build HNSW index for inner product search (<#>)
        # (Useful if embeddings are normalized, which makes inner product fast & identical in ranking to cosine)
        create_hnsw_ip_index = f"""
        CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_ip 
        ON originality_embeddings 
        USING hnsw (embedding vector_ip_ops)
        WITH (m = 16, ef_construction = 64);
        """

        try:
            with cls.get_cursor() as cursor:
                cursor.execute(create_table_query)
                cursor.execute(create_btree_indexes)
                cursor.execute(create_hnsw_cosine_index)
                cursor.execute(create_hnsw_ip_index)
            logger.info("[DB] Schema and indexes successfully initialized.")
        except Exception as e:
            logger.error(f"[DB] Error setting up database schema: {e}")
            raise

    @classmethod
    def upsert_function_embedding(
        cls, file_path: str, function_name: str, signature: str, cleaned_source: str, embedding: list
    ):
        """
        Inserts a new function's metadata and vector embedding,
        or updates the signature, source, and embedding if the function already exists in that file.
        """
        query = """
        INSERT INTO originality_embeddings (file_path, function_name, signature, cleaned_source, embedding)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (file_path, function_name)
        DO UPDATE SET
            signature = EXCLUDED.signature,
            cleaned_source = EXCLUDED.cleaned_source,
            embedding = EXCLUDED.embedding,
            created_at = CURRENT_TIMESTAMP;
        """
        try:
            with cls.get_cursor() as cursor:
                cursor.execute(query, (file_path, function_name, signature, cleaned_source, embedding))
            logger.info(f"[DB] Saved embedding for {function_name} in {file_path}")
        except Exception as e:
            logger.error(f"[DB] Failed to upsert embedding for {function_name} in {file_path}: {e}")
            raise

    @classmethod
    def query_similar_functions(
        cls, query_embedding: list, limit: int = 5, metric: str = "cosine"
    ) -> list:
        """
        Queries the database for functions closest to the query_embedding.
        
        Args:
            query_embedding: The query vector (dense list of floats).
            limit: Maximum number of records to return.
            metric: Similarity metric to use. Options:
                    'cosine' -> Cosine distance (<=>)
                    'inner_product' -> Negative Inner Product (<#>)
                    'l2' -> L2 / Euclidean distance (<->)
        Returns:
            A list of dictionary records containing match metadata and similarity scores.
        """
        # Determine operator and distance computation
        if metric == "cosine":
            operator = "<=>"
            # Cosine similarity = 1 - cosine distance
            score_expr = "1 - (embedding <=> %s)"
        elif metric == "inner_product":
            operator = "<#>"
            # Inner product (if vectors are normalized, returns similarity score directly)
            # pgvector's <#> operator returns negative inner product, so we negate it
            score_expr = "-(embedding <#> %s)"
        elif metric == "l2":
            operator = "<->"
            score_expr = "embedding <-> %s"
        else:
            raise ValueError("Unsupported metric. Choose 'cosine', 'inner_product', or 'l2'.")

        query = f"""
        SELECT 
            id,
            file_path,
            function_name,
            signature,
            cleaned_source,
            {score_expr} AS similarity_score
        FROM originality_embeddings
        ORDER BY embedding {operator} %s
        LIMIT %s;
        """

        try:
            # Using RealDictCursor to return results as Python dicts
            with cls.get_cursor(cursor_factory=RealDictCursor) as cursor:
                # We pass query_embedding twice: once for score calculation, once for sorting
                cursor.execute(query, (query_embedding, query_embedding, limit))
                results = cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"[DB] Failed to execute similarity query: {e}")
            raise

# --- Self-Test & Usage Harness ---
if __name__ == "__main__":
    # Test setting up schema and performing insert/query with 3D mock vectors
    import random
    
    print("[TEST] Running db_client self-test...")
    
    # We will use 3 dimensions for our mock tests to match db_test.py
    TEST_DIM = 3
    
    try:
        # Initialize schema
        DatabaseManager.setup_schema(vector_dim=TEST_DIM)
        
        # Insert mock functions
        mock_embedding_1 = [0.1, 0.9, 0.0]
        mock_embedding_2 = [0.1, 0.85, 0.1]
        mock_embedding_3 = [0.9, 0.1, 0.1]
        
        print("\n[TEST] Inserting mock functions...")
        DatabaseManager.upsert_function_embedding(
            file_path="agents/originality/parser.py",
            function_name="clean_function_source",
            signature="def clean_function_source(node)",
            cleaned_source="def clean_function_source(node):\n    # mock code\n    pass",
            embedding=mock_embedding_1
        )
        DatabaseManager.upsert_function_embedding(
            file_path="agents/originality/parser.py",
            function_name="extract_functions_from_file",
            signature="def extract_functions_from_file(file_path)",
            cleaned_source="def extract_functions_from_file(file_path):\n    # mock code\n    pass",
            embedding=mock_embedding_2
        )
        DatabaseManager.upsert_function_embedding(
            file_path="agents/originality/detector.py",
            function_name="calculate_cosine_similarity",
            signature="def calculate_cosine_similarity(v1, v2)",
            cleaned_source="def calculate_cosine_similarity(v1, v2):\n    # math\n    pass",
            embedding=mock_embedding_3
        )
        
        # Perform query
        query_vec = [0.1, 0.88, 0.05]
        print(f"\n[TEST] Querying database for vectors similar to: {query_vec}")
        
        matches = DatabaseManager.query_similar_functions(query_vec, limit=2, metric="cosine")
        
        for idx, match in enumerate(matches, 1):
            print(f"\nMatch #{idx}:")
            print(f"  File: {match['file_path']}")
            print(f"  Function: {match['function_name']}")
            print(f"  Similarity Score (Cosine): {match['similarity_score']:.6f}")
            
    except psycopg2.OperationalError as op_err:
        print(f"\n[TEST] Operational Error: {op_err}")
        print("Note: Ensure PostgreSQL docker-compose container is running with 'docker-compose up -d'")
    except Exception as err:
        print(f"\n[TEST] Error encountered during test: {err}")
