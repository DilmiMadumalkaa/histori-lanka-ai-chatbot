#!/usr/bin/env python3
"""
RAG-Ready Historical Sites Dataset Creator
Uses existing comprehensive dataset and enriches with archaeological data
"""

import pandas as pd
import os
from pathlib import Path


def enhance_with_archaeological_data():
    """Enhance existing dataset with archaeological and tourism information"""
    
    print("\n" + "="*70)
    print("   RAG-READY HISTORICAL SITES DATASET CREATOR")
    print("   Enhancing with Archaeological & Tourism Data")
    print("="*70)
    
    # Load existing comprehensive dataset
    input_file = Path("data/processed/comprehensive_historical_sites_merged.csv")
    
    if not input_file.exists():
        print(f"\n❌ Input file not found: {input_file}")
        return
    
    print(f"\n📂 Loading existing dataset...")
    df = pd.read_csv(input_file)
    print(f"   Loaded {len(df)} sites")
    
    # Archaeological information for major sites
    archaeological_enhancements = {
        "Anuradhapura": {
            "archaeological_significance": "UNESCO World Heritage Site. Ancient capital (4th century BCE - 10th century CE). Contains Jaya Sri Maha Bodhi, Thuparama Vihara, Abhayagiriya, Jetavana Monastery. Extensive archaeological remains of ancient Buddhist civilization.",
            "historical_period": "Ancient Kingdom",
            "region_specific": "North Central Province"
        },
        "Polonnaruwa": {
            "archaeological_significance": "UNESCO World Heritage Site. Medieval capital (11th-13th century CE). Features Gal Vihara, Vatadage, Quadrangle complex, royal palace ruins. UNESCO inscription: 1982. Important medieval Sinhalese architecture.",
            "historical_period": "Medieval Kingdom",
            "region_specific": "North Central Province"
        },
        "Sigiriya": {
            "archaeological_significance": "UNESCO World Heritage Site. Ancient rock fortress (5th century CE, King Kashyapa). UNESCO inscription: 1982. Contains palace remains, frescoes, water gardens. Architectural marvel of ancient engineering.",
            "historical_period": "Ancient Kingdom",
            "region_specific": "Central Province"
        },
        "Dambulla": {
            "archaeological_significance": "UNESCO World Heritage Site. Golden temple complex with five cave temples (1st century BCE onwards). UNESCO inscription: 1991. Contains 153 Buddha statues, extensive murals, religious inscriptions. Largest cave temple in Sri Lanka.",
            "historical_period": "Ancient Kingdom",
            "region_specific": "Central Province"
        },
        "Kandy": {
            "archaeological_significance": "UNESCO World Heritage Site (Sacred City). Medieval capital (14th century onwards). Center of Buddhist pilgrimage. Contains Sri Dalada Maligawa (Temple of Sacred Tooth Relic), royal palace, Kandy Lake. UNESCO inscription: 1988.",
            "historical_period": "Medieval Kingdom",
            "region_specific": "Central Province"
        },
        "Galle Fort": {
            "archaeological_significance": "UNESCO World Heritage Site. Historic fortified city (Portuguese 1588, Dutch 1649 onwards, British). Well-preserved colonial ramparts, lighthouse, heritage structures. Important maritime colonial heritage. UNESCO inscription: 1988.",
            "historical_period": "Colonial Period",
            "region_specific": "Southern Province"
        },
        "Jaffna Fort": {
            "archaeological_significance": "Star fort built by Portuguese (1588), extended by Dutch and British. Contains colonial military installations and engineering. Important northern maritime colonial heritage.",
            "historical_period": "Colonial Period",
            "region_specific": "Northern Province"
        },
        "Matara Fort": {
            "archaeological_significance": "Dutch star fort (1763). Colonial military architecture on southern coast. Contains historical structures representing Dutch colonial engineering and administration.",
            "historical_period": "Colonial Period",
            "region_specific": "Southern Province"
        },
        "Colombo Fort": {
            "archaeological_significance": "Historic fortified area. Portuguese, Dutch, British colonial periods. Contains railway station (1881), Old Parliament, historical fort walls. Important urban heritage complex of colonial Colombo.",
            "historical_period": "Colonial Period",
            "region_specific": "Western Province"
        },
        "Mihintale": {
            "archaeological_significance": "Sacred mountain and ancient monastery (3rd century BCE). Important pilgrimage site where Buddhism was introduced by Mahinda (son of Emperor Ashoka). Ancient stairs, dagobas, meditation caves, ancient inscriptions.",
            "historical_period": "Ancient Kingdom",
            "region_specific": "North Central Province"
        },
        "Yapahuwa": {
            "archaeological_significance": "Ancient rock fortress (13th century CE). Contains ancient monastery remains, stone sculptures, palace ruins. Important medieval Sinhalese architectural site.",
            "historical_period": "Medieval Kingdom",
            "region_specific": "North Western Province"
        },
        "Sinharaja Forest Reserve": {
            "archaeological_significance": "UNESCO World Heritage Site. Rainforest with ancient ecological heritage (World Heritage 1988). Contains indigenous and historical forest use patterns. Biodiversity and cultural heritage site.",
            "historical_period": "Ancient",
            "region_specific": "Southern & Sabaragamuwa Province"
        },
        "Adams Peak": {
            "archaeological_significance": "Sacred mountain (2,243m) with ancient temple and footprint shrine. Multi-faith pilgrimage site (Buddhist, Hindu, Islamic, Christian traditions). Ancient pilgrimage routes and religious heritage.",
            "historical_period": "Ancient",
            "region_specific": "Central & Sabaragamuwa Province"
        }
    }
    
    # Add archaeological information
    print(f"\n🏛️  Adding archaeological data...")
    df['archaeological_significance'] = ''
    df['historical_period'] = 'General Historical'
    df['region_specific'] = ''
    df['unesco_status'] = ''
    
    unesco_sites = ['Anuradhapura', 'Polonnaruwa', 'Sigiriya', 'Dambulla', 'Kandy', 
                    'Galle Fort', 'Sinharaja', 'Sacred City']
    
    enhanced_count = 0
    for idx, row in df.iterrows():
        site_name = row['site_name']
        
        # Check if site is in archaeological enhancements
        for arch_site, arch_info in archaeological_enhancements.items():
            if arch_site.lower() in site_name.lower():
                df.at[idx, 'archaeological_significance'] = arch_info['archaeological_significance']
                df.at[idx, 'historical_period'] = arch_info['historical_period']
                df.at[idx, 'region_specific'] = arch_info['region_specific']
                enhanced_count += 1
                break
        
        # Mark UNESCO sites
        if any(unesco in site_name for unesco in unesco_sites):
            df.at[idx, 'unesco_status'] = 'UNESCO World Heritage Site'
        else:
            df.at[idx, 'unesco_status'] = 'Other'
    
    print(f"   Enhanced {enhanced_count} sites with archaeological data")
    
    # Prepare for RAG optimization
    print(f"\n✨ Optimizing for RAG system...")
    
    # Ensure all essential columns exist
    if 'description' not in df.columns:
        df['description'] = df.get('site_name', 'Unknown')
    
    if 'url' not in df.columns:
        df['url'] = ''
    
    # Create RAG-optimized columns
    df['rag_content'] = df.apply(
        lambda row: f"Site: {row['site_name']}\n\n{row['description']}\n\nArchaeological Significance: {row['archaeological_significance']}\n\nHistorical Period: {row['historical_period']}",
        axis=1
    )
    
    # Select final columns in logical order
    final_columns = [
        'site_name',
        'description',
        'archaeological_significance', 
        'historical_period',
        'region_specific',
        'unesco_status',
        'url',
        'rag_content'
    ]
    
    # Add other existing useful columns
    for col in df.columns:
        if col not in final_columns and col not in ['rag_content']:
            if col not in ['site_type', 'region']:  # Exclude duplicates
                final_columns.append(col)
    
    # Keep only available columns
    available_columns = [col for col in final_columns if col in df.columns]
    df_final = df[available_columns].copy()
    
    # Remove duplicates by site name
    df_final = df_final.drop_duplicates(subset=['site_name']).reset_index(drop=True)
    
    # Sort by name
    df_final = df_final.sort_values('site_name').reset_index(drop=True)
    
    # Save final RAG dataset
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "historical_sites_rag_ready.csv"
    df_final.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ Saved RAG-ready dataset:")
    print(f"   📁 {output_file}")
    print(f"   📊 {len(df_final)} sites")
    
    # Print statistics
    print("\n" + "="*70)
    print("📊 RAG DATASET STATISTICS")
    print("="*70)
    
    print(f"\n✓ Total sites: {len(df_final)}")
    print(f"✓ UNESCO sites: {(df_final['unesco_status'] == 'UNESCO World Heritage Site').sum()}")
    print(f"✓ With descriptions: {(df_final['description'].notna() & (df_final['description'] != '')).sum()}")
    print(f"✓ With archaeological info: {(df_final['archaeological_significance'] != '').sum()}")
    
    if 'region' in df_final.columns:
        print(f"\n🗺️  Regional Coverage:")
        regions = df_final['region'].value_counts()
        for region, count in regions.head(5).items():
            print(f"   • {region}: {count} sites")
    
    if 'site_type' in df_final.columns:
        print(f"\n🏛️  Site Types:")
        types = df_final['site_type'].value_counts()
        for site_type, count in types.head(5).items():
            print(f"   • {site_type}: {count} sites")
    
    print(f"\n📝 Content Quality:")
    desc_lengths = df_final['description'].astype(str).str.len()
    print(f"   • Average description length: {desc_lengths.mean():.0f} characters")
    print(f"   • Longest: {desc_lengths.max()} characters")
    print(f"   • Shortest: {desc_lengths.min()} characters")
    
    print(f"\n🎯 Data Sources Included:")
    if 'source' in df_final.columns:
        sources = df_final['source'].value_counts()
        for source, count in sources.items():
            print(f"   • {source}: {count} sites")
    
    print(f"\n✨ READY FOR RAG CHATBOT IMPLEMENTATION")
    print("="*70 + "\n")
    
    return df_final


