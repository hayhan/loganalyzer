# Licensed under the MIT License - see LICENSE.txt
""" Visualization of dataset """
import numpy as np
import matplotlib.pyplot as plt
# import seaborn as sns
# from sklearn.preprocessing import StandardScaler
import umap


__all__ = [
    "visualize_with_umap",
]


# https://umap-learn.readthedocs.io/en/latest/basic_usage.html
def visualize_with_umap(dataset, labels):
    """ Visaulize dataset with umap """
    reducer = umap.UMAP(random_state=42)
    reducer.fit(dataset)

    embedding = reducer.transform(dataset)
    # Verify that the result of calling transform is idenitical to
    # accessing the embedding_ attribute
    assert np.all(embedding == reducer.embedding_)
    print(embedding.shape)

    target_len = len(set(labels))
    plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='Spectral', s=5)
    plt.gca().set_aspect('equal', 'datalim')
    plt.colorbar(boundaries=np.arange(target_len+1)-0.5).set_ticks(np.arange(target_len))
    plt.title('UMAP projection of the dataset', fontsize=24)
    plt.show()
