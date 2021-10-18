# Licensed under the MIT License - see LICENSE.txt
""" Visualization of dataset """
from typing import List
import numpy as np
import matplotlib.pyplot as plt
# import seaborn as sns
# from sklearn.preprocessing import StandardScaler
import umap


__all__ = [
    "visualize_with_umap",
]


# https://umap-learn.readthedocs.io/en/latest/basic_usage.html
def visualize_with_umap(dataset: np.ndarray, targets: List[int], label: bool):
    """ Visaulize dataset with umap """
    reducer = umap.UMAP(random_state=42)
    reducer.fit(dataset)

    embedding = reducer.transform(dataset)
    # Verify that the result of calling transform is idenitical to
    # accessing the embedding_ attribute
    assert np.all(embedding == reducer.embedding_)
    print(embedding.shape)

    tgt_len = len(set(targets))
    plt.scatter(embedding[:, 0], embedding[:, 1], c=targets, cmap='Spectral', s=5)
    plt.gca().set_aspect('equal', 'datalim')
    plt.colorbar(boundaries=np.arange(tgt_len+1)+0.5).set_ticks(np.arange(tgt_len)+1)
    plt.title('UMAP projection of the dataset', fontsize=24)

    if label:
        for i, tgt in enumerate(targets):
            plt.annotate(tgt, (embedding[:, 0][i], embedding[:, 1][i]), fontsize=10)

    plt.show()
