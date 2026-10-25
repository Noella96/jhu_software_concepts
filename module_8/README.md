# Module 8 — Data Preparation & Statistics Assignment

**Course:** Johns Hopkins University — Principles of Software Development / Software Concepts (EN.605.601)  
**Author:** Noella Formin (`Noella96` / `Achaformin@gmail.com`)  
**AWS Account ID:** `594366804861`  
**S3 Bucket:** `grad-cafe-nf-594366804861`  
**Execution Environment:** Amazon SageMaker Notebook Instance (`ml.t3.medium`) / Python 3.12 Kernel  

---

## Deliverables Checklist & Directory Structure

All required assignment deliverables are placed directly within `module_8/`:

| Filename | Type | Description |
| :--- | :--- | :--- |
| `module_8.ipynb` | Jupyter Notebook | End-to-end reproducible workflow with embedded execution outputs, markdown headers, and S3 upload. |
| `analytics.pdf` | Written Report | Publication-grade analytical summary addressing all 7 statistical and data quality questions. |
| `cleaned_gradcafe.json` | Dataset (JSON) | Standardized, validated, and feature-engineered Grad Café dataset (30,500 records). |
| `missingness_summary.csv` | CSV Table | Column-by-column missing value counts and percentages for the raw dataset. |
| `summary_statistics.csv` | CSV Table | Descriptive statistics (count, mean, median, std, min, max, 25%, 50%, 75%) for numeric features. |
| `initial_dataframe.png` | Screenshot | High-resolution capture of the first 5 rows of the raw Grad Café dataset. |
| `missingness_summary.png` | Screenshot | Missingness summary table showing counts and percentages across all 12 columns. |
| `low_program_count.png` | Screenshot | Output series showing programs occurring fewer than 3 times (`Information: 1`). |
| `date_based.png` | Screenshot | DataFrame table after date parsing, showing decomposed `outcome` and `decision_date`. |
| `float_columns.png` | Screenshot | DataFrame table after float conversion and derived indicator feature engineering. |
| `outlier_summary.png` | Screenshot | Summary table detailing Z-score outlier detection ($|z| > 3$) and analytical handling rationale. |
| `GRE-vs-GRE-V.png` | Matplotlib Chart | Scatter plot of GRE Quantitative vs. Verbal scores with NumPy best-fit line and legend. |
| `GPA-vs-GRE.png` | Matplotlib Chart | Scatter plot of undergraduate GPA vs. GRE Quantitative score with NumPy best-fit line and legend. |
| `Degree-vs-International.png`| Matplotlib Chart | Grouped bar chart comparing applicant volume by Degree level and domestic/international residency. |
| `Acceptances-over-Time.png` | Matplotlib Chart | Time-series histogram of admissions acceptances binned into 3-day intervals. |
| `GPA-by-Outcome.png` | Matplotlib Chart | Boxplot displaying undergraduate GPA distributions by admissions outcome (`Accepted`, `Rejected`, `Waitlisted`). |
| `Numeric-Correlation-Heatmap.png` | Matplotlib Chart | Annotated correlation heatmap across numeric attributes (`GPA`, `GRE`, `GRE V`, `GRE AW`). |

---

## Key Empirical Findings

1. **Accepted PhD Average GRE:** **162.36 points** ($n = 2,495$, $SD = 4.62$, median = 162.0).
2. **Accepted Master's Average GPA:** **3.70 / 4.00** (mean = 3.6997, $n = 4,531$, $SD = 0.174$, median = 3.70).
3. **GRE Quantitative vs. GRE Verbal Correlation:** Pearson $r = 0.0194, p = 0.1282$ ($n = 6,126$). No statistically significant correlation at $\alpha = 0.05$.
4. **GPA vs. GRE Quantitative Correlation:** Pearson $r = 0.0265, p = 0.0229$; Spearman $\rho = 0.0266, p = 0.0223$ ($n = 7,390$). Statistically significant due to large sample size, but negligible magnitude ($R^2 < 0.001$).
5. **Group Comparison (GPA of Accepted vs. Rejected):**
   - Accepted: mean = 3.6985 ($n = 8,290$)
   - Rejected: mean = 3.7013 ($n = 8,158$)
   - Welch's two-sample $t$-test: $t = -1.0357, p = 0.3003$
   - Mann-Whitney $U$ test: $U = 33,499,895.5, p = 0.3008$
   - **Conclusion:** No statistically significant difference in GPA between accepted and rejected applicants; GPA serves as a threshold qualification while holistic factors govern admissions decisions.
6. **Categorical Association Tests:**
   - **Degree vs. Residency:** $\chi^2 = 0.0670, df = 1, p = 0.7957$. Proportions of international applicants are independent of degree level ($\approx 52.2\%$).
   - **Degree vs. Outcome:** $\chi^2 = 6.2688, df = 2, p = 0.0435$. Marginally significant difference; PhD applicants experienced slightly higher acceptance rates ($45.66\%$ vs $44.59\%$).

---

## Cloud Architecture & Teardown Confirmation

- **Data Ingestion:** The dataset was ingested from Amazon S3 bucket `grad-cafe-nf-594366804861` (`applicant_data.json`).
- **Data Persistence:** The cleaned dataset `cleaned_gradcafe.json` (30,500 records) was uploaded back to S3 (`s3://grad-cafe-nf-594366804861/cleaned_gradcafe.json`).
- **Resource Hygiene:** In compliance with AWS cost management policies, the Amazon SageMaker notebook instance was stopped following pipeline execution ($0.00 ongoing charges).
