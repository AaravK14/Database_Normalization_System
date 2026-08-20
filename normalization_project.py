
import mysql.connector
from mysql.connector import Error
from prettytable import PrettyTable
from collections import defaultdict
import re
import sys

def create_connection(host, user, password, database=None):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            autocommit=False
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def show_table(cur, name, title=None):
    try:
        cur.execute(f"SELECT * FROM {name}")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        t = PrettyTable(cols)
        for r in rows:
            t.add_row(r)
        print(f"\n📋 {title or f'TABLE: {name}'}  (rows: {len(rows)})")
        print(t)
        
        
        cur.execute(f"SHOW CREATE TABLE {name}")
        create_stmt = cur.fetchone()[1]
        if "FOREIGN KEY" in create_stmt or "PRIMARY KEY" in create_stmt:
            print("\n🔑 Constraints:")
            for line in create_stmt.split('\n'):
                if 'PRIMARY KEY' in line or 'FOREIGN KEY' in line or 'KEY' in line:
                    print(f"   {line.strip()}")
    except Exception as e:
        print(f"⚠️ Could not show table '{name}': {e}")

def input_nonempty(prompt):
    while True:
        v = input(prompt).strip()
        if v:
            return v

def safe_name(s):
    s = re.sub(r'[^a-zA-Z0-9_]', '_', s)
    if s[0].isdigit():
        s = 'col_' + s
    return s.lower()

def infer_datatype(values):
    values = [v for v in values if v is not None and str(v).strip()]
    if not values:
        return "VARCHAR(255)"
    
    
    try:
        for v in values:
            int(v)
        max_val = max(int(v) for v in values)
        if max_val < 128:
            return "TINYINT"
        elif max_val < 32768:
            return "SMALLINT"
        elif max_val < 2147483648:
            return "INT"
        else:
            return "BIGINT"
    except:
        pass
    
    
    try:
        for v in values:
            float(v)
        return "DECIMAL(10,2)"
    except:
        pass
    
    
    max_len = max(len(str(v)) for v in values)
    if max_len <= 50:
        return "VARCHAR(50)"
    elif max_len <= 100:
        return "VARCHAR(100)"
    elif max_len <= 255:
        return "VARCHAR(255)"
    else:
        return "TEXT"

def analyze_functional_dependencies(rows, col_names):
    fds = []
    n = len(col_names)
    
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            
            lhs = col_names[i]
            rhs = col_names[j]
            
            
            mapping = defaultdict(set)
            for row in rows:
                if row[i] is not None:
                    mapping[row[i]].add(row[j])
            
            if all(len(vals) == 1 for vals in mapping.values() if vals != {None}):
                fds.append((lhs, rhs))
    
    return fds

def find_candidate_key(rows, col_names):
    if not rows:
        return [col_names[0]]
    
    
    for col in col_names:
        idx = col_names.index(col)
        values = [row[idx] for row in rows if row[idx] is not None]
        if len(set(values)) == len(values) and len(values) == len(rows):
            return [col]
    
    
    for i in range(len(col_names)):
        for j in range(i + 1, len(col_names)):
            pairs = [(row[i], row[j]) for row in rows]
            pairs_filtered = [p for p in pairs if None not in p]
            if len(set(pairs_filtered)) == len(pairs_filtered) and len(pairs_filtered) == len(rows):
                return [col_names[i], col_names[j]]
    
    
    return [col_names[0]]

def create_table_with_fk(cur, table_name, columns, primary_key, foreign_keys=None):
    cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    col_defs = []
    for col_name, col_type in columns.items():
        col_def = f"{col_name} {col_type}"
        if col_name in primary_key:
            col_def += " NOT NULL"
        col_defs.append(col_def)
    
    
    if len(primary_key) == 1:
        pk_def = f"PRIMARY KEY ({primary_key[0]})"
    else:
        pk_def = f"PRIMARY KEY ({', '.join(primary_key)})"
    col_defs.append(pk_def)
    
    
    if foreign_keys:
        for fk_col, (ref_table, ref_col) in foreign_keys.items():
            fk_def = f"FOREIGN KEY ({fk_col}) REFERENCES {ref_table}({ref_col}) ON DELETE CASCADE ON UPDATE CASCADE"
            col_defs.append(fk_def)
            
            col_defs.append(f"INDEX idx_{fk_col} ({fk_col})")
    
    create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)}) ENGINE=InnoDB"
    cur.execute(create_sql)

