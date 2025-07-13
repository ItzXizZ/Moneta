#!/usr/bin/env python3
"""
Simple script to check current scores and save them to JSON
"""

import requests
import json

def check_current_scores():
    """Check current scores from the live update endpoint"""
    try:
        response = requests.get('http://localhost:5000/score-updates')
        if response.status_code == 200:
            data = response.json()
            print("📊 Current Live Scores:")
            print("=" * 50)
            
            # Sort by score
            updates = sorted(data['updates'], key=lambda x: x['score'], reverse=True)
            
            for i, update in enumerate(updates, 1):
                print(f"{i:2d}. {update['content'][:50]}...")
                print(f"     Score: {update['score']:.2f}")
                print()
            
            print(f"📈 Total memories: {len(updates)}")
            print(f"🕒 Last update: {data.get('timestamp', 'Unknown')}")
            
            return data['updates']
        else:
            print(f"❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_scores_to_json():
    """Save current scores to JSON file"""
    try:
        response = requests.post('http://localhost:5000/save-scores')
        if response.status_code == 200:
            data = response.json()
            print("✅ " + data['message'])
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def compare_with_json():
    """Compare live scores with what's in the JSON file"""
    try:
        # Get live scores
        live_response = requests.get('http://localhost:5000/score-updates')
        if live_response.status_code != 200:
            print("❌ Could not get live scores")
            return
        
        # Get JSON scores
        json_response = requests.get('http://localhost:5000/memories')
        if json_response.status_code != 200:
            print("❌ Could not get JSON scores")
            return
        
        live_data = live_response.json()
        json_data = json_response.json()
        
        live_scores = {update['id']: update['score'] for update in live_data['updates']}
        json_scores = {mem['id']: mem.get('score', 0) for mem in json_data.get('memories', [])}
        
        print("🔍 Comparing Live Scores vs JSON Scores:")
        print("=" * 60)
        
        all_ids = set(live_scores.keys()) | set(json_scores.keys())
        differences = []
        
        for mem_id in all_ids:
            live_score = live_scores.get(mem_id, 0)
            json_score = json_scores.get(mem_id, 0)
            
            if abs(live_score - json_score) > 0.01:
                differences.append((mem_id, live_score, json_score))
                print(f"⚠️  {mem_id}: Live={live_score:.2f}, JSON={json_score:.2f}")
            else:
                print(f"✅ {mem_id}: Live={live_score:.2f}, JSON={json_score:.2f}")
        
        if differences:
            print(f"\n📊 Found {len(differences)} differences")
            print("💡 Use 'save_scores_to_json()' to sync them")
        else:
            print("\n🎉 All scores are in sync!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 MemoryOS Score Checker")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Check current live scores")
        print("2. Save scores to JSON")
        print("3. Compare live vs JSON scores")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            check_current_scores()
        elif choice == '2':
            save_scores_to_json()
        elif choice == '3':
            compare_with_json()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice") 