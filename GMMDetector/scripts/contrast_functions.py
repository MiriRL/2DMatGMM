import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

from App.image_processing import calculate_background_color, remove_vignette
from sklearn.mixture import GaussianMixture

def get_contrasts_from_img(
    image_path,
    mask_path
):
    contrasts = []

    mask_name = os.path.basename(mask_path)

    
    print(f"{mask_name} read", end="\r")

    # check if the image is either in the png or jpg format
    if not os.path.exists(image_path):
        print(f"Could not find image corresponding to mask '{mask_name}', skipping")

    mask = cv2.imread(mask_path, 0)
    image = cv2.imread(image_path)

    assert mask is not None, f"Could not load mask {mask_path}"
    assert image is not None, f"Could not load image {image_path}"

    mask = cv2.erode(
        mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1
    )

    # If the mask is empty, skip this image
    if cv2.countNonZero(mask) < 10:
        return None

    flake_color = np.array(image[mask != 0])
    bg_color = calculate_background_color(image, 10)
    
    background_color = np.array(bg_color)

    if np.any(background_color == 0):
        print(f"Error with image {os.path.basename(image_path)}; Invalid Background {bg_color}, skipping")
        return None

    flake_contrast = (flake_color / background_color) - 1

    contrasts.extend(flake_contrast)

    contrasts = np.array(contrasts)

    return contrasts

def create_histogram_plots(image_contrast_dict, num_components=2, bins=100, save_results=False, results_dir=None):
    """
    Display BGR histograms stacked vertically above each image using OpenCV for image loading.

    Parameters:
    - image_contrast_dict (dict): A dictionary where keys are image file paths,
      and values are NumPy arrays of RGB values used for contrast analysis.
    """

    for image_path, contrast_data in image_contrast_dict.items():
        # Load the image using cv2 (BGR by default), then convert to RGB
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            print(f"Warning: Could not load image at {image_path}")
            continue
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)  # For displaying the image properly
        file_name = os.path.basename(image_path)

        # Create figure with 4 vertically stacked plots (3 histograms + 1 image)
        fig, axs = plt.subplots(4, 1, figsize=(8, 10), gridspec_kw={'height_ratios': [1, 1, 1, 3]})
        fig.suptitle(f"{file_name}: Color contrast histograms", fontsize=14)

        # Channel info
        channel_colors = ['blue', 'green', 'red']
        channel_names = ['Blue', 'Green', 'Red']

        for i in range(3):
            if contrast_data is None:
                # If the contrast data was invalid, we skip it
                break
            data = contrast_data[:, i].reshape(-1)

            # Autoscale: define bin edges based on data min/max with padding
            data_min, data_max = data.min(), data.max()
            range_padding = (data_max - data_min) * 0.1 if data_max != data_min else 0.1
            x_min = data_min - range_padding
            x_max = data_max + range_padding

            # Histogram bins and density
            bins = np.linspace(x_min, x_max, 100)
            counts, bin_edges = np.histogram(data, bins=bins)
            bin_widths = np.diff(bin_edges)
            # Normalize
            total_count = np.sum(counts)
            with np.errstate(divide='ignore', invalid='ignore'):
                density = np.divide(counts, total_count * bin_widths, 
                                    out=np.zeros_like(counts, dtype=float), 
                                    where=bin_widths > 0)

            # Plot histogram
            axs[i].bar(bin_edges[:-1], density, width=bin_widths, color=channel_colors[i], alpha=0.6, align='edge', edgecolor='black')
            axs[i].set_xlim(x_min, x_max)
            axs[i].set_ylabel(f'{channel_names[i]} Count')

            # Fit 2-Gaussian GMM
            gmm = GaussianMixture(n_components=num_components, random_state=0)
            gmm.fit(data.reshape(-1, 1))

            # Overlay Gaussian PDFs and then annotate peaks
            x_vals = np.linspace(x_min, x_max, 512).reshape(-1, 1)
            for mean, std, weight in zip(gmm.means_.flatten(), 
                                        np.sqrt(gmm.covariances_).flatten(), 
                                        gmm.weights_.flatten()):
                pdf = weight * (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_vals - mean) / std) ** 2)
                axs[i].plot(x_vals, pdf, color=channel_colors[i], linewidth=2)

            means = gmm.means_.flatten()
            # Draw vertical lines at peaks
            for mean in means:
                axs[i].axvline(x=mean, color='black', linestyle=':', linewidth=1.5)

            # Annotate means with their x-values
            for mean in means:
                axs[i].text(mean, axs[i].get_ylim()[1]*0.85, f"{mean:.3f}",
                            rotation=90, va='bottom', ha='center',
                            fontsize=9, color='black', backgroundcolor='white')

            # If exactly two peaks, calculate and display their difference
            if len(means) == 2:
                peak_diff = abs(means[0] - means[1])
                axs[i].text(0.95, 0.95, f"Δ peaks = {peak_diff:.3f}",
                            transform=axs[i].transAxes,
                            ha='right', va='top',
                            fontsize=10,
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

            if i == 2:
                axs[i].set_xlabel("Contrast Value")


        # Show the image
        axs[3].imshow(image_rgb)
        axs[3].axis('off')

        plt.tight_layout()
        plt.subplots_adjust(top=0.92)  # Make room for title
        plt.show()

        if save_results:
            # Save the figure
            os.makedirs(results_dir, exist_ok=True)
            assert os.path.exists(results_dir), f"Results directory {results_dir} does not exist"
            graph_name = file_name.replace('.png', '_histogram.png').replace('.jpg', '_histogram.png').replace('.tif', '_histogram.png')  # Makes the graph a png file
            fig.savefig(os.path.join(results_dir, graph_name), bbox_inches='tight')
            print(f"Saved histogram plot to {results_dir}")