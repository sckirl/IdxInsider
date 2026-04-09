# Business Logic & Extraction Requirements

## 1. Transaction Date ('Tanggal Transaksi') Extraction Logic

To ensure high accuracy in extracting the actual date of transaction (vs. filing date), the scraper must prioritize the following labels found in IDX PDF disclosures (POJK 11/2017 & POJK 4/2024).

### Label Priority (Case-Insensitive)
1.  **"Tanggal Transaksi"**
2.  **"Waktu Pelaksanaan"**
3.  **"Tanggal Perolehan"** (for BUY) or **"Tanggal Penjualan"** (for SELL)
4.  **"Tanggal Perubahan"**
5.  **"Tanggal Pelaksanaan"**

### Extraction Strategy
- **Step A: Targeted Regex.** Search for the above labels followed by a colon or space and a date pattern.
- **Step B: Table Parsing.** Many disclosures list transactions in a table. If multiple dates exist in a table, extract each row as a separate transaction.
- **Step C: Date Normalization.** Indonesian dates often use month names. Map the following:
    - *Januari, Februari, Maret, April, Mei, Juni, Juli, Agustus, September, Oktober, November, Desember*
- **Step D: Fallback.** If no transaction date is found within the document body, use the **PublishedDate** from the IDX API but mark the record with a `date_inferred: true` flag.

---

## 2. 'Cluster Buy' Scoring System

The 'Cluster Buy' signal is one of the strongest indicators of insider conviction.

### Rule Definition
A **Cluster Buy** occurs when multiple unique insiders purchase shares of the same ticker within a close timeframe.

- **Window:** Rolling 7-day window (Transaction Date $T \pm 7$ days).
- **Condition:** Only transactions categorized as **BUY** or **EXERCISE** are eligible.
- **Scoring Logic:**
    - **2 Unique Insiders:** Add **+3 points** to the `score` of every transaction in that cluster.
    - **3+ Unique Insiders:** Add **+5 points** to the `score` of every transaction in that cluster.

### Implementation Note for DEV
Since Cluster Buy depends on other records, the score should be:
1.  Calculated upon initial ingestion.
2.  Recalculated for the "neighborhood" (same ticker, $\pm 7$ days) whenever a new transaction is added to the database.

---

## 3. Transaction Type Mapping & Scoring Impact

Map raw Indonesian terms to normalized types. Only "Market" actions should impact the conviction score.

| Raw Indonesian Term | Normalized Type | Score Impact | Include in Cluster? |
| :--- | :--- | :--- | :--- |
| `Beli`, `Pembelian`, `Penambahan`, `Buy` | **BUY** | Positive (Base + Role + Value) | Yes |
| `Jual`, `Penjualan`, `Pelepasan`, `Pengurangan`, `Sell` | **SELL** | Negative | No |
| `Pelaksanaan MESOP`, `Pelaksanaan ESOP`, `Exercise`, `Konversi` | **EXERCISE** | Neutral/Positive (+1 Base) | Yes |
| `Hibah`, `Pemberian`, `Gift` | **GIFT** | 0 (Neutral) | No |
| `Waris`, `Warisan`, `Turun Waris`, `Inheritance` | **INHERITANCE** | 0 (Neutral) | No |
| `Saham Bonus`, `Bonus` | **BONUS** | 0 (Neutral) | No |
| `Dividen Saham` | **DIVIDEND** | 0 (Neutral) | No |
| `Pemisahan Saham`, `Stock Split` | **SPLIT** | 0 (Neutral) | No |
| `Penggabungan Saham`, `Reverse Split` | **REVERSE_SPLIT** | 0 (Neutral) | No |
| `Repo`, `Repurchase Agreement` | **REPO** | 0 (Neutral) | No |

### Scoring Formula Refinement
`Final Score = Base_Role_Weight + Transaction_Value_Weight + Cluster_Bonus + Other_Modifiers`

- **Base_Role_Weight:** (e.g., Direktur Utama = 5)
- **Transaction_Value_Weight:** (e.g., > 1B IDR = 3)
- **Cluster_Bonus:** (+3 or +5 as defined above)
- **Non-Market Actions:** If Type is GIFT, INHERITANCE, or BONUS, the `Final Score` is always **0**.

---

## 4. Status Kepemilikan (Ownership Status)
- **"Langsung"** -> `direct_ownership: true` (Bonus: +1)
- **"Tidak Langsung"** -> `direct_ownership: false` (Bonus: 0)
