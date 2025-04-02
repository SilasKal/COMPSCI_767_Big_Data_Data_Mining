import csv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from io import BytesIO
from PIL import Image


def mse(image1, image2):
    # Resize images to the same shape
    image1 = image1.resize((300, 200)).convert('RGB')
    image2 = image2.resize((300, 200)).convert('RGB')
    # fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    # axes[0].imshow(image1)
    # axes[0].axis('off')
    # axes[1].imshow(image2)
    # axes[1].axis('off')
    # fig.suptitle(f'Mean Squared Error: {np.mean((np.array(image1) - np.array(image2)) ** 2):.2f}')
    # plt.show()
    image1 = np.array(image1)
    image2 = np.array(image2)

    return np.mean((image1 - image2) ** 2) / 255.0


def get_picture_openbook(url):
    if url.startswith('//'):
        url = 'http:' + url
    elif url.startswith('http'):
        pass
    elif url.startswith('/'):
        return None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            # plt.imshow(image)
            # plt.axis('off')
            # plt.show()
        else:
            print(f"Failed to download image:{url} {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image for ID:{url} {e}")
        return None
    return image
def get_picture_gutenberg(url):
    if url:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                # plt.imshow(image)
                # plt.axis('off')
                # plt.show()
            else:
                print(f"Failed to download image: {url} {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading image for {url} {e}")
            return None
    else:
        return None
    return image

def normalize_title(title):
    common_prefixes = {"the ", "a ", "an "}
    words = title.lower().split()
    # Remove common prefixes if they exist
    if words[0] in common_prefixes:
        words.pop(0)
    return " ".join(words)

def perform_matching():
    table_a = pd.read_csv('table_a_cleaned.csv')
    table_b = pd.read_csv('table_b_cleaned.csv')
    # Normalize titles
    # table_a['title'] = table_a.apply(lambda row: normalize_title(row['title']), axis=1)
    # table_b['title'] = table_b.apply(lambda row: normalize_title(row['title']), axis=1)
    # not used since it performs poorly
    # Create a Cartesian Product (Cross Join)
    table_a = table_a.rename(columns={
        col: f"ltable_{col}" for col in table_a.columns
    })
    table_b = table_b.rename(columns={
        col: f"rtable_{col}" for col in table_b.columns
    })
    table_a['key'] = 1
    table_b['key'] = 1
    table_c = table_a.merge(table_b, on='key').drop(columns=['key'])
    print(f"Size of cartesian product: {len(table_c)}")

    # Compute Title Edit Distance
    table_c['distance_title'] = table_c.apply(
        lambda row: edit_distance(row['ltable_title'], row['rtable_title']) / max(len(row['ltable_title']), len(row['rtable_title'])),
        axis=1
    )

    # Compute Author Edit Distance
    table_c['distance_author'] = table_c.apply(
        lambda row: 1 if pd.isna(row['ltable_author']) or pd.isna(row['rtable_author'])
        else edit_distance(row['ltable_author'], row['rtable_author']) / max(len(row['ltable_author']), len(row['rtable_author'])), axis=1
    )

    # Compute Language Match
    table_c['language_match'] = np.where(
        (table_c['ltable_language'].fillna('') == table_c['rtable_language'].fillna('')) |
        (table_c['ltable_language'].isna() | table_c['rtable_language'].isna()), 1, 0
    )
    print("Finished computing distances and language matches")
    # Filter matches based on distances and language match
    filtered_table_c = table_c[
        (table_c['distance_title'] < 0.6) &
        (table_c['distance_author'] < 0.35) &
        (table_c['language_match'] == 1)
        ]
    filtered_table_c.to_csv('table_c_initial.csv', index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')
    print(f"Size filtered matches: {len(filtered_table_c)}")
    print("Finished filtering matches")
    # Compute Year Difference Normalization
    max_year_diff = filtered_table_c[['ltable_first_published_year', 'rtable_first_published_year']].max().max() - table_c[
        ['ltable_first_published_year', 'rtable_first_published_year']].min().min()
    filtered_table_c['difference_year'] = filtered_table_c.apply(
        lambda row: abs(
            row['ltable_first_published_year'] - row['rtable_first_published_year']) / max_year_diff if max_year_diff > 0 else 0,
        axis=1
    )
    print('Finished computing publish year difference')

    # Compute cover_mse
    filtered_table_c['cover_mse'] = filtered_table_c.apply(
        lambda row: 0 if get_picture_openbook(row['ltable_cover_image']) is None or get_picture_gutenberg(
            row['rtable_cover_image']) is None
        else mse(get_picture_openbook(row['ltable_cover_image']), get_picture_gutenberg(row['rtable_cover_image'])),
        axis=1
    )
    print('Finished computing cover_mse')

    # Compute score
    filtered_table_c['score'] = (0.5 * filtered_table_c['distance_title'] + 0.3 *
                                        filtered_table_c['distance_author'] + 0.1 * filtered_table_c['difference_year']
                                        + 0.1 * filtered_table_c['cover_mse'])
    print('Finished computing score')
    # Add ID column
    filtered_table_c['ID'] = np.arange(len(filtered_table_c))
    filtered_table_c = filtered_table_c[['ID', 'ltable_ID', 'rtable_ID', 'ltable_title', 'rtable_title', 'ltable_author',
                                         'rtable_author', 'ltable_first_published_year', 'rtable_first_published_year',
                                         'ltable_language', 'rtable_language', 'ltable_cover_image', 'rtable_cover_image',
                                         'ltable_publisher', 'rtable_publisher', 'distance_title', 'distance_author',
                                         'difference_year', 'language_match', 'cover_mse', 'score']]
    filtered_table_c.sort_values('score', ascending=True, inplace=True)
    filtered_table_c.to_csv('tableC.csv', index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')

import Levenshtein as lev

def jaccard_similarity(str1, str2):
    a = set(str1.split())
    b = set(str2.split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))

def edit_distance_not_optimized(str1, str2): # not used since it is slow
    len_str1 = len(str1) + 1
    len_str2 = len(str2) + 1

    # Create a matrix
    matrix = np.zeros((len_str1, len_str2), dtype=int)
    matrix[:, 0] = np.arange(len_str1)
    matrix[0, :] = np.arange(len_str2)

    for i in range(1, len_str1):
        for j in range(1, len_str2):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            matrix[i, j] = min(matrix[i-1, j] + 1,      # Deletion
                               matrix[i, j-1] + 1,      # Insertion
                               matrix[i-1, j-1] + cost) # Substitution
    return matrix[len_str1 - 1, len_str2 - 1]

def edit_distance(str1, str2):
    return lev.distance(str1, str2)

perform_matching()