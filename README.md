# Database Normalization System

A Python and MySQL based DBMS project that automates the normalization of relational data from **0NF to 1NF, 2NF, and 3NF** while maintaining data integrity through Primary Keys, Foreign Keys, and referential integrity constraints.

## 📌 Overview

The Database Normalization System takes user-defined relational data and automatically analyzes and transforms it into normalized database structures.

The system identifies functional dependencies, determines candidate keys, detects partial and transitive dependencies, and creates normalized MySQL tables with appropriate Primary Key and Foreign Key relationships.

## 🎯 Objectives

* Automate the database normalization process.
* Identify functional dependencies and candidate keys.
* Convert unnormalized data into 1NF, 2NF, and 3NF.
* Reduce data redundancy and eliminate dependency-related anomalies.
* Maintain referential integrity using Primary and Foreign Keys.
* Provide an interactive SQL console for database inspection and queries.

## ✨ Features

* 0NF → 1NF → 2NF → 3NF normalization
* Automatic candidate key detection
* Functional dependency analysis
* Detection of partial dependencies
* Detection of transitive dependencies
* Automatic decomposition of relations
* Primary and Foreign Key generation
* Referential integrity with CASCADE operations
* Automatic SQL data-type inference
* Multi-valued attribute handling
* Interactive SQL console
* MySQL database integration

## 🔄 Normalization Process

### 0NF

The user enters an unnormalized relation containing attributes that may include multi-valued or repeating data.

### 1NF

The system:

* Converts multi-valued attributes into atomic values.
* Removes repeating groups.
* Generates a candidate key.
* Creates the corresponding MySQL table.

### 2NF

The system:

* Checks for partial dependencies.
* Identifies attributes dependent on individual components of a composite key.
* Decomposes the relation where required.
* Establishes Foreign Key relationships.

### 3NF

The system:

* Checks for transitive dependencies.
* Separates dependent attributes into lookup tables.
* Creates Foreign Key relationships between the decomposed tables.

## 🗄️ Database Design

The generated database uses:

* Primary Keys for entity identification
* Foreign Keys for relationships
* Indexes for Foreign Key columns
* InnoDB tables for relational integrity
* CASCADE operations for maintaining relationships

## 🛠️ Technologies Used

| Technology             | Purpose                                    |
| ---------------------- | ------------------------------------------ |
| Python                 | Core application and normalization logic   |
| MySQL                  | Relational database management             |
| SQL                    | Database creation, queries and constraints |
| mysql-connector-python | Python-MySQL connectivity                  |
| PrettyTable            | Tabular terminal output                    |

## 📂 Project Structure

```text
Database_Normalization_System/
│
├── normalization_project.py
├── requirements.txt
├── schema.sql
├── README.md
├── .gitignore
├── .env.example
│
├── docs/
│   └── er_diagram.png
│
└── screenshots/
    ├── input.png
    ├── 1nf.png
    ├── 2nf.png
    ├── 3nf.png
    └── sql_console.png
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Database_Normalization_System
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install and configure MySQL

Make sure MySQL Server is installed and running.

The program will ask for:

* MySQL Host
* MySQL Username
* MySQL Password
* Database Name

### 4. Run the application

```bash
python normalization_project.py
```

## 💻 Usage

1. Enter your MySQL connection details.
2. Enter the database name.
3. Define the columns of the unnormalized relation.
4. Enter the data.
5. The system analyzes the relation.
6. Functional dependencies and candidate keys are identified.
7. The relation is transformed through 1NF, 2NF and 3NF.
8. Generated tables and relationships are displayed.
9. Use the interactive SQL console to inspect the resulting database.

## 📸 Screenshots

### Input and Database Setup

![Input](screenshots/input.png)

### 1NF

![1NF](screenshots/1nf.png)

### 2NF

![2NF](screenshots/2nf.png)

### 3NF

![3NF](screenshots/3nf.png)

### SQL Console

![SQL Console](screenshots/sql_console.png)

## 📊 Example Normalization Flow

```text
Unnormalized Relation (0NF)
          ↓
      Atomic Values
          ↓
         1NF
          ↓
  Remove Partial Dependencies
          ↓
         2NF
          ↓
 Remove Transitive Dependencies
          ↓
         3NF
```

## 🚀 Future Scope

* Support for BCNF and higher normal forms.
* Graphical interface for database visualization.
* Automatic ER diagram generation.
* Support for CSV and Excel input files.
* Improved functional dependency inference.
* Export of generated schemas and SQL scripts.

## 👨‍💻 Project

**Database Normalization System**

Developed as a DBMS course project using Python, MySQL and SQL.
