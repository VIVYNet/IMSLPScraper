# Imports
from urllib.request import urlopen
from urllib.parse import quote
from bs4 import BeautifulSoup
import concurrent.futures
import traceback
import pymongo
import uuid
import json

# Read file
login_info = json.load(open("login.json"))

# Get login info from login file
ADDRESS = login_info["address"]
PORT = login_info["port"]
USERNAME = login_info["username"]
PASSWORD = login_info["password"]

# Connect to MongoDB, whilst checking if the login file specified localhost
if ADDRESS.lower() == "localhost":
    client = pymongo.MongoClient(f"mongodb://localhost/")
else:
    client = pymongo.MongoClient(f"mongodb://{USERNAME}:{PASSWORD}@{ADDRESS}:{PORT}/")

# Get all databases and the targeted collection
db = client['VIVY']
col = db['imslpCOL']

# # COMMENT OR DELETE
# col.drop()
# col = db['imslpCOL_test']

# Helper function
def scrape(key, value):
    # Try
    try:
        # Continue if the key is "metadata"
        if key == "metadata":
            # Print status
            print("-= NEXT PAGE =-")
            
            # Return
            return
        
        # Query if 
        litmus = col.find_one({"title": value["intvals"]["worktitle"], 
                               "composer": value["intvals"]["composer"]})
        
        # Check if litmus returns something
        if litmus:
            # Print status
            print("Skipped Link")
            
            # Return
            return
        
        # Create a temp variable to hold download links
        table_info = {}
        links = []
        
        # Get title, composer, and link information
        id = uuid.uuid4().hex
        title = value["intvals"]["worktitle"]       
        composer = value["intvals"]["composer"]
        page_link = value["permlink"]
        
        # Print page
        print(page_link)
        
        # Make a bs4 instance of the page link of iterated item
        html_page = urlopen("https:" + quote(page_link[6:]))
        soup = BeautifulSoup(html_page, "lxml")
        
        # Iterate through all 'a' tags in the page
        for link in soup.findAll('a'):
            # Search for links that contain the string "ImageFromIndex"
            if "ImagefromIndex" in str(link.get("href")):
                # Put link into list
                links.append(link.get("href").replace("ImagefromIndex", "IMSLPDisclaimerAccept") + "/hfnm")
        
        # Get the table information of the iterated page
        div = soup.find('div', attrs={'class': 'wi_body'})
        table = div.find('table', attrs={'border': '0'})
        table_contents = table.find_all('tr')
        
        # Iterate through the rows of the table
        for i in table_contents:            
            # Get header and span elements
            header = i.find("th")
            spans = header.find("span")
            
            # Check if there is no span elements
            if spans:                
                # Get the first span
                key = spans.text
                
                # Check if the text is "ernative"
                if "ernative" in key:
                    # Add alternative title info
                    table_info["Alternative Title"] = i.find("td").text.rstrip()
                    
                    # Continue
                    continue
                
                # Continue to add info
                table_info[key] = i.find("td").text.rstrip()
                
                # Continue
                continue
            
            # Insert information from information table to a dictionary            
            table_info[i.find("th").text.rstrip()] = i.find("td").text.rstrip()
            
        # Stage data
        single_data = {
            "_id": id,
            "title": title,
            "composer": composer,
            "link": page_link,
            "information": table_info,
            "links": links
        }
        
        # Insert into collection
        col.insert_one(single_data)
    
    # Except
    except Exception as e:
        # Print status
        print("One link not added")
        
        # Log error
        with open(f'logs/{uuid.uuid4().hex}.txt', 'w') as file:
            traceback.print_exc(file=file)

# Main process
if __name__ == '__main__':
    # Iterate through IMSLP's API
    for i in range(0, 1000000, 1000):
        # Try:
        try:
            # Get JSON response from IMSLP API
            response = urlopen(f"https://imslp.org/imslpscripts/API.ISCR.php?account=worklist/disclaimer=accepted/sort=id/type=2/start={i}/retformat=json")
            
            # Format into dictionary datatype
            data = json.loads(response.read().decode("utf-8"))
            
        # Except
        except Exception as e:
            # Print status
            print("One link not added")
            
            # Log error
            with open(f'logs/{uuid.uuid4().hex}.txt', 'w') as file:
                traceback.print_exc(file=file)
                
        with concurrent.futures.ProcessPoolExecutor() as executor:
            _ = [executor.submit(scrape, key, value) for key, value in data.items()]
            
        # # Iterate through each item in the dictionary
        # for key, value in data.items():
        #     # Call scrape function
        #     scrape(key, value)
    