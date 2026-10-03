# AIDA 1145 Week 4 — Practice Lab 1: Supplier Inventory Intake

- **Type:** Ungraded, fully worked practice example
- **Week topic:** Ingestion and extraction patterns
- **Tools:** VS Code and Python; MariaDB is optional
- **D2L submission:** None for this practice lab

## What you will do

A warehouse receives a supplier inventory spreadsheet as a CSV file. You will run a completed Python program that checks the rows, separates valid records from records that need correction, and writes clear result files.

By the end, you will have practised how to:

- open a CSV file with pandas;
- make inconsistent column headings easier to work with;
- check required information and convert values into the right data types;
- find invalid and duplicate records; and
- save clean records, rejected records, duplicates, and a short count summary.

The supplied data are fictional. You do not need a database to complete the main practice steps.

## Step 1 — Accept access and prepare a work folder

1. Sign in to GitHub using the account you use for AIDA 1145.
2. Accept the invitation to `AIDA_1145_Practical_Lab_Examples` if GitHub shows one.
3. On your computer, create a folder named `AIDA-work`.
4. Open VS Code.
5. In VS Code, select **File → Open Folder** and choose the `AIDA-work` folder.
6. Select **Terminal → New Terminal**. A command area opens at the bottom of VS Code.

## Step 2 — Download the two repositories you need

First, download the course practice materials. In the VS Code terminal, type `git clone ` (including the space), then paste this address and press **Enter**:

```bash
git clone https://github.com/stem-ai-studio-classroom/AIDA_1145_Practical_Lab_Examples.git
```

If the terminal says that this folder already exists, the course repository has already been downloaded. Open the existing `AIDA_1145_Practical_Lab_Examples` folder in VS Code and continue; do not clone it again.

Next, download your own private AIDA 1145 repository:

1. In your browser, open your assigned private AIDA 1145 repository on GitHub.
2. Select the green **Code** button, choose **HTTPS**, and copy the repository address.
3. In the VS Code terminal, type `git clone `, paste the address you copied, and press **Enter**. Use your actual repository address; do not type a placeholder.

If you have already downloaded your private student repository to this computer, do not clone it a second time. Open that existing folder instead.

## Step 3 — Copy Practice Lab 1 into your private repository

1. In the VS Code Explorer (the file list on the left), open `AIDA_1145_Practical_Lab_Examples`.
2. Open its `week-04` folder.
3. Right-click the folder named `practice-supplier-inventory-intake` and select **Copy**.
4. In the Explorer, open your own private AIDA 1145 repository.
5. If it does not already have a folder named `week-04`, create one inside your private repository.
6. Right-click the private repository's `week-04` folder and select **Paste**.
7. In VS Code, select **File → Open Folder** and open the copied `practice-supplier-inventory-intake` folder from inside your private repository.
8. Check the folder path shown in VS Code. It must be under your private student repository, not under `AIDA_1145_Practical_Lab_Examples`.
9. Select **Terminal → New Terminal** again. The terminal should now open in the copied practice folder.

You will run and inspect the copy in your own private repository. The instructor's course-material repository is read-only for students: do not edit or push to it.

## Step 4 — Check Python

In the VS Code terminal, use the command for your computer.

**Windows:**

```powershell
py --version
```

**macOS:**

```bash
python3 --version
```

You need Python 3.10 or later. If the command is not recognized, ask your instructor for help before continuing.

## Step 5 — Create and activate this lab's Python environment

This environment keeps the packages for this practice separate from other Python work.

Create the environment.

**Windows:**

```powershell
py -m venv .venv
```

**macOS:**

```bash
python3 -m venv .venv
```

Activate it.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS:**

```bash
source .venv/bin/activate
```

After activation, the terminal prompt usually begins with `(.venv)`. If PowerShell blocks activation, enter this command in the same terminal and then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This setting applies only to the current PowerShell window.

## Step 6 — Install the packages listed for this lab

`requirements.txt` is a text file listing the Python packages needed for the required practice. The following commands ask Python to install those packages.

**Windows:**

```powershell
py -m pip install -r requirements.txt
```

**macOS:**

```bash
python3 -m pip install -r requirements.txt
```

Wait until the install finishes before moving on. Do not type `requirements.txt` by itself; it is not a program.

## Step 7 — Look at the supplied files

In VS Code's Explorer, check that you can see:

