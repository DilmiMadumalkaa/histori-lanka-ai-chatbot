#!/usr/bin/env python3
"""
Comprehensive Dataset Merger
Combines all data sources into one research-ready dataset for Sri Lanka historical sites
"""

import pandas as pd
import os
from pathlib import Path


class ComprehensiveDatasetMerger:
    """Merge all historical sites data sources"""
    
    def __init__(self):
        self.sources = {}
        self.merged_df = None
    
    def load_all_sources(self, data_dir):
        """Load all available CSV sources"""
        csv_files = {
            'wikipedia': data_dir / 'wikipedia_sites.csv',
            'tourism': data_dir / 'tourism_board_sites.csv',
            'unesco': data_dir / 'unesco_sites.csv',
            'comprehensive': data_dir / 'comprehensive_historical_sites.csv'
        }
        
        for source_name, filepath in csv_files.items():
            try:
                if filepath.exists():
                    df = pd.read_csv(filepath)
                    self.sources[source_name] = df
                    print(f"✓ Loaded {source_name}: {len(df)} sites")
                else:
                    print(f"✗ {source_name} not found: {filepath}")
            except Exception as e:
                print(f"✗ Error loading {source_name}: {e}")
    
    def merge_all_sources(self):
        """intelligently merge all data sources"""
        if not self.sources:
            print("No sources loaded")
            return None
        
        # Start with comprehensive as base (most sites)
        if 'comprehensive' in self.sources:
            merged = self.sources['comprehensive'].copy()
            print(f"\n📊 Starting with comprehensive source: {len(merged)} sites")
        else:
            # Fallback to first available source
            merged = None
            for source_df in self.sources.values():
                merged = source_df.copy()
                break
        
        # Ensure all data is string type to avoid type conflicts
        merged = merged.astype(str).replace('nan', '')
        
        # Add missing columns if needed
        required_columns = [
            'site_name', 'description', 'url', 'source',
            'location', 'category', 'inscription_year', 'authority'
        ]
        for col in required_columns:
            if col not in merged.columns:
                merged[col] = ''
        
        # Merge UNESCO data for heritage status
        if 'unesco' in self.sources:
            unesco_df = self.sources['unesco'].copy()
            unesco_df = unesco_df.astype(str).replace('nan', '')
            print(f"Merging UNESCO data: {len(unesco_df)} World Heritage Sites")
            
            # Match UNESCO sites by name similarity
            for idx, row in merged.iterrows():
                site_name = str(row['site_name']).lower()
                
                # Look for UNESCO match
                for _, unesco_row in unesco_df.iterrows():
                    unesco_name = str(unesco_row['site_name']).lower()
                    
                    # Simple string matching
                    if unesco_name in site_name or site_name in unesco_name:
                        if not merged.at[idx, 'category'] or merged.at[idx, 'category'] == '':
                            merged.at[idx, 'category'] = str(unesco_row.get('category', 'Cultural'))
                        if not merged.at[idx, 'inscription_year'] or merged.at[idx, 'inscription_year'] == '':
                            merged.at[idx, 'inscription_year'] = str(unesco_row.get('inscription_year', ''))
                        if not merged.at[idx, 'authority'] or merged.at[idx, 'authority'] == '':
                            merged.at[idx, 'authority'] = 'UNESCO'
                        break
        
        # Merge Wikipedia data for better descriptions
        if 'wikipedia' in self.sources:
            wiki_df = self.sources['wikipedia'].copy()
            wiki_df = wiki_df.astype(str).replace('nan', '')
            print(f"Enhancing with Wikipedia data: {len(wiki_df)} sites")
            
            for idx, row in merged.iterrows():
                site_name = str(row['site_name']).lower()
                
                # Look for Wikipedia match
                for _, wiki_row in wiki_df.iterrows():
                    wiki_name = str(wiki_row['site_name']).lower()
                    
                    if wiki_name == site_name or wiki_name in site_name or site_name in wiki_name:
                        # Use Wikipedia description if available and better
                        wiki_desc = str(wiki_row.get('description', ''))
                        if wiki_desc and len(wiki_desc) > len(str(row['description'])):
                            merged.at[idx, 'description'] = wiki_desc
                        if not merged.at[idx, 'url'] or merged.at[idx, 'url'] == '':
                            merged.at[idx, 'url'] = str(wiki_row.get('url', ''))
                        break
        
        # Remove duplicates
        merged = merged.drop_duplicates(subset=['site_name'])
        
        # Clean up - keep only required columns
        for col in required_columns:
            if col not in merged.columns:
                merged[col] = ''
        
        merged = merged[required_columns].copy()
        merged = merged[merged['site_name'].notna() & (merged['site_name'] != '') & (merged['site_name'] != 'nan')]
        
        self.merged_df = merged
        return merged
    
    def add_metadata(self):
        """Add additional metadata for research"""
        if self.merged_df is None:
            return
        
        print("\n📝 Adding research metadata...")
        
        # Categorize by type
        def categorize_site(name, category, description):
            name_lower = str(name).lower()
            desc_lower = str(description).lower() if description else ""
            
            if any(term in name_lower or term in desc_lower for term in ['temple', 'viharaya', 'dagoba', 'stupa']):
                return 'Buddhist Temple'
            elif any(term in name_lower or term in desc_lower for term in ['fort', 'fortress']):
                return 'Fort/Fortress'
            elif any(term in name_lower or term in desc_lower for term in ['ancient', 'ruins', 'archaeological']):
                return 'Archaeological'
            elif any(term in name_lower or term in desc_lower for term in ['museum', 'gallery']):
                return 'Museum'
            elif any(term in name_lower or term in desc_lower for term in ['peak', 'mountain', 'sanctuary']):
                return 'Natural/Sacred'
            elif any(term in name_lower or term in desc_lower for term in ['mosque', 'church', 'cathedral']):
                return 'Other Religious'
            elif any(term in name_lower or term in desc_lower for term in ['palace', 'hotel', 'building']):
                return 'Colonial/Heritage'
            else:
                return category if category else 'Historical Site'
        
        self.merged_df['site_type'] = self.merged_df.apply(
            lambda row: categorize_site(row['site_name'], row.get('category', ''), 
                                       row.get('description', '')),
            axis=1
        )
        
        # Add region mapping
        region_keywords = {
            'Central Highlands': ['kandy', 'dambulla', 'peradeniya', 'nuwara eliya', 'badulla'],
            'North Central': ['anuradhapura', 'polonnaruwa', 'kurunegala', 'yapahuwa', 'panduwasnuwara'],
            'South': ['galle', 'matara', 'unawatuna', 'dondra', 'mirissa'],
            'West': ['colombo', 'negombo', 'mount lavinia', 'beruwala', 'kalutara'],
            'North': ['jaffna', 'mannar', 'mullaitivu'],
            'East': ['trincomalee', 'batticaloa'],
            'Uva': ['badulla', 'tissamaharama']
        }
        
        def get_region(name):
            name_lower = str(name).lower()
            for region, keywords in region_keywords.items():
                for keyword in keywords:
                    if keyword in name_lower:
                        return region
            return 'Other'
        
        self.merged_df['region'] = self.merged_df['site_name'].apply(get_region)
        
        print("✓ Added site_type and region columns")
    
    def get_statistics(self):
        """Generate dataset statistics for research"""
        if self.merged_df is None:
            return {}
        
        stats = {
            'total_sites': len(self.merged_df),
            'sites_by_type': self.merged_df['site_type'].value_counts().to_dict(),
            'sites_by_region': self.merged_df['region'].value_counts().to_dict(),
            'with_description': self.merged_df['description'].notna().sum(),
            'with_url': self.merged_df['url'].notna().sum(),
            'unicode_sites': (self.merged_df['authority'] == 'UNESCO').sum(),
            'sources': self.merged_df['source'].unique().tolist()
        }
        
        return stats
    
    def save_datasets(self, output_dir):
        """Save multiple output formats"""
        if self.merged_df is None:
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Main dataset
        main_file = output_dir / 'comprehensive_historical_sites_merged.csv'
        self.merged_df.to_csv(main_file, index=False, encoding='utf-8')
        print(f"\n✓ Saved main dataset: {main_file}")
        
        # By type
        for site_type in self.merged_df['site_type'].unique():
            if pd.notna(site_type):
                subset = self.merged_df[self.merged_df['site_type'] == site_type]
                filename = output_dir / f"sites_{site_type.lower().replace('/', '_')}.csv"
                subset.to_csv(filename, index=False, encoding='utf-8')
        
        # By region
        for region in self.merged_df['region'].unique():
            if pd.notna(region):
                subset = self.merged_df[self.merged_df['region'] == region]
                filename = output_dir / f"sites_{region.lower().replace(' ', '_')}.csv"
                subset.to_csv(filename, index=False, encoding='utf-8')
        
        # UNESCO only
        unesco_subset = self.merged_df[self.merged_df['authority'] == 'UNESCO']
        if len(unesco_subset) > 0:
            unesco_file = output_dir / 'sites_unesco_world_heritage.csv'
            unesco_subset.to_csv(unesco_file, index=False, encoding='utf-8')
        
        print("✓ Saved filtered datasets by type and region")


