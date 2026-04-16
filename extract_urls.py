import os
import django
from django.conf import settings
from django.urls import get_resolver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HRM.settings')
django.setup()

def get_urls(url_patterns, prefix=''):
    urls = []
    for pattern in url_patterns:
        if hasattr(pattern, 'url_patterns'):
            urls.extend(get_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
        else:
            urls.append(prefix + str(pattern.pattern))
    return urls

urls = get_urls(get_resolver().url_patterns)
with open('extracted_urls.txt', 'w') as f:
    for url in urls:
        f.write(f"/{url}\n")
print("Done extracting URLs!")
