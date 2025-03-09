import csv

import pandas as pd
import matplotlib.pyplot as plt
def reorder_author_name(name):
    if pd.isna(name):  # Check for missing values
        return name
    if ',' in name:  # If name already contains a comma, reorder it
        last, first = name.split(',', 1)
        # print(f"{first.strip()} {last.strip()}")
        return f"{first.strip()} {last.strip()}"
    parts = name.split()  # Split name into parts
    if len(parts) < 2:  # If there's only one word, return as is
        return name
    return f"{parts[-1]} {' '.join(parts[:-1])}"  # Reorder the name

def detect_outliers(series, threshold=1.5):
    q1 = series.quantile(0.1)
    q3 = series.quantile(0.9)
    iqr = q3 - q1
    lower_bound = q1 - threshold * iqr
    upper_bound = q3 + threshold * iqr
    return series[(series < lower_bound) | (series > upper_bound)]

def apply_same_schema():
    table_a = pd.read_csv('openlibrary_books.csv')
    table_b = pd.read_csv('gutenberg_books.csv')
    # drop rows with only null values
    table_b = table_b.dropna(how='all')
    # Apply the same schema to both tables
    gutenberg_schema = ['ID', 'title', 'author', 'publisher', 'first_published_year', 'language', 'cover_image']
    openlibrary_schema = ['ID', 'title', 'subtitle', 'author', 'publisher', 'first_published_year', 'language',
                          'cover_image', 'pages', 'rating', 'isbn_10', 'isbn_13']
    # table_a['title'] = table_a.apply(
    #     lambda row: row['title'] if len(row['title']) >= 20 else f"{row['title']} {row['subtitle']}"
    #     if pd.notna(row['subtitle']) else row['title'], axis=1)
    columns_to_drop = set(openlibrary_schema) - set(gutenberg_schema)
    # drop columns that are not in the schema
    table_a = table_a.drop(columns=[col for col in columns_to_drop])
    print(table_a.columns == table_b.columns)
    print(f"Schema of both tables {table_a.columns=}")
    # compute missing values
    missing_values = table_a.isnull().sum()
    print(f"Missing values in table_a:\nFraction:\n{missing_values/len(table_a)}\nPercentage:\n{(missing_values/len(table_a)*100).round(2)}%")
    missing_values = table_b.isnull().sum()
    # print(f"Missing values in table_b:\nFraction:\n{missing_values/len(table_b)}\nPercentage:\n{(missing_values/len(table_b)*100).round(2)}%")
    # classify the columns as numerical or categorical
    # for text columms report average, max and min length
    text_columns = ['ID', 'title', 'author', 'publisher', 'language', 'cover_image']
    numerical_columns = ['first_published_year', ]
    for col in text_columns:
        print(f"{col}:\nAverage length: {table_a[col].str.len().mean()}\nMax length: {table_a[col].str.len().max()}\nMin length: {table_a[col].str.len().min()}")
    # create histograms for text columns
    for col in text_columns + numerical_columns:
        if col in text_columns:
            table_a[col].str.len().hist()
            plt.xlabel('Length')
        elif col in numerical_columns:
            table_a[col].hist()
            plt.xlabel('Value')
        plt.ylabel('Frequency')
        plt.title(col)
        # plt.show()

        # Identify outliers in numerical columns
    for col in numerical_columns:
        outliers = detect_outliers(table_a[col].dropna())
        print(f"Outliers in {col}: {outliers.values}")
    for col in text_columns:
        outliers = detect_outliers(table_a[col].str.len().dropna())
        print(f"Outliers in {col}: {set(table_a[col][table_a[col].str.len().isin(outliers)].values)}")




    # analyse the language column
    set_lang_a = set(table_a['language'])
    # print(f"Languages in table_a: {set_lang_a}")
    set_lang_b = set(table_b['language'])
    # print(f"Languages in table_b: {set_lang_b}")
    # standardize the language column
    table_a['language'] = table_a['language'].replace('English, Middle (1100-1500)', 'Middle English')
    table_a['language'] = table_a['language'].replace('Undetermined', '')
    table_a['language'] = table_a['language'].replace('Spanish, English', 'English')
    table_a['language'] = table_a['language'].replace('French, English', 'French')
    # standardize the name column
    table_b['author'] = table_b['author'].map(reorder_author_name) # replace last name, first name with first name last name
    # replace same publisher / author names with a single name
    table_a['author'] = table_a['author'].replace('3dtotal 3dtotal Publishing', '3DTotal Publishing')
    table_a['author'] = table_a['author'].replace('3dtotal Publishing', '3DTotal Publishing')
    table_a['author'] = table_a['author'].replace('3DTotal.com', '3DTotal Publishing')
    table_a.to_csv('table_a_cleaned.csv', index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')
    table_b.to_csv('table_b_cleaned.csv', index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')


apply_same_schema()