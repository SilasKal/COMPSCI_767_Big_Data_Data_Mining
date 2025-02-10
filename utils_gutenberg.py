import csv
import os
import requests
import time
from bs4 import BeautifulSoup
import pandas as pd

def get_html_pages(query, num_pages):
    # Create directory if it doesn't exist
    output_dir = f"gutenberg_html_pages_{query}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i in range(1, num_pages + 1):
        if query == "relevance":
            url = f"https://www.gutenberg.org/ebooks/search/?sort_order=downloads&start_index={(i - 1) * 25 + 1}"
        else:
            url = f"https://www.gutenberg.org/ebooks/search/?query={query}&submit_search=Go!&start_index={(i-1)*25+1}"
        print(f"Fetching page {i} from {url}")
        print(url)
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(output_dir, f'page_{query}_{i}.html')
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved page {i} to {file_path}")
        else:
            print(f"Failed to fetch page {i}")
        time.sleep(1)  # Delay to avoid being blocked


def get_book_html(input_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    book_counter = 0
    for filename in os.listdir(input_directory):
        if filename.endswith('.html'):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                book_links = soup.find_all("a", class_="link") # extract links to books
                book_links = [link.get('href') for link in book_links]
                for link in book_links:
                    book_url = f"https://www.gutenberg.org{link}"
                    book_html = requests.get(book_url).text
                    book_id = link.split('/')[-1]
                    output_filepath = os.path.join(output_directory, f"{book_id}.html")
                    with open(output_filepath, 'w', encoding='utf-8') as output_file:
                        output_file.write(book_html)
                    book_counter += 1
                    print(f"Saved book {book_id} to {output_filepath}")
                    time.sleep(1)  # delay to avoid being blocked
    print(f"Total books saved: {book_counter}")


def extract_book_title(soup):
    """Extracts the book title"""
    # Find the book name
    book_name = soup.find('td', {'itemprop': 'headline'})

    # Extract the text if found
    book_name_text = book_name.get_text(strip=True) if book_name else None
    return book_name_text

def extract_author(soup):
    """Extracts the author name"""
    # Find the row containing the author
    author_tag = soup.find('a', itemprop='creator')

    # Extract the author's name without the date
    if author_tag:
       author_name = author_tag.get_text(strip=True)
       author_name = ', '.join([part for part in author_name.split(',') if not all(char.isdigit() or char in '?-BCE ' for char in part.strip())])
       return author_name
    return None

def extract_publisher(soup):
    """Extracts the publisher"""
    publisher_tag = soup.find("div", itemprop="publisher")
    return publisher_tag["content"] if publisher_tag else None

def extract_first_published_year(soup):
    """Extracts the first published year"""
    # Find the published date
    published_date = soup.find('td', {'itemprop': 'datePublished'})
    # Extract the text if found
    published_date_text = published_date.get_text(strip=True).split(",")[-1] if published_date else None
    return published_date_text


def extract_cover_image(soup):
    """Extracts the book cover image URL"""
    cover_tag = soup.find("img", class_="cover-art")
    return cover_tag["src"] if cover_tag else None

def extract_language(soup):
    """Extracts the book language"""
    language_row = soup.find('tr', {'property': 'dcterms:language'})
    # Extract the language text from <td>
    language_text = language_row.find('td').get_text(strip=True) if language_row else None
    return language_text

def extract_ebook_number(soup):
    """Extracts the EBook-No."""
    ebook_tag = soup.find("th", string="EBook-No.")
    if ebook_tag:
        ebook_dd = ebook_tag.find_next_sibling("td")
        return ebook_dd.text.strip() if ebook_dd else None
    return None

def process_books_gutenberg(input_directory, output_filepath):
    data = []
    for filename in os.listdir(input_directory):
        if filename.endswith('.html'):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                title = extract_book_title(soup)
                author = extract_author(soup)
                publisher = extract_publisher(soup)
                first_published_year = extract_first_published_year(soup)
                cover_image = extract_cover_image(soup)
                language = extract_language(soup)
                ebook_number = extract_ebook_number(soup)
                data.append({
                    "ID": ebook_number,
                    "title": title,
                    "author": author,
                    "publisher": publisher,
                    "first_published_year": first_published_year,
                    "language": language,
                    "cover_image": cover_image,
                })
    df = pd.DataFrame(data)
    df.to_csv(output_filepath, index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')
    print(f"Processed {len(data)} books and saved to {output_filepath}")


def combine_csv():
    """
    Combines the CSV files generated by the process_books function
    """
    dtype = {
        'first_published_year': str,
        'pages': str,
        'isbn_10': str,
        'isbn_13': str,
        'ID': str
    }
    df1 = pd.read_csv("gutenberg_books_relevance.csv", dtype=dtype)
    df2 = pd.read_csv("gutenberg_books_fantasy.csv", dtype=dtype)
    df = pd.concat([df1, df2])
    print(df.head(5))
    print(df.shape)
    df = df.drop_duplicates(subset=['ID'], keep='first')  # filter out duplicates
    print(df.shape)
    df.to_csv("gutenberg_books.csv", index=False, quoting=csv.QUOTE_MINIMAL, sep=",", na_rep='')
