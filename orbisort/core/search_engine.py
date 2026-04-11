import sqlite3
from database.db_manager import DB_PATH
from difflib import get_close_matches


import os

def search_files(query, limit=10):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = query.lower()

    # 🔹 FAST INDEX SEARCH
    cursor.execute(
        """
        SELECT original_path, new_path
        FROM files
        WHERE LOWER(new_path) LIKE ? OR LOWER(original_path) LIKE ?
        LIMIT ?
    """,
        (f"%{query}%", f"%{query}%", limit),
    )

    raw_results = cursor.fetchall()
    results = [(os.path.basename(path), path) for (orig, path) in raw_results if path]


    # 🔹 FUZZY MATCH (if low results)
    if len(results) < 3:

        cursor.execute("SELECT original_path, new_path FROM files")
        all_files = cursor.fetchall()
        all_with_names = [(os.path.basename(path), path) for (orig, path) in all_files if path]

        names = [f[0].lower() for f in all_with_names]

        matches = get_close_matches(query, names, n=limit, cutoff=0.5)

        fuzzy_results = [
            (name, path) for (name, path) in all_with_names if name.lower() in matches
        ]

        # avoid duplicates
        existing = {r[1] for r in results}
        for item in fuzzy_results:
            if item[1] not in existing:
                results.append(item)
                existing.add(item[1])

    conn.close()

    return results

def semantic_search_files(query, limit=5):
    from database.vector_store import vector_store
    import os
    paths = vector_store.semantic_search(query, n_results=limit)
    results = []
    
    if not paths:
        return results
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for path in paths:
        cursor.execute("SELECT original_path FROM files WHERE new_path = ?", (path,))
        row = cursor.fetchone()
        name = os.path.basename(path)
        results.append((name, path))
    conn.close()
    
    return results

