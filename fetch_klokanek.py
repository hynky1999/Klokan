import os
import requests

# Ensure the 'pdfs' directory exists
if not os.path.exists('pdfs'):
    os.makedirs('pdfs')

# Loop through the years
for year in range(2004, 2023):
    # Construct the URL
    url = f"https://matematickyklokan.net/phocadownload/sborniky/sbornik_klokan_{year}.pdf"
    
    # Fetch the content from the URL
    response = requests.get(url)
    
    # Ensure the request was successful
    if response.status_code == 200:
        # Write the content to a file
        with open(f'pdfs/sbornik_klokan_{year}.pdf', 'wb') as f:
            f.write(response.content)