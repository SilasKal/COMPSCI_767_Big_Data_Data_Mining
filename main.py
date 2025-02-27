import utils_gutenberg as gb
import utils_openlibrary as ol

if __name__ == "__main__":
    # Assignment 1
    # extract data from gutenberg trending
    gb.get_html_pages("relevance", 50)
    gb.get_book_html("gutenberg_html_pages_relevance", "gutenberg_html_books_relevance")
    gb.process_books_gutenberg("gutenberg_html_books_relevance", "gutenberg_books_relevance.csv")
    # extract data from gutenberg fantasy
    gb.get_html_pages("fantasy", 50)
    gb.get_book_html("gutenberg_html_pages_fantasy", "gutenberg_html_books_fantasy")
    gb.process_books_gutenberg("gutenberg_html_books_fantasy", "gutenberg_books_fantasy.csv")
    gb.combine_csv() # combine the two csv files
    # extract data from openlibrary trending
    ol.get_html_pages("relevance", 50)
    ol.get_book_html("openlibrary_html_pages_relevance", "openlibrary_html_books_relevance")
    ol.process_books("openlibrary_html_books_relevance", "openlibrary_books_relevance.csv")
    # extract data from openlibrary fantasy
    ol.get_html_pages("fantasy", 50)
    ol.get_book_html("openlibrary_html_pages_fantasy", "openlibrary_html_books_fantasy")
    ol.process_books("openlibrary_html_books_fantasy", "openlibrary_books_fantasy.csv")
    ol.combine_csv() # combine the two csv files
    # Assignment 2


