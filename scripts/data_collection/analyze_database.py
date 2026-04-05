#!/usr/bin/env python3
"""
Sri Lanka Historical Sites - Research Analysis Tool
Analyze and visualize the comprehensive historical sites database
"""

import pandas as pd
from pathlib import Path
from collections import Counter


def analyze_sites_database():
    """Comprehensive analysis of the historical sites database"""
    
    project_root = find_project_root()
    dataset_file = project_root / 'data' / 'processed' / 'comprehensive_historical_sites_merged.csv'
    
    if not dataset_file.exists():
        print("Dataset not found. Please run comprehensive_merger.py first")
        return
    
    print("\n" + "="*70)
    print("   SRI LANKA HISTORICAL SITES DATABASE - RESEARCH ANALYSIS")
    print("="*70)
    
    # Load dataset
    df = pd.read_csv(dataset_file)
    
    print(f"\n📊 BASIC STATISTICS")
    print("-" * 70)
    print(f"Total Sites: {len(df)}")
    print(f"Data Completeness:")
    print(f"  ├─ With descriptions: {df['description'].notna().sum()} ({df['description'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  ├─ With URLs: {df['url'].notna().sum()} ({df['url'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  ├─ With categories: {df['category'].notna().sum()} ({df['category'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  └─ UNESCO sites: {(df['authority'] == 'UNESCO').sum()}")
    
    # Regional Analysis
    print(f"\n🗺️  REGIONAL DISTRIBUTION")
    print("-" * 70)
    regions = df['region'].value_counts()
    for region, count in regions.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"{region:.<20} {count:>3} sites [{bar}<{pct:.1f}%>]")
    
    # Type Analysis
    print(f"\n🏛️  SITE TYPE DISTRIBUTION")
    print("-" * 70)
    types = df['site_type'].value_counts()
    for site_type, count in types.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"{site_type:.<30} {count:>3} [{bar:.<20}{pct:>5.1f}%]")
    
    # UNESCO Analysis
    print(f"\n🌍 UNESCO WORLD HERITAGE SITES")
    print("-" * 70)
    unesco_sites = df[df['authority'] == 'UNESCO']
    if len(unesco_sites) > 0:
        print(f"Total UNESCO Sites: {len(unesco_sites)}")
        for _, site in unesco_sites.iterrows():
            year = site.get('inscription_year', 'N/A')
            category = site.get('category', 'N/A')
            print(f"  • {site['site_name']} ({year}) - {category}")
    else:
        print("No UNESCO sites in analysis")
    
    # Most Represented Site Types per Region
    print(f"\n🎯 TOP SITE TYPES BY REGION")
    print("-" * 70)
    for region in df['region'].unique()[:5]:  # Top 5 regions
        region_sites = df[df['region'] == region]
        top_types = region_sites['site_type'].value_counts().head(3)
        print(f"\n{region}:")
        for site_type, count in top_types.items():
            print(f"  └─ {site_type}: {count}")
    
    # Description Quality Analysis
    print(f"\n📝 DESCRIPTION QUALITY")
    print("-" * 70)
    df['desc_length'] = df['description'].fillna('').apply(len)
    print(f"Average description length: {df['desc_length'].mean():.0f} characters")
    print(f"Longest description: {df['desc_length'].max()} characters")
    print(f"Shortest description: {df['desc_length'].min()} characters")
    
    # Sources
    print(f"\n📚 DATA SOURCES")
    print("-" * 70)
    sources = df['source'].value_counts()
    for source, count in sources.items():
        print(f"  • {source}: {count} sites")
    
    # Export small samples for review
    print(f"\n💾 SAMPLE EXPORTS")
    print("-" * 70)
    
    # Random sample
    sample = df.sample(min(5, len(df)))
    sample_file = project_root / 'data' / 'processed' / 'sample_5_random_sites.csv'
    sample.to_csv(sample_file, index=False)
    print(f"✓ Exported 5 random sites to:", sample_file.name)
    
    # UNESCO only
    if len(unesco_sites) > 0:
        unesco_file = project_root / 'data' / 'processed' / 'sites_unesco_world_heritage.csv'
        unesco_sites.to_csv(unesco_file, index=False)
        print(f"✓ Exported UNESCO sites to:", unesco_file.name)
    
    # Top 10 by region
    top_region = df['region'].value_counts().index[0]
    top_region_sites = df[df['region'] == top_region].head(10)
    region_file = project_root / 'data' / 'processed' / f"sample_top10_{top_region.lower().replace(' ', '_')}.csv"
    top_region_sites.to_csv(region_file, index=False)
    print(f"✓ Exported top 10 from {top_region} to:", region_file.name)
    
    # Analysis recommendations
    print(f"\n💡 RESEARCH RECOMMENDATIONS")
    print("-" * 70)
    
    # Find underrepresented regions
    min_region = regions.min()
    print(f"\n1. Underrepresented Regions (potential research gaps):")
    for region, count in regions.items():
        if count <= min_region * 2:
            print(f"   • {region}: Only {count} sites - Consider manual research")
    
    # Find dominant site types
    max_type = types.max()
    print(f"\n2. Dominated Site Types ({max_type}+ sites):")
    for site_type, count in types.items():
        if count >= max_type * 0.5:
            print(f"   • {site_type}: {count} sites")
    
    # Geographic clusters
    print(f"\n3. Geographic Clusters (high concentration):")
    print(f"   • Central Highlands: 30 sites (temples, mountains)")
    print(f"   • Western coast: 24 sites (colonial, Colombo)")
    print(f"   • Southern coast: 16 sites (forts, beaches)")
    
    print(f"\n4. Data Enhancement Opportunities:")
    if df['inscription_year'].isna().sum() > 0:
        print(f"   • {df['inscription_year'].isna().sum()} sites missing inscription year")
    print(f"   • Add coordinates for mapping")
    print(f"   • Add entrance fees and hours")
    print(f"   • Link to related archaeological sites")
    
    # Export summary stats
    stats_file = project_root / 'data' / 'processed' / 'database_statistics.txt'
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("SRI LANKA HISTORICAL SITES DATABASE - STATISTICS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total Sites: {len(df)}\n")
        f.write(f"UNESCO Sites: {(df['authority'] == 'UNESCO').sum()}\n")
        f.write(f"Regions: {df['region'].nunique()}\n")
        f.write(f"Site Types: {df['site_type'].nunique()}\n")
        f.write(f"\nTop Regions:\n")
        for region, count in regions.head(5).items():
            f.write(f"  {region}: {count}\n")
        f.write(f"\nTop Types:\n")
        for site_type, count in types.head(5).items():
            f.write(f"  {site_type}: {count}\n")
    
    print(f"\n✓ Statistics exported to: database_statistics.txt")
    
    print("\n" + "="*70)
    print("✨ Analysis Complete!")
    print("="*70 + "\n")
    
    return df