- `data/supplier_inventory.csv` — the fictional supplier file used as input;
- `analysis.py` — the completed example program;
- `outputs/` — the result files produced by the program;
- `decision_note.md` — a completed example explaining the results;
- `requirements.txt` — pandas, needed for the required Python practice;
- `optional-requirements.txt` — packages used only by the optional database extension; and
- `load_to_mariadb.py` and `sql/` — an optional database extension.

Open `data/supplier_inventory.csv`. Each line is one supplier inventory record. Some records contain problems on purpose so you can see how the checks work.

## Step 8 — Run the completed example

Make sure your terminal is open in the copied practice folder and the environment is active. Run:

**Windows:**

```powershell
py analysis.py
```

**macOS:**

```bash
python3 analysis.py
```

The terminal should report:

| Count | Expected result |
|---|---:|
| Incoming records | 9 |
| Clean records | 4 |
| Rejected records | 5 |
| Duplicate records | 1 |

The program creates four files in the `outputs` folder:

- `clean_inventory.csv` — records that passed the checks;
- `rejected_inventory.csv` — records needing correction, with a reason;
- `duplicate_inventory.csv` — repeated supplier/product/date records; and
- `ingestion_summary.csv` — the record counts shown above.

Open each output file in VS Code and compare it with the original input file. Then read `decision_note.md` to see an example explanation of what the results mean.

## Step 9 — Follow the main code logic

Open `analysis.py`. You do not need to write the program for this practice; follow how it handles the records:

1. `pd.read_csv(...)` reads the supplier CSV file into a pandas table.
2. `standardize_columns(...)` removes extra spaces, uses lowercase letters, and changes spaces in headings to underscores.
3. `add_rejection_reasons(...)` checks important fields and converts quantity, cost, and date into suitable types. It writes a reason beside records that fail a check.
4. The duplicate check finds repeated supplier, product, and received-date combinations among otherwise valid records.
5. The program separates the rows into clean, rejected, and duplicate groups.
6. `to_csv(...)` writes those groups and the count summary into `outputs` so you can inspect them.

The program does not silently discard a bad row: it keeps the row in the rejected output and records why it needs attention.

## Optional Step 10 — Load the clean data into MariaDB

**You may skip this entire section.** MariaDB is not needed to complete Practice Lab 1. Do not install a database just for this optional extension. Only try it if you already have a local MariaDB service and know how to connect to it.

1. In your local MariaDB client, run `sql/create_database.sql` to create and select the practice database.
2. Install the additional Python packages for this optional extension.

   **Windows:**

   ```powershell
   py -m pip install -r optional-requirements.txt
   ```

   **macOS:**

   ```bash
   python3 -m pip install -r optional-requirements.txt
   ```

3. Set the connection address in your terminal. Replace the example username and password with credentials for your own local database only. Do not put a password in a file, commit it to Git, or share it in a screenshot.

   **Windows PowerShell:**

   ```powershell
   $env:MARIADB_URL = "mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@localhost:3306/aida1145"
   ```

   **macOS:**

   ```bash
   export MARIADB_URL="mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@localhost:3306/aida1145"
   ```

4. Run the optional loader.

   **Windows:**

   ```powershell
   py load_to_mariadb.py
   ```

   **macOS:**

   ```bash
   python3 load_to_mariadb.py
   ```

5. In your MariaDB client, run the queries in `sql/verify_inventory.sql` and inspect the results.

If you do not already have a local database or are unsure about the connection, stop here and ask your instructor. The Python practice in Steps 1–9 is complete without this extension.

## Optional Step 11 — Save your practice copy to your private repository

Practice is ungraded and does not require a D2L submission. If you made meaningful changes or want to save your work in GitHub, use the terminal in your copied lab folder:

```bash
git status
git add .
git commit -m "Complete AIDA 1145 Practice Lab 1"
git push
```

These commands must run in your own private student repository. If Git says there is nothing to commit, no new files or changes need saving. Never push to the instructor's Practical Lab Examples repository.

## If something does not work

- **`py` is not recognized:** On macOS, use the `python3` command shown above. On Windows, ask your instructor to help check Python installation.
- **`ModuleNotFoundError`:** Activate `.venv` and repeat Step 6.
- **`FileNotFoundError`:** In VS Code, confirm you opened the copied practice folder and that `supplier_inventory.csv` is inside `data`.
- **MariaDB connection error:** Skip the optional database extension. The required Python practice does not need MariaDB.

When asking for help, share the command you ran and the full error message. Never share a password, token, or database connection URL containing a password.
