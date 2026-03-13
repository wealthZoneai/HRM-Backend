import json
import re

# Read extracted URLs
with open('extracted_urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith('/admin')]

# Define the base collection structure
collection = {
    "info": {
        "name": "HRM Backend API",
        "description": "Auto-generated Postman collection for the HRM Django Backend",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [],
    "variable": [
        {
            "key": "base_url",
            "value": "http://127.0.0.1:8000",
            "type": "string"
        },
        {
            "key": "token",
            "value": "",
            "type": "string"
        }
    ]
}

# Group URLs by their first path segment (e.g., /api/hr -> hr, /api/emp -> emp, /support -> support)
groups = {}

def get_method_from_url(url):
    url_lower = url.lower()
    if 'create' in url_lower or 'add' in url_lower or 'apply' in url_lower or 'submit' in url_lower or 'login' in url_lower:
        return 'POST'
    elif 'update' in url_lower or 'edit' in url_lower or 'action' in url_lower:
        return 'PUT' # or PATCH
    elif 'delete' in url_lower or 'remove' in url_lower:
        return 'DELETE'
    return 'GET'

def format_path_variables(url):
    # Convert Django /<int:pk>/ to Postman /:pk/
    formatted_url = re.sub(r'<[^:]+:([^>]+)>', r':\1', url)
    
    # Extract variables for Postman request
    variables = []
    matches = re.finditer(r'<[^:]+:([^>]+)>', url)
    for match in matches:
        var_name = match.group(1)
        variables.append({
            "key": var_name,
            "value": "1",
            "description": f"Auto-generated variable for {var_name}"
        })
        
    return formatted_url, variables

for url in urls:
    # Skip swagger/schema endpoints
    if 'schema' in url or 'swagger' in url or 'redoc' in url:
        continue
        
    parts = [p for p in url.split('/') if p]
    if not parts:
        continue
        
    # Determine grouping folder
    folder_name = "General"
    if parts[0] == "api" and len(parts) > 1:
        folder_name = parts[1].capitalize()
        name = " ".join(parts[2:]).replace('-', ' ').replace('_', ' ').title() or folder_name
    else:
        folder_name = parts[0].capitalize()
        name = " ".join(parts[1:]).replace('-', ' ').replace('_', ' ').title() or folder_name
        
    if not name.strip() or name.startswith('<'):
        name = "Endpoint"
        
    if folder_name not in groups:
        groups[folder_name] = []
        
    method = get_method_from_url(url)
    postman_url, variables = format_path_variables(url)
    
    # Create request item
    request_item = {
        "name": f"{method} {name}",
        "request": {
            "method": method,
            "header": [
                {
                    "key": "Authorization",
                    "value": "Bearer {{token}}",
                    "type": "text"
                }
            ],
            "url": {
                "raw": f"{{{{base_url}}}}{postman_url}",
                "host": ["{{base_url}}"],
                "path": [p for p in postman_url.split('/') if p],
                "variable": variables
            }
        },
        "response": []
    }
    
    # Add body for POST/PUT
    if method in ['POST', 'PUT', 'PATCH']:
        request_item['request']['body'] = {
            "mode": "raw",
            "raw": "{}",
            "options": {
                "raw": {
                    "language": "json"
                }
            }
        }
        
    groups[folder_name].append(request_item)

# Build final collection
for folder_name, items in groups.items():
    if len(items) == 1:
        collection["item"].append(items[0])
    else:
        collection["item"].append({
            "name": folder_name,
            "item": items
        })

# Save to file
with open('HRM_Postman_Collection.json', 'w') as f:
    json.dump(collection, f, indent=4)

print("Collection generated: HRM_Postman_Collection.json")