def find_project_root():
    """Find project root"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / 'data').exists() and (parent / 'scripts').exists():
            return parent
    return current


def main():
    print("\n" + "="*70)
    print("   COMPREHENSIVE HISTORICAL SITES DATASET MERGER")
    print("="*70)
    
    project_root = find_project_root()
    data_dir = project_root / 'data' / 'raw'
    output_dir = project_root / 'data' / 'processed'
    
    print(f"\n📁 Project root: {project_root}")
    print(f"📂 Data directory: {data_dir}")
    
    merger = ComprehensiveDatasetMerger()
    
    # Load all sources
    print("\n🔄 Loading all data sources...")
    merger.load_all_sources(data_dir)
    
    # Merge
    print("\n🔗 Merging data sources...")
    merged_df = merger.merge_all_sources()
    
    if merged_df is None:
        print("No data to merge")
        return
    
    # Add metadata
    merger.add_metadata()
    
    # Get statistics
    stats = merger.get_statistics()
    
    # Save
    print("\n💾 Saving comprehensive datasets...")
    merger.save_datasets(output_dir)
    
    # Print statistics
    print("\n" + "="*70)
    print("📊 RESEARCH DATASET STATISTICS")
    print("="*70)
    print(f"\n✅ Total unique sites: {stats['total_sites']}")
    print(f"✓ With descriptions: {stats['with_description']}")
    print(f"✓ With URLs: {stats['with_url']}")
    print(f"✓ UNESCO World Heritage Sites: {stats['unicode_sites']}")
    
    print(f"\n📍 Sites by Region:")
    for region, count in sorted(stats['sites_by_region'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {region}: {count}")
    
    print(f"\n🏛️  Sites by Type:")
    for site_type, count in sorted(stats['sites_by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {site_type}: {count}")
    
    print(f"\n📚 Data Sources:")
    for source in stats['sources']:
        print(f"   • {source}")
    
    print("\n" + "="*70)
    print(f"✨ READY FOR RESEARCH!")
    print(f"Main dataset: data/processed/comprehensive_historical_sites_merged.csv")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
