
"""
This script scrapes the ISBNs for best-selling books off of Amazon.
It works by constructing a tree of categories/subcategories from each page,
then traverses the tree to add the best-sellers to the ISBN list.
It uses BeautifulSoup to parse the html.

Possible improvements: 
- Extracting ISBNs while constructing the tree.
This didn't work initially, so a separate function was created to walk the tree.
Adding this improvement should cut the time complexity in half in theory.
"""

import requests
from bs4 import BeautifulSoup
import sys

BEST_SELLER_URLS = ["http://www.amazon.com/best-sellers-books-Amazon/zgbs/books/ref=zg_bs_unv_b_1_13913_4",
                    "http://www.amazon.co.jp/gp/bestsellers/english-books/ref=zg_bs_unv_fb_1_101602011_3",
                    "http://www.amazon.co.uk/gp/bestsellers/books/ref=pd_dp_ts_b_1",
                    "http://www.amazon.it/gp/bestsellers/books/ref=zg_bs_unv_b_1_508758031_1",
                    "http://www.amazon.fr/gp/bestsellers/english-books/ref=pd_dp_ts_eb_1",
                    "http://www.amazon.de/gp/bestsellers/books-intl-de/ref=pd_dp_ts_eb_1",
                    "http://www.amazon.es/gp/bestsellers/foreign-books/ref=pd_dp_ts_fb_1"]

def main(filename):
    ISBN_LIST = []
    # Process each url and find best-seller isbns
    print "\nProcessing each page. This might take some time..."
    for url in BEST_SELLER_URLS:
        get_all_best_sellers(url)
        print "Best seller ISBNs for {:.21} have been scraped.".format(url)
    
    # Write the isbn list to file
    with open(filename, 'w') as f:
    for isbn in ISBN_LIST:
        f.write(isbn + '\n')
    print "ISBNs have been saved to file: {}".format(filename)
    
if __name__ == "__main__":
    main(sys.argv[1])

#----- Extract the ISBNs -------
def url_to_soup(url):
    """Helper function to turn url into soup."""
    page = requests.get(url)
    return BeautifulSoup(page.content)

def get_top_100_isbns(category_url):
    """Get the top 100 ISBNS for the category page.
    The top 100 ISBNS are spread across 5 pages. This function opens
    each page and saves the ISBNS to a list. The list is returned."""
    soup = url_to_soup(category_url)
    top_100_links = [item['href'] for item in soup.find_all('a',href=True,ajaxurl=True)]
    isbn_list = []
    for link in top_100_links:
        isbn_list.extend(get_isbns_from_page(link))
    return isbn_list
    
def get_isbns_from_page(page_url):
    """Retrieve a list of isbns from the given page."""
    soup = url_to_soup(page_url)
    href_lyst = [item.a['href'] for item in soup.find_all('div',{'class':'zg_title'})]
    book_lyst = [(href.split('/')[-3],href.split('/')[-1]) for href in href_lyst]
    isbn_lyst = [isbn for _,isbn in book_lyst]
    return isbn_lyst

def get_sub_category_links(page_url):
    """Return a list of subcategory urls/links from the given page."""
    soup = url_to_soup(page_url)
    menu = soup.find('ul',{'id':'zg_browseRoot'})
    lyst = menu.find_all('li',{'class':''})
    return [item.a['href'] for item in lyst if item.a]
               
def add_to_isbn_list(page_url):
    """Processes the url and appends isbns on its page to the global isbn list."""
    isbns = get_top_100_isbns(page_url)
    ISBN_LIST.extend(isbns)
    
def get_all_best_sellers(page_url):
    """Get all best seller isbns, including those for each subcategory.
    Given a page url, it walks through each category and extracts the isbns."""
    head = Node(page_url)
    build_tree(head)
    traverse_tree(head)

#------ Node class for traversing the categories ----------------
class Node(object):
    def __init__(self,url,parent=None):
        self.url = url.split('/ref')[0]
        self.parent = parent
        self.children = []
        
    def add_children(self,lyst):
        child_lyst = [Node(child,parent=self) for child in lyst]
        self.children.extend(child_lyst)

    def find_children(self):
        children = get_sub_category_links(self.url)
        return children

#---- Build a category tree and traverse it --------
def build_tree(node):
    children = node.find_children()
    if node.parent is not None:
        if node.parent.url in children:
            node.children = None
            return
    node.add_children(children)
    for child in node.children:
        build_tree(child)
        
def traverse_tree(node):
    add_to_isbn_list(node.url)
    if node.children is None:
        return
    for child in node.children:
        traverse_tree(child)

