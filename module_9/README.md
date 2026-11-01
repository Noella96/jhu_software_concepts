# Module 9: K-Means Clustering of Grad Cafe Programs

## Contents
- `kmeans.py` – single script: loads `../module_8/cleaned_gradcafe.json`, drops missing programs, splits `program` on the first comma into `Program`/`University`, TF-IDF vectorizes `Program`, runs PCA + K-Means, and writes all figures.
- `initial_cluster.png` – 2-component PCA, K-Means (k=50, `max_iter=100`, `n_init=5`).
- `clustered_dataFrame.png` – 100-row sample of Program / University / Cluster.
- `elbow.png` – inertia for k=1..100 on 100-component PCA (capped at available features).
- `computer_science.png`, `philosophy.png` – GRE and GRE V box plots for the matching clusters.

## Run
```bash
pip install pandas scikit-learn matplotlib
python module_9/kmeans.py
```
Python 3.10+. Seeded with `random_state=42`. Pylint: 10.00/10.

## Results and caveats
- 30,500 entries, but only **24 unique program names** (the Module 8 data is far less varied than the assignment's sample of 2,610).
- The elbow curve drops to zero inertia at k=24 (all distinct points separated), so the assignment's k≈85 is impossible; the script uses `min(85, distinct points)` = 24.
- No Philosophy program exists in this data. `philosophy.png` uses a proxy cluster (**Information Studies**, set by `PHILOSOPHY_PROXY`) and is titled "Philosophy-like".
- Computer Science vs proxy: GRE medians 162 vs 163, GRE V medians 159 vs 159; both ranges 155-170 / 150-168. No CS-specific anomaly visible; scores look suspiciously uniform across every program (same ranges, nearly identical means), which suggests the dataset's score fields need further cleaning/validation.