def main():
    print("="*70)
    print("  ENHANCED MySQL DATABASE NORMALIZER (1NF → 2NF → 3NF)")
    print("  With Foreign Keys, Primary Keys & Referential Integrity")
    print("="*70)
    
    
    print("\n🔌 MySQL Connection Setup")
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    user = input("MySQL User (default: root): ").strip() or "root"
    password = input("MySQL Password: ").strip()
    
    conn = create_connection(host, user, password)
    if not conn:
        print("❌ Failed to connect to MySQL. Exiting.")
        return
    
    cur = conn.cursor()
    
    
    db_name = safe_name(input_nonempty("Database name: "))
    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cur.execute(f"USE {db_name}")
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        conn.commit()
        print(f"✅ Using database: {db_name}\n")
    except Error as e:
        print(f"❌ Error creating/using database: {e}")
        return
    
    
    table_name = safe_name(input_nonempty("Enter name for your unnormalized table: "))
    
    
    print("\n📝 Define columns (e.g., student_id, student_name, courses, instructor, instructor_phone)")
    cols = []
    while True:
        c = input("Column name (Enter to finish): ").strip()
        if not c:
            break
        cols.append(safe_name(c))
    
    if len(cols) < 2:
        print("Need at least 2 columns. Exiting.")
        return
    
    
    col_defs = ", ".join(f"{c} TEXT" for c in cols)
    cur.execute(f"DROP TABLE IF EXISTS {table_name}_temp")
    cur.execute(f"CREATE TABLE {table_name}_temp ({col_defs})")
    conn.commit()
    print(f"✅ Table '{table_name}_temp' created\n")
    
    
    print("📥 Enter data. For multi-valued attributes, use commas (e.g., 'DBMS,OS,Networks')")
    rows_data = []
    while True:
        vals = []
        print(f"\n--- Row {len(rows_data) + 1} ---")
        for c in cols:
            v = input(f"{c}: ").strip()
            vals.append(v if v else None)
        
        rows_data.append(vals)
        placeholders = ", ".join(["%s"] * len(vals))
        cur.execute(f"INSERT INTO {table_name}_temp VALUES ({placeholders})", vals)
        conn.commit()
        
        if input("Add another row? (y/N): ").strip().lower() != "y":
            break
    
    
    print("\n🔍 Inferring optimal data types...")
    col_types = {}
    for i, col in enumerate(cols):
        values = [row[i] for row in rows_data]
        col_types[col] = infer_datatype(values)
        print(f"   {col}: {col_types[col]}")
    
    
    cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    typed_col_defs = ", ".join(f"{c} {col_types[c]}" for c in cols)
    cur.execute(f"CREATE TABLE {table_name} ({typed_col_defs})")
    
    for vals in rows_data:
        placeholders = ", ".join(["%s"] * len(vals))
        cur.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", vals)
    conn.commit()
    
    
    print("\n" + "="*70)
    print("  UNNORMALIZED TABLE (0NF)")
    print("="*70)
    show_table(cur, table_name, "Original Unnormalized Table")
    print("\n⚠️ Issues: May contain multi-valued attributes, repeating groups, no keys")
    
    
    print("\n" + "="*70)
    print("  STEP 1: FIRST NORMAL FORM (1NF)")
    print("="*70)
    print("📖 1NF Rules:")
    print("   - Each cell contains atomic (single) values")
    print("   - No repeating groups")
    print("   - Each row is unique")
    print("   - Primary key defined")
    
    nf1_table = f"{table_name}_1nf"
    cur.execute(f"DROP TABLE IF EXISTS {nf1_table}")
    
    
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    
    expanded_rows = []
    for row in rows:
        split_cols = []
        for cell in row:
            if cell and "," in str(cell):
                pieces = [p.strip() for p in str(cell).split(",")]
                split_cols.append(pieces)
            else:
                split_cols.append([cell])
        
        combos = [[]]
        for col_vals in split_cols:
            new_combos = []
            for combo in combos:
                for val in col_vals:
                    new_combos.append(combo + [val])
            combos = new_combos
        
        expanded_rows.extend(combos)
    
    
    typed_col_defs = ", ".join(f"{c} {col_types[c]}" for c in cols)
    cur.execute(f"CREATE TABLE {nf1_table} ({typed_col_defs})")
    
    for combo in expanded_rows:
        placeholders = ", ".join(["%s"] * len(combo))
        cur.execute(f"INSERT INTO {nf1_table} VALUES ({placeholders})", combo)
    
    conn.commit()
    show_table(cur, nf1_table, "1NF: Atomic Values")
    print("✅ 1NF achieved: All attributes are atomic")
    
    
    print("\n" + "="*70)
    print("  ANALYZING FUNCTIONAL DEPENDENCIES")
    print("="*70)
    
    cur.execute(f"SELECT * FROM {nf1_table}")
    rows_1nf = cur.fetchall()
    
    fds = analyze_functional_dependencies(rows_1nf, cols)
    
    print("\n🔍 Detected Functional Dependencies:")
    if fds:
        for lhs, rhs in fds:
            print(f"   {lhs} → {rhs}")
    else:
        print("   (None detected)")
    
    candidate_key = find_candidate_key(rows_1nf, cols)
    print(f"\n🔑 Candidate Key: {', '.join(candidate_key)}")
    
    
    cur.execute(f"DROP TABLE IF EXISTS {nf1_table}")
    create_table_with_fk(cur, nf1_table, col_types, candidate_key)
    
    for combo in expanded_rows:
        placeholders = ", ".join(["%s"] * len(combo))
        try:
            cur.execute(f"INSERT INTO {nf1_table} VALUES ({placeholders})", combo)
        except Error:
            pass  
    
    conn.commit()
    show_table(cur, nf1_table, "1NF with Primary Key")
    
    
    print("\n" + "="*70)
    print("  STEP 2: SECOND NORMAL FORM (2NF)")
    print("="*70)
    print("📖 2NF Rules:")
    print("   - Must be in 1NF")
    print("   - No partial dependencies (non-key attributes fully depend on entire key)")
    
    created_tables = {}  
    
    if len(candidate_key) == 1:
        print(f"\n✅ Already in 2NF: Single-column key ({candidate_key[0]})")
        print("   No partial dependencies possible with single-attribute key")
        nf2_main = nf1_table
        created_tables[nf2_main] = (cols, candidate_key, {})
    else:
        print(f"\n⚙️ Composite key detected: {', '.join(candidate_key)}")
        print("   Checking for partial dependencies...")
        
        
        non_key_attrs = [c for c in cols if c not in candidate_key]
        partial_deps = defaultdict(list)
        
        for attr in non_key_attrs:
            for key_part in candidate_key:
                idx_key = cols.index(key_part)
                idx_attr = cols.index(attr)
                
                mapping = defaultdict(set)
                for row in rows_1nf:
                    if row[idx_key] is not None:
                        mapping[row[idx_key]].add(row[idx_attr])
                
                if all(len(vals) == 1 for vals in mapping.values()):
                    partial_deps[key_part].append(attr)
                    break
        
        if partial_deps:
            print("\n⚠️ Partial dependencies found:")
            for key_part, attrs in partial_deps.items():
                print(f"   {key_part} → {', '.join(attrs)}")
            
            
            for key_part, attrs in partial_deps.items():
                table_2nf = f"{key_part}_details"
                cols_2nf = [key_part] + attrs
                
                
                table_col_types = {c: col_types[c] for c in cols_2nf}
                
                create_table_with_fk(cur, table_2nf, table_col_types, [key_part])
                
                
                seen = set()
                for row in rows_1nf:
                    key_idx = cols.index(key_part)
                    key_val = row[key_idx]
                    
                    if key_val and key_val not in seen:
                        vals = [row[cols.index(c)] for c in cols_2nf]
                        placeholders = ", ".join(["%s"] * len(vals))
                        try:
                            cur.execute(f"INSERT INTO {table_2nf} VALUES ({placeholders})", vals)
                            seen.add(key_val)
                        except Error:
                            pass
                
                conn.commit()
                show_table(cur, table_2nf, f"2NF: {key_part} and its attributes")
                created_tables[table_2nf] = (cols_2nf, [key_part], {})
            
            
            removed_attrs = [a for attrs in partial_deps.values() for a in attrs]
            remaining = [c for c in cols if c not in removed_attrs]
            
            nf2_main = f"{table_name}_2nf_main"
            main_col_types = {c: col_types[c] for c in remaining}
            
            
            fks = {}
            for key_part in partial_deps.keys():
                if key_part in remaining:
                    fks[key_part] = (f"{key_part}_details", key_part)
            
            create_table_with_fk(cur, nf2_main, main_col_types, candidate_key, fks)
            
            seen_rows = set()
            for row in rows_1nf:
                vals = tuple(row[cols.index(c)] for c in remaining)
                if vals not in seen_rows:
                    placeholders = ", ".join(["%s"] * len(vals))
                    try:
                        cur.execute(f"INSERT INTO {nf2_main} VALUES ({placeholders})", vals)
                        seen_rows.add(vals)
                    except Error:
                        pass
            
            conn.commit()
            show_table(cur, nf2_main, "2NF: Main table with Foreign Keys")
            created_tables[nf2_main] = (remaining, candidate_key, fks)
            print("✅ 2NF achieved: Partial dependencies removed with FK relationships")
        else:
            print("✅ No partial dependencies found - already in 2NF")
            nf2_main = nf1_table
            created_tables[nf2_main] = (cols, candidate_key, {})
    
    
    print("\n" + "="*70)
    print("  STEP 3: THIRD NORMAL FORM (3NF)")
    print("="*70)
    print("📖 3NF Rules:")
    print("   - Must be in 2NF")
    print("   - No transitive dependencies (non-key → non-key)")
    
    
    cur.execute(f"SELECT * FROM {nf2_main}")
    rows_2nf = cur.fetchall()
    cur.execute(f"DESCRIBE {nf2_main}")
    cols_2nf = [row[0] for row in cur.fetchall()]
    
    
    print("\n⚙️ Checking for transitive dependencies...")
    
    transitive_deps = []
    for i, col_a in enumerate(cols_2nf):
        if col_a in candidate_key:
            continue
        for j, col_b in enumerate(cols_2nf):
            if i >= j or col_b in candidate_key:
                continue
            
            
            mapping = defaultdict(set)
            for row in rows_2nf:
                if row[i] is not None:
                    mapping[row[i]].add(row[j])
            
            if all(len(vals) == 1 for vals in mapping.values() if vals != {None}):
                transitive_deps.append((col_a, col_b))
    
    if transitive_deps:
        print("⚠️ Transitive dependencies found:")
        for lhs, rhs in transitive_deps:
            print(f"   {lhs} → {rhs}")
        
        
        processed = set()
        for lhs, rhs in transitive_deps:
            if lhs in processed:
                continue
            
            
            dependent_attrs = [rhs for l, r in transitive_deps if l == lhs]
            
            table_3nf = f"{lhs}_lookup"
            cols_3nf = [lhs] + dependent_attrs
            
            table_col_types = {c: col_types[c] for c in cols_3nf}
            create_table_with_fk(cur, table_3nf, table_col_types, [lhs])
            
            
            seen = set()
            for row in rows_2nf:
                lhs_idx = cols_2nf.index(lhs)
                lhs_val = row[lhs_idx]
                
                if lhs_val and lhs_val not in seen:
                    vals = [row[cols_2nf.index(c)] for c in cols_3nf]
                    placeholders = ", ".join(["%s"] * len(vals))
                    try:
                        cur.execute(f"INSERT INTO {table_3nf} VALUES ({placeholders})", vals)
                        seen.add(lhs_val)
                    except Error:
                        pass
            
            conn.commit()
            show_table(cur, table_3nf, f"3NF: {lhs} lookup table")
            created_tables[table_3nf] = (cols_3nf, [lhs], {})
            processed.add(lhs)
        
        
        removed_attrs = [rhs for _, rhs in transitive_deps]
        final_cols = [c for c in cols_2nf if c not in removed_attrs]
        
        nf3_main = f"{table_name}_3nf"
        final_col_types = {c: col_types[c] for c in final_cols}
        
        
        fks_3nf = {}
        for lhs in processed:
            if lhs in final_cols:
                fks_3nf[lhs] = (f"{lhs}_lookup", lhs)
        
        
        if nf2_main in created_tables:
            _, _, fks_2nf = created_tables[nf2_main]
            for fk_col, fk_ref in fks_2nf.items():
                if fk_col in final_cols:
                    fks_3nf[fk_col] = fk_ref
        
        create_table_with_fk(cur, nf3_main, final_col_types, candidate_key, fks_3nf)
        
        seen_rows = set()
        for row in rows_2nf:
            vals = tuple(row[cols_2nf.index(c)] for c in final_cols)
            if vals not in seen_rows:
                placeholders = ", ".join(["%s"] * len(vals))
                try:
                    cur.execute(f"INSERT INTO {nf3_main} VALUES ({placeholders})", vals)
                    seen_rows.add(vals)
                except Error:
                    pass
        
        conn.commit()
        show_table(cur, nf3_main, "3NF: Final main table with all Foreign Keys")
        print("✅ 3NF achieved: Transitive dependencies removed with FK relationships")
    else:
        print("✅ No transitive dependencies found - already in 3NF")
    
    
    print("\n" + "="*70)
    print("  NORMALIZATION COMPLETE!")
    print("="*70)
    
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    cur.execute("SHOW TABLES")
    tables = [row[0] for row in cur.fetchall()]
    print(f"\n📊 Created {len(tables)} tables:")
    for t in tables:
        if not t.endswith('_temp'):
            print(f"   - {t}")
    
    print("\n🔗 Relationship Summary:")
    for t in tables:
        if t.endswith('_temp'):
            continue
        cur.execute(f"SHOW CREATE TABLE {t}")
        create_stmt = cur.fetchone()[1]
        if "FOREIGN KEY" in create_stmt:
            print(f"\n   {t}:")
            for line in create_stmt.split('\n'):
                if 'FOREIGN KEY' in line:
                    print(f"     {line.strip()}")
    
    print(f"\n💾 All tables saved in MySQL database: {db_name}")
    print("✅ Referential integrity enforced with CASCADE operations")
    
    
    try:
        cur.execute(f"DROP TABLE IF EXISTS {table_name}_temp")
        conn.commit()
    except:
        pass
    
    
    print("\n" + "="*70)
    print("Interactive SQL Console (type 'exit' to quit, 'tables' to list)")
    print("="*70)
    
    while True:
        try:
            q = input("\nSQL> ").strip()
            if not q:
                continue
            if q.lower() == "exit":
                break
            if q.lower() == "tables":
                cur.execute("SHOW TABLES")
                for row in cur.fetchall():
                    print(f"   - {row[0]}")
                continue
            
            cur.execute(q)
            if cur.description:
                rows = cur.fetchall()
                pt = PrettyTable([d[0] for d in cur.description])
                for r in rows:
                    pt.add_row(r)
                print(pt)
                print(f"\n({len(rows)} rows)")
            else:
                conn.commit()
                print(f"✅ Query executed (affected rows: {cur.rowcount})")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    conn.close()
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()