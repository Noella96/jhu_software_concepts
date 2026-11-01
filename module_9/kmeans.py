"""Cluster Grad Cafe program names with TF-IDF, PCA and K-Means.

Run from any directory: ``python kmeans.py``. All PNG outputs are written
next to this script.
"""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
# pylint: disable=wrong-import-position
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer

OUT_DIR = Path(__file__).resolve().parent
DATA_PATH = OUT_DIR.parent / "module_8" / "cleaned_gradcafe.json"
RANDOM_STATE = 42
DPI = 300
INITIAL_K = 50
FINAL_K = 85  # assignment target; capped at distinct points (see final_clustering)
PHILOSOPHY_PROXY = "Information Studies"  # dataset has no Philosophy program
MAX_K = 100
HIGH_DIM_COMPONENTS = 100


def load_programs(path=DATA_PATH):
    """Load raw records, drop missing programs, split program/university."""
    raw = pd.read_json(path)
    raw["program"] = raw["program"].replace(r"^\s*$", None, regex=True)
    raw = raw[raw["program"].notna() & (raw["program"].str.strip() != "None")]
    raw = raw.reset_index(drop=True)
    parts = raw["program"].str.split(",", n=1, expand=True)
    raw["Program"] = parts[0].str.strip()
    raw["University"] = parts[1].str.strip() if 1 in parts else ""
    raw["University"] = raw["University"].fillna("")
    return raw


def vectorize(programs):
    """Return fitted TF-IDF sparse matrix of program names."""
    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english")
    return vectorizer.fit_transform(programs)


def save_current(name):
    """Save the current matplotlib figure as a tight 300 DPI PNG."""
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=DPI, bbox_inches="tight")
    plt.close()


def plot_initial_clusters(coords, labels):
    """Scatter the 2-D PCA projection coloured by cluster."""
    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(coords[:, 0], coords[:, 1], c=labels, cmap="nipy_spectral",
                          s=8, alpha=0.7, label="Program entry")
    plt.colorbar(scatter, label="Cluster number")
    plt.title("Initial K-Means Clustering of Grad Cafe Programs (k=50)")
    plt.xlabel("PCA component 1 (unitless)")
    plt.ylabel("PCA component 2 (unitless)")
    plt.legend(loc="upper right")
    save_current("initial_cluster.png")


def save_dataframe_image(frame, name, rows=100):
    """Render the first rows of a DataFrame as a table image."""
    sample = frame.head(rows)
    fig, axis = plt.subplots(figsize=(10, 0.22 * rows + 1))
    axis.axis("off")
    table = axis.table(cellText=sample.values, colLabels=sample.columns,
                       loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(6)
    table.auto_set_column_width(list(range(len(sample.columns))))
    axis.set_title("Clustered Grad Cafe Programs (first 100 rows)")
    fig.savefig(OUT_DIR / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def initial_clustering(matrix, frame):
    """PCA to 2-D, K-Means with 50 clusters, plot and table outputs."""
    coords = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform(
        matrix.toarray())
    print(f"PCA feature shape: {coords.shape}")
    model = KMeans(n_clusters=INITIAL_K, max_iter=100, n_init=5,
                   random_state=RANDOM_STATE).fit(coords)
    plot_initial_clusters(coords, model.labels_)
    clustered = frame[["Program", "University"]].copy()
    clustered["Cluster"] = model.labels_
    ordered = clustered.sort_values("Cluster", kind="stable")
    # Take rows spread across clusters so the sample shows several groups.
    sample = ordered.iloc[:: max(len(ordered) // 100, 1)].head(100)
    save_dataframe_image(sample.sort_values("Cluster"), "clustered_dataFrame.png")


def elbow_analysis(features, chosen_k):
    """Run K-Means for k=1..100 and plot inertia."""
    ks = list(range(1, MAX_K + 1))
    inertia = [KMeans(n_clusters=k, n_init=1, max_iter=100,
                      random_state=RANDOM_STATE).fit(features).inertia_
               for k in ks]
    plt.figure(figsize=(9, 6))
    plt.plot(ks, inertia, marker="o", markersize=3, label="Inertia")
    plt.axvline(chosen_k, color="red", linestyle="--", label=f"Chosen k={chosen_k}")
    plt.title("Elbow Method: K-Means Inertia vs. Cluster Count")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia (sum of squared distances)")
    plt.legend()
    save_current("elbow.png")


def find_cluster(frame, keyword):
    """Return the cluster holding most rows whose Program matches keyword."""
    mask = frame["Program"].str.contains(keyword, case=False, na=False)
    if not mask.any():
        raise ValueError(f"No program matches {keyword!r}")
    return int(frame.loc[mask, "Cluster"].value_counts().idxmax())


def box_plot(frame, cluster, title, name):
    """Box plot of GRE and GRE V for one cluster."""
    subset = frame.loc[frame["Cluster"] == cluster, ["GRE", "GRE V"]]
    subset = subset.apply(pd.to_numeric, errors="coerce")
    print(f"\n{title} (cluster {cluster}, n={len(subset)})")
    print(subset.describe().round(2).to_string())
    fig, axes = plt.subplots(1, 2, figsize=(9, 6))
    for axis, col, color in zip(axes, ["GRE", "GRE V"], ["tab:blue", "tab:orange"]):
        values = subset[col].dropna()
        axis.boxplot(values, patch_artist=True, boxprops={"facecolor": color})
        axis.set_xticks([1], [col])
        axis.set_xlabel("Score type")
        axis.set_ylabel(f"{col} score (points)")
        axis.legend([axis.patches[0]], [f"{col} (n={len(values)})"], loc="best")
    fig.suptitle(title)
    fig.savefig(OUT_DIR / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def final_clustering(matrix, frame):
    """High-dim PCA, elbow, final K-Means, and CS vs Philosophy analysis."""
    n_comp = min(HIGH_DIM_COMPONENTS, matrix.shape[1] - 1)
    features = PCA(n_components=n_comp, random_state=RANDOM_STATE).fit_transform(
        matrix.toarray())
    print(f"High-dim PCA shape: {features.shape}")
    # K-Means cannot form more non-empty clusters than distinct feature rows.
    chosen_k = min(FINAL_K, len(pd.DataFrame(features).drop_duplicates()))
    print(f"Final k: {chosen_k} (target {FINAL_K})")
    elbow_analysis(features, chosen_k)
    frame["Cluster"] = KMeans(n_clusters=chosen_k, n_init=5, max_iter=100,
                              random_state=RANDOM_STATE).fit_predict(features)
    cs_cluster = find_cluster(frame, "computer science")
    try:
        phil_cluster = find_cluster(frame, "philosophy")
    except ValueError:
        print(f"No Philosophy program in data; using proxy {PHILOSOPHY_PROXY!r}")
        phil_cluster = find_cluster(frame, PHILOSOPHY_PROXY)
    box_plot(frame, phil_cluster, "Philosophy-like Cluster: GRE and GRE V Scores",
             "philosophy.png")
    box_plot(frame, cs_cluster, "Computer Science Cluster: GRE and GRE V Scores",
             "computer_science.png")
    return frame


def main():
    """Run the full Module 9 pipeline."""
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", message="Number of distinct clusters")
    frame = load_programs()
    print(f"Number of Entries: {len(frame):,}")
    print(f"Number of Program Input Names: {frame['Program'].nunique():,}")
    matrix = vectorize(frame["Program"])
    print(f"TF-IDF type: {type(matrix).__name__}, shape: {matrix.shape}")
    initial_clustering(matrix, frame)
    final_clustering(matrix, frame)


if __name__ == "__main__":
    main()