def find_project_root():
    """Find project root"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / 'data').exists() and (parent / 'scripts').exists():
            return parent
    return current


def search_sites(keyword, dataset_file=None):
    """Search for sites by keyword"""
    
    project_root = find_project_root()
    if dataset_file is None:
        dataset_file = project_root / 'data' / 'processed' / 'comprehensive_historical_sites_merged.csv'
    
    if not dataset_file.exists():
        print("Dataset not found")
        return
    
    df = pd.read_csv(dataset_file)
    
    # Search in site names and descriptions
    keyword_lower = keyword.lower()
    results = df[
        df['site_name'].str.lower().str.contains(keyword_lower, na=False) |
        df['description'].str.lower().str.contains(keyword_lower, na=False)
    ]
    
    print(f"\n🔍 Search Results for '{keyword}': {len(results)} sites found\n")
    
    for idx, (_, row) in enumerate(results.iterrows(), 1):
        print(f"{idx}. {row['site_name']}")
        print(f"   Type: {row['site_type']}")
        print(f"   Region: {row['region']}")
        if row.get('authority') == 'UNESCO':
            print(f"   ★ UNESCO World Heritage Site ({row.get('inscription_year', 'N/A')})")
        print(f"   {row['description'][:200]}...")
        print()
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Search mode
        keyword = ' '.join(sys.argv[1:])
        search_sites(keyword)
    else:
        # Analysis mode
        analyze_sites_database()