def cleanup_unnecessary_files():
    """Remove unnecessary filtered dataset files"""
    
    print("\n🧹 CLEANING UP UNNECESSARY FILES...")
    
    processed_dir = Path("data/processed")
    
    # Files to remove (filtered datasets created by analyze_database.py)
    unnecessary_patterns = [
        "sites_buddhist_temple.csv",
        "sites_central_highlands.csv",
        "sites_archaeological.csv",
        "sites_fort_fortress.csv",
        "sites_natural_sacred.csv",
        "sites_colonial_heritage.csv",
        "sites_museum.csv",
        "sites_north_central.csv",
        "sites_north.csv",
        "sites_east.csv",
        "sites_south.csv",
        "sites_uva.csv",
        "sites_west.csv",
        "sites_unesco_world_heritage.csv",
        "sites_other_religious.csv",
        "sites_other.csv",
        "sites_ancient_",
        "sites_buddhist_temples_in_sri_lanka.csv",
        "sites_hindu_temples_in_sri_lanka.csv",
        "sites_mosques_in_sri_lanka.csv",
        "sites_national_parks_of_sri_lanka.csv",
        "sample_5_random_sites.csv",
        "sample_top10_other.csv",
        "sites_other.csv"
    ]
    
    removed_count = 0
    if processed_dir.exists():
        for file in processed_dir.glob("*.csv"):
            filename = file.name
            
            # Check if file matches unnecessary patterns
            should_remove = False
            for pattern in unnecessary_patterns:
                if pattern in filename or filename.startswith("sites_"):
                    should_remove = True
                    break
            
            # Keep the main datasets
            if filename in ["comprehensive_historical_sites_merged.csv", 
                           "historical_sites_rag_ready.csv"]:
                should_remove = False
            
            if should_remove:
                try:
                    file.unlink()
                    print(f"   ✓ Removed: {filename}")
                    removed_count += 1
                except Exception as e:
                    print(f"   ✗ Failed to remove {filename}: {str(e)[:50]}")
    
    print(f"\n✅ Cleanup complete: Removed {removed_count} unnecessary files")


def main():
    """Main execution"""
    
    # Create RAG dataset
    df_final = enhance_with_archaeological_data()
    
    # Cleanup unnecessary files
    cleanup_unnecessary_files()
    
    print("\n📋 FILES KEPT IN /data/processed/:")
    processed_dir = Path("data/processed")
    csv_files = list(processed_dir.glob("*.csv"))
    for f in sorted(csv_files):
        size_kb = f.stat().st_size / 1024
        print(f"   • {f.name} ({size_kb:.1f} KB)")
    
    print("\n" + "="*70)
    print("🎉 RAG DATASET CREATION & CLEANUP COMPLETE!")
    print("="*70)
    print("\n📊 Final Output:")
    print("   ✓ PRIMARY: historical_sites_rag_ready.csv - RAG-optimized dataset")
    print("   ✓ ARCHIVE: comprehensive_historical_sites_merged.csv - Full source data")
    print("\n🚀 Ready for RAG chatbot implementation!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
