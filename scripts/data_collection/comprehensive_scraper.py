#!/usr/bin/env python3
"""
Comprehensive Sri Lanka Historical Sites Scraper
Combines Wikipedia, Wikidata, and manual sources for complete coverage
"""

import requests
import pandas as pd
import json
import time
import os
from bs4 import BeautifulSoup
from pathlib import Path


class ComprehensiveSriLankaScraper:
    """Multi-source scraper for all Sri Lanka historical sites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.sites = []
        self.failed_sites = []

    def scrape_wikidata(self):
        """Query Wikidata for all historical sites in Sri Lanka"""
        print("\n📡 Querying Wikidata for Sri Lanka historical sites...")
        
        sparql_query = """
        SELECT ?item ?itemLabel ?location ?locLabel ?inception ?significant_date ?coordinates
        WHERE {
            ?item wdt:P131 ?location.
            ?location wdt:P131* wd:Q854.
            ?item wdt:P31 wd:Q839954.
            FILTER (?item != ?location)
            SERVICE wikibase:label { 
                bd:serviceParam wikibase:language "en". 
                ?item rdfs:label ?itemLabel.
                ?location rdfs:label ?locLabel.
            }
        }
        LIMIT 500
        """
        
        url = "https://query.wikidata.org/sparql"
        params = {
            'query': sparql_query,
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', {}).get('bindings', [])
                print(f"✓ Found {len(results)} sites from Wikidata")
                return results
        except Exception as e:
            print(f"✗ Wikidata query failed: {e}")
        
        return []

    def scrape_from_wikidata_results(self, results):
        """Convert Wikidata results to site records"""
        for result in results:
            try:
                site_name = result.get('itemLabel', {}).get('value', '')
                location = result.get('locLabel', {}).get('value', '')
                
                if site_name and site_name not in [s['site_name'] for s in self.sites]:
                    self.sites.append({
                        'site_name': site_name,
                        'location': location,
                        'description': f"Historical site in {location}, Sri Lanka",
                        'source': 'Wikidata',
                        'category': 'Historical Site',
                        'url': f"https://www.wikidata.org/wiki/{result.get('item', {}).get('value', '').split('/')[-1]}"
                    })
            except:
                pass

    def scrape_wikipedia_index(self):
        """Get historical sites from Wikipedia category pages"""
        print("\n📖 Scraping Wikipedia categories for Sri Lanka historical sites...")
        
        categories = [
            "Ancient_cities_in_Sri_Lanka",
            "Buddhist_temples_in_Sri_Lanka",
            "Forts_in_Sri_Lanka",
            "Hindu_temples_in_Sri_Lanka",
            "Mosques_in_Sri_Lanka",
            "Churches_in_Sri_Lanka",
            "Palaces_in_Sri_Lanka",
            "Archaeological_sites_in_Sri_Lanka",
            "Cultural_heritage_sites_of_Sri_Lanka",
            "Museums_in_Sri_Lanka",
            "Waterfalls_in_Sri_Lanka",
            "National_parks_of_Sri_Lanka",
            "Rock_formations_in_Sri_Lanka"
        ]
        
        for category in categories:
            try:
                url = f"https://en.wikipedia.org/wiki/Category:{category}"
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                links = soup.find_all('a', class_='CategoryTreeLabel')
                if not links:
                    links = soup.find_all('a')[10:40]  # Fallback
                
                for link in links[:15]:
                    site_name = link.get_text().strip()
                    if site_name and len(site_name) > 3 and site_name not in [s['site_name'] for s in self.sites]:
                        self.sites.append({
                            'site_name': site_name,
                            'description': f"{site_name} - {category.replace('_', ' ')}",
                            'source': 'Wikipedia Category',
                            'category': category.replace('_', ' '),
                            'url': f"https://en.wikipedia.org/wiki/{site_name.replace(' ', '_')}"
                        })
                
                time.sleep(0.5)  # Rate limit
            except Exception as e:
                pass

    def scrape_detailed_wikipedia(self, site_name):
        """Get detailed description from Wikipedia article"""
        try:
            url = f"https://en.wikipedia.org/wiki/{site_name.replace(' ', '_')}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.find('div', id='mw-content-text')
            
            if content:
                paragraphs = []
                for p in content.find_all('p')[:3]:
                    text = p.get_text().strip()
                    if len(text) > 50:
                        paragraphs.append(text)
                
                if paragraphs:
                    return ' '.join(paragraphs)
        except:
            pass
        
        return None

    def save_comprehensive_dataset(self, filename):
        """Save comprehensive dataset to CSV"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        if not self.sites:
            print("No sites to save")
            return
        
        df = pd.DataFrame(self.sites)
        df = df.drop_duplicates(subset=['site_name'])
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\n{'='*70}")
        print(f"✅ Saved {len(df)} unique historical sites to:")
        print(f"   {filename}")
        print(f"{'='*70}")
        
        return df


