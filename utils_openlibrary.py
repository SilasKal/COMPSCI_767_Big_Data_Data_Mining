import csv
import re
from bs4 import BeautifulSoup
import os
import requests
import time

def get_html_pages(query, num_pages):
    """
    Fetches the HTML pages from the Open Library website to extract links to books
    :param query: Query string to search for books
    :param num_pages: Number of pages to fetch
    """
    output_dir = "openlibrary_html_pages"
    base_url = "https://openlibrary.org/"
    if query == "relevance":
        base_url = "https://openlibrary.org/trending/now?page=" # most relevant books open library
        output_dir = "openlibrary_html_pages_relevance"
    elif query == "fantasy":
        base_url = f"https://openlibrary.org/search?q=fantasy&mode=everything&page=" # fantasy books
        output_dir = "openlibrary_html_pages_fantasy"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i in range(1, num_pages + 1):
        url = base_url + str(i)
        print(f"Fetching page {i} from {url}")
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(output_dir, f'page_{i}.html')
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved page {i} to {file_path}")
        else:
            print(f"Failed to fetch page {i}")
        time.sleep(1)  # small delay to avoid being blocked


def get_book_html(input_directory, output_directory):
    """
    extracts the book html pages from the Open Library website
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    for filename in os.listdir(input_directory):
        if filename.endswith('.html'):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                book_links = soup.findAll("a", class_="results") # extract links to books
                book_links = [link.get('href') for link in book_links]
                for link in book_links:
                    book_url = f"https://openlibrary.org{link}"
                    book_html = requests.get(book_url).text
                    book_id = link.split('/')[-1]
                    output_filepath = os.path.join(output_directory, f"{book_id}.html")
                    with open(output_filepath, 'w', encoding='utf-8') as output_file:
                        output_file.write(book_html)


def extract_book_title(soup):
    """Extracts the book title"""
    title_tag = soup.find("h1", class_="work-title")
    return title_tag.text.strip() if title_tag else None

def extract_book_subtitle(soup):
    """Extracts the book subtitle"""
    subtitle_tag = soup.find("h2", class_="work-subtitle")
    return subtitle_tag.text.strip() if subtitle_tag else None

def extract_author(soup):
    """Extracts the author name"""
    author_tag = soup.find("a", itemprop="author")
    return author_tag.text.strip() if author_tag else None

def extract_first_published_year(soup):
    """Extracts the first published year"""
    published_tag = soup.find("span", class_="first-published-date")
    return published_tag.text.strip("()").replace("(", "").replace(")", "") if published_tag else None

def extract_rating(soup):
    """Extracts the rating value"""
    rating_tag = soup.find("span", itemprop="ratingValue")
    return rating_tag.text.strip() if rating_tag else None

def extract_cover_image(soup):
    """Extracts the book cover image URL"""
    cover_tag = soup.find("img", class_="cover")
    return cover_tag["src"] if cover_tag else None


def extract_publisher(soup):
    """Extracts the publisher from the book html"""
    publisher_tag = soup.find("a", itemprop="publisher")
    return publisher_tag.text.strip() if publisher_tag else None

def extract_number_of_pages(soup):
    """Extracts the number of pages from the book html"""
    pages_tag = soup.find("span", class_="edition-pages", itemprop="numberOfPages")
    return pages_tag.text.strip() if pages_tag else None

def extract_language(soup):
    """Extracts the book language from the book html"""
    language_tag = soup.find("span", itemprop="inLanguage")
    return language_tag.text.strip() if language_tag else None

def extract_isbn_10(soup):
    """Extracts the ISBN-10 number from the book html"""
    isbn10_tag = soup.find("dd", class_="object", itemprop="isbn")
    if isbn10_tag:
        numbers = re.findall(r'\b\d{10}\b', isbn10_tag.text.strip())
        if numbers:
            return numbers[0]
    return None

def extract_isbn_13(soup):
    """Extracts the ISBN-13 number from the book html"""
    isbn10_tag = soup.find("dd", class_="object", itemprop="isbn")
    if isbn10_tag:
        numbers = re.findall(r'\b\d{13}\b', isbn10_tag.text.strip())
        if numbers:
            return numbers[0]
    return None

def extract_work_id(soup):
    """Extracts the Work ID from the book html"""
    work_id_dt = soup.find("dt", string="Work ID")
    if work_id_dt:
        work_id_dd = work_id_dt.find_next_sibling("dd", class_="object")
        return work_id_dd.text.strip() if work_id_dd else None
    return None

import pandas as pd
def process_books(input_directory, output_file):
    """
    uses extraction functions and saves the data to a CSV file
    """
    data = []

    for filename in os.listdir(input_directory):
        if filename.endswith('.html'):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                title = extract_book_title(soup)

                subtitle = extract_book_subtitle(soup)
                author = extract_author(soup)
                first_published_year = extract_first_published_year(soup)
                rating = extract_rating(soup)
                cover_image = extract_cover_image(soup)
                pages = extract_number_of_pages(soup)
                language = extract_language(soup)
                publisher = extract_publisher(soup)
                isbn_10 = extract_isbn_10(soup)
                isbn_13 = extract_isbn_13(soup)
                work_id = extract_work_id(soup)
                data.append({
                    'ID': work_id,
                    'title': title,
                    'subtitle': subtitle,
                    'author': author,
                    'publisher': publisher,
                    'first_published_year': first_published_year,
                    'language': language,
                    'cover_image': cover_image,
                    'pages': pages,
                    'rating': rating,
                    'isbn_10': isbn_10,
                    'isbn_13': isbn_13

                })

    df = pd.DataFrame(data)
    print(df.head(5))
    df = df.map(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')
    print(f"Data saved to {output_file}")

def combine_csv():
    """
    Combines the CSV files generated by the process_books function
    """
    dtype = {
        'first_published_year': str,
        'pages': str,
        'isbn_10': str,
        'isbn_13': str
    }
    df1 = pd.read_csv("openlibrary_books_relevance.csv", dtype=dtype)
    df2 = pd.read_csv("openlibrary_books_fantasy.csv", dtype=dtype)
    df = pd.concat([df1, df2])
    df = df.drop_duplicates(subset=['ID'], keep='first')  # filter out duplicates
    df.to_csv("openlibrary_books.csv", index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')