# Pre-built comprehensive sites list (from research + tourism data)
COMPREHENSIVE_SRI_LANKA_SITES = """
Anuradhapura
Polonnaruwa
Sigiriya
Dambulla
Kandy
Galle
Adams Peak
Mihintale
Yapahuwa
Matara
Colombo
Jaffna
Trincomalee
Batticaloa
Kurunegala
Badulla
Nuwara Eliya
Peradeniya
Negombo
Beruwala
Mount Lavinia
Tissamaharama
Ridi
Mannar
Koneswaram Temple
Kelaniya Temple
Sri Dalada Maligawa
Brazen Palace
Lovamahapaya
Thuparama Vihara
Jetavana Monastery
Abhayagiriya
Rankot Vihara
Lankatilaka
Gadaladeniya Viharaya
Degaldoruwa Viharaya
Embekke Devale
Isurumuniya Vihara
Kuttam Pokuna
Polonnaruwa Quadrangle
Hatadage
Lankathilake Viharaya
Ruwanwella Maha Bodhi
Aluvihara Viharaya
Pothgul Vihara
Atadage
Shiva Devale
Parakrama Samudra
Panduwasnuwara
Kurunegala Rock Fortress
Yapahuwa Rock Temple
Trincomalee Fort
Matara Fort
Batticaloa Fort
Jaffna Fort
Kalutara Fort
Colombo Fort
Galle Fort Clock Tower
Galle Lighthouse
Galle Dutch Cemetery
Dondra Head Lighthouse
Dondra Temple
Unawatuna Beach
Beruwala Beach
Negombo Beach
Kosgoda Turtle Sanctuary
Minneriya Tank
Kaudulla Tank
Bundala National Park
Minneriya National Park
Yala National Park
Udawalawe National Park
Sinharaja Forest Reserve
Horton Plains National Park
Pidurutalagala
Peradeniya Botanical Gardens
Hakgala Botanical Gardens
National Museum Colombo
National Museum Kandy
Colombo National Museum
Colombo Fort Railway Station
Colombo General Post Office
Kandy Railway Station
Kandy Lake
Kandy Tower Hall
Kandy Prison
Nuwara Eliya Railway Station
Nuwara Eliya Post Office
Nuwara Eliya Grand Hotel
Kangaramula National Park
Sacred City of Kandy
Adam's Peak Pilgrimage Route
Colombo Japanese Peace Pagoda
Jami Ul Alfar Mosque
St Lucia's Cathedral
St Andrew's Church
Kelaniya Sanctuary
Ridi Viharaya
Kandy Temple Complex
Dalada Perahera Festival Site
Kandy Esala Perahera Route
Mihintale Sacred Mountain
Mihintale Stupa
Mihintale Monastery
Ancient City of Anuradhapura
Ancient City of Polonnaruwa
Sigiriya Rock Fortress
Sigiriya Palace
Sigiriya Frescoes
Dambulla Golden Temple
Dambulla Rock Temples
Rangiri Dambulla
Sri Pada Sanctuary
Ambuluwawa Mountain
Hakgala Sanctuary
Koneswaram Fort
Trincomalee Harbour
Trincomalee War Cemetery
Jaffna Archaeological Museum
Jaffna Library
Jaffna Temple
Nallur Kandasamy Temple
Mannar Island Fort
Mannar Bridge
Mannar Temple
Batticaloa Lagoon
Batticaloa Municipality
Nilaveli Beach
Nilaveli Temple
Arugambay Beach
Arugambe Lagoon
Colombo Old Parliament Building
Colombo City Hall
Colombo Fort Complex
Colombo Kotahena Church
Colombo Grand Oriental Hotel
Mount Lavinia Hotel
Peradeniya Bridge
Peradeniya Temple
Peradeniya University Historical Grounds
Badulla Colonial Town
Badulla Fort Ruins
Matara District Office
Matara Buddhist Temple
Matara Paravi Sandal Viharaya
Nuwara Eliya Colonial Heritage
Nuwara Eliya Golf Club
Nuwara Eliya Town Hall
Galle Fortifications Complex
Galle Old Town Heritage
Galle Historical Mosque
Beruwala Fisheries Harbour
Beruwala Temple
Negombo Fort Ruins
Negombo British Cemetery
Negombo Church
Anuradhapura Sacred Bodhi Tree
Polonnaruwa Gal Vihara
Sigiriya Water Gardens
Dambulla Sri Pada
Kandy Dalada Viharaya
Galle Fort Clock Tower Heritage
Adams Peak Sacred Footprint
Mihintale Dagoba Complex
Yapahuwa Rock Temple
Tissamaharama Rajamaha Viharaya
"""


def find_project_root():
    """Find the project root directory"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / 'data').exists() and (parent / 'scripts').exists():
            return parent
    return current


def main():
    import os
    
    print("\n" + "="*70)
    print("   COMPREHENSIVE SRI LANKA HISTORICAL SITES SCRAPER")
    print("="*70)
    
    project_root = find_project_root()
    print(f"\n📁 Project root: {project_root}")
    
    scraper = ComprehensiveSriLankaScraper()
    
    # Step 1: Query Wikidata
    wikidata_results = scraper.scrape_wikidata()
    if wikidata_results:
        scraper.scrape_from_wikidata_results(wikidata_results)
    
    time.sleep(1)
    
    # Step 2: Scrape Wikipedia categories
    scraper.scrape_wikipedia_index()
    
    time.sleep(1)
    
    # Step 3: Add comprehensive manual list
    print("\n📝 Adding comprehensive sites list...")
    for site in COMPREHENSIVE_SRI_LANKA_SITES.strip().split('\n'):
        site = site.strip()
        if site and site not in [s['site_name'] for s in scraper.sites]:
            scraper.sites.append({
                'site_name': site,
                'description': f"Historical site: {site}",
                'source': 'Comprehensive List',
                'url': f"https://en.wikipedia.org/wiki/{site.replace(' ', '_')}"
            })
    
    print(f"✓ Added {len(scraper.sites)} sites total")
    
    # Step 4: Enhance with Wikipedia descriptions
    print(f"\n📖 Fetching Wikipedia descriptions...")
    for i, site in enumerate(scraper.sites[:100], 1):  # Limit to first 100
        if i % 20 == 0:
            print(f"   Processed {i} sites...")
        
        description = scraper.scrape_detailed_wikipedia(site['site_name'])
        if description:
            site['description'] = description
        
        time.sleep(0.5)
    
    # Step 5: Save dataset
    output_file = project_root / "data" / "raw" / "comprehensive_historical_sites.csv"
    df = scraper.save_comprehensive_dataset(str(output_file))
    
    if df is not None:
        print(f"\n📊 DATASET SUMMARY:")
        print(f"   ├─ Total sites: {len(df)}")
        print(f"   ├─ Sources: {df['source'].unique().tolist()}")
        print(f"   ├─ With descriptions: {df['description'].notna().sum()}")
        print(f"   └─ Saved to: {output_file}")


if __name__ == "__main__":
    main()
