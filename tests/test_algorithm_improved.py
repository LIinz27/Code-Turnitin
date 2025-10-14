#!/usr/bin/env python3
"""
Algorithm Improvement Testing for Code Turnitin

This script tests the improved algorithm by:
1. Running same test cases as before 
2. Comparing results with baseline
3. Measuring performance improvements
4. Generating AFTER report

Author: Created for Code Turnitin thesis presentation  
Date: October 2025
"""

import sys
import os
import time
import json
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import demo similarity analyzer
from demo.demo_similarity import get_demo_analyzer
from demo.demo_handler import get_demo_handler, initialize_demo

def load_baseline_results():
    """Load the baseline test results"""
    reports_dir = Path("tests/reports")
    baseline_files = list(reports_dir.glob("algorithm_consistency_before_*.json"))
    
    if not baseline_files:
        print("❌ No baseline results found. Run test_algorithm_consistency.py first.")
        return None
        
    # Get the most recent baseline file
    baseline_file = max(baseline_files, key=lambda f: f.stat().st_mtime)
    
    with open(baseline_file, 'r') as f:
        baseline_data = json.load(f)
    
    print(f"📋 Loaded baseline from: {baseline_file.name}")
    return baseline_data

def run_improved_algorithm_test():
    """Run the same test cases with improved algorithm"""
    print("🔧 Testing Improved Algorithm")
    print("=" * 60)
    
    # Initialize demo system
    print("🔧 Initializing demo system...")
    success, issues = initialize_demo()
    if not success:
        print(f"❌ Failed to initialize demo system: {issues}")
        return None
        
    demo_analyzer = get_demo_analyzer()
    demo_handler = get_demo_handler()
    print("✅ Demo system initialized successfully")
    
    # Get same test repositories as baseline
    test_repos = []
    
    # Get Java repositories
    java_repos = demo_handler.get_repositories_by_language('Java')
    if java_repos:
        test_repos.extend(java_repos[:2])
        
    # Get JavaScript repositories  
    js_repos = demo_handler.get_repositories_by_language('JavaScript')
    if js_repos:
        test_repos.extend(js_repos[:2])
        
    # Get Python repositories
    python_repos = demo_handler.get_repositories_by_language('Python')
    if python_repos:
        test_repos.extend(python_repos[:1])
    
    test_repos = test_repos[:5]  # Same as baseline
    
    # Generate same test pairs
    test_cases = []
    repo_count = len(test_repos)
    
    for i in range(8):  # Same number as baseline
        repo1_idx = i % repo_count
        repo2_idx = (i + 1) % repo_count
        if repo1_idx != repo2_idx:
            test_cases.append((test_repos[repo1_idx], test_repos[repo2_idx]))
    
    print(f"📝 Running {len(test_cases)} test cases (same as baseline)")
    print("=" * 60)
    
    # Run tests with improved algorithm
    results = []
    for idx, (repo1, repo2) in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {idx}/{len(test_cases)}")
        print(f"🔄 Testing: {repo1.get('name')[:30]}... vs {repo2.get('name')[:30]}...")
        
        # Run multiple times to check consistency
        run_results = []
        for run in range(5):
            print(f"   Run {run + 1}/5...", end=" ")
            
            try:
                start_time = time.time()
                comparison_result = demo_analyzer.compare_repositories(
                    source_repo=repo1,
                    target_repo=repo2,
                    algorithm='jaccard'
                )
                processing_time = time.time() - start_time
                
                similarity_score = comparison_result.get('similarity_score', 0.0)
                
                run_results.append({
                    'run': run + 1,
                    'similarity_score': similarity_score,
                    'processing_time': processing_time
                })
                
                print(f"Score: {similarity_score:.4f}")
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                run_results.append({
                    'run': run + 1,
                    'error': str(e)
                })
        
        # Analyze consistency for this test case
        valid_scores = [r['similarity_score'] for r in run_results if 'similarity_score' in r]
        
        if valid_scores:
            min_score = min(valid_scores)
            max_score = max(valid_scores)
            avg_score = sum(valid_scores) / len(valid_scores)
            score_variance = max_score - min_score
            
            test_result = {
                'repo1': {'id': repo1.get('id'), 'name': repo1.get('name'), 'language': repo1.get('language')},
                'repo2': {'id': repo2.get('id'), 'name': repo2.get('name'), 'language': repo2.get('language')},
                'run_results': run_results,
                'analysis': {
                    'min_score': min_score,
                    'max_score': max_score,
                    'average_score': avg_score,
                    'score_variance': score_variance,
                    'is_consistent': score_variance < 0.001,
                    'consistency_level': 'GOOD' if score_variance < 0.001 else ('MEDIUM' if score_variance < 0.01 else 'POOR')
                }
            }
            
            print(f"   📊 Results: Min={min_score:.4f}, Max={max_score:.4f}, Variance={score_variance:.4f}")
            print(f"   🎯 Consistency: {test_result['analysis']['consistency_level']}")
        else:
            test_result = {
                'repo1': {'id': repo1.get('id'), 'name': repo1.get('name')},
                'repo2': {'id': repo2.get('id'), 'name': repo2.get('name')},
                'error': 'All runs failed',
                'run_results': run_results
            }
            print("   ❌ All runs failed!")
        
        results.append(test_result)
    
    return results

def compare_with_baseline(improved_results, baseline_data):
    """Compare improved results with baseline"""
    print("\n" + "=" * 60)
    print("📊 ALGORITHM IMPROVEMENT COMPARISON")
    print("=" * 60)
    
    baseline_results = baseline_data.get('detailed_results', [])
    
    if len(improved_results) != len(baseline_results):
        print(f"⚠️  Warning: Different number of test cases (improved: {len(improved_results)}, baseline: {len(baseline_results)})")
        return
    
    improvements = []
    consistency_comparison = {'improved': 0, 'same': 0, 'degraded': 0}
    accuracy_changes = []
    
    for i, (improved, baseline) in enumerate(zip(improved_results, baseline_results)):
        print(f"\n🧪 Test Case {i+1}:")
        
        if 'analysis' not in improved or 'analysis' not in baseline:
            print("   ❌ Incomplete data, skipping comparison")
            continue
            
        # Compare consistency
        improved_consistency = improved['analysis']['consistency_level']
        baseline_consistency = baseline['analysis']['consistency_level']
        
        print(f"   📊 Consistency: {baseline_consistency} → {improved_consistency}")
        
        if improved_consistency == baseline_consistency:
            consistency_comparison['same'] += 1
        elif (improved_consistency == 'GOOD' and baseline_consistency != 'GOOD') or \
             (improved_consistency == 'MEDIUM' and baseline_consistency == 'POOR'):
            consistency_comparison['improved'] += 1
            print("   ✅ Consistency improved!")
        else:
            consistency_comparison['degraded'] += 1
            print("   ❌ Consistency degraded!")
        
        # Compare average similarity scores
        improved_score = improved['analysis']['average_score']
        baseline_score = baseline['analysis']['average_score']
        score_change = improved_score - baseline_score
        
        print(f"   🎯 Average Score: {baseline_score:.4f} → {improved_score:.4f} (Δ{score_change:+.4f})")
        
        accuracy_changes.append({
            'test_case': i + 1,
            'baseline_score': baseline_score,
            'improved_score': improved_score,
            'score_change': score_change,
            'repo1': improved['repo1']['name'][:30],
            'repo2': improved['repo2']['name'][:30]
        })
    
    # Overall summary
    print(f"\n🎯 OVERALL IMPROVEMENT SUMMARY:")
    print(f"Consistency Improvements: {consistency_comparison['improved']}")
    print(f"Consistency Same: {consistency_comparison['same']}")
    print(f"Consistency Degraded: {consistency_comparison['degraded']}")
    
    if accuracy_changes:
        avg_score_change = sum(ac['score_change'] for ac in accuracy_changes) / len(accuracy_changes)
        max_improvement = max(accuracy_changes, key=lambda x: x['score_change'])
        max_degradation = min(accuracy_changes, key=lambda x: x['score_change'])
        
        print(f"\n📈 ACCURACY CHANGES:")
        print(f"Average Score Change: {avg_score_change:+.4f}")
        print(f"Best Improvement: {max_improvement['score_change']:+.4f} (Case {max_improvement['test_case']})")
        print(f"Worst Change: {max_degradation['score_change']:+.4f} (Case {max_degradation['test_case']})")
        
        # Determine overall improvement
        if consistency_comparison['improved'] > consistency_comparison['degraded']:
            overall_status = "🟢 IMPROVED"
        elif consistency_comparison['improved'] == consistency_comparison['degraded']:
            if avg_score_change > 0.01:
                overall_status = "🟡 SLIGHTLY IMPROVED"
            elif avg_score_change < -0.01:
                overall_status = "🟠 SLIGHTLY DEGRADED"
            else:
                overall_status = "🔵 NO SIGNIFICANT CHANGE"
        else:
            overall_status = "🔴 DEGRADED"
        
        print(f"\n🎯 Overall Algorithm Status: {overall_status}")
    
    return {
        'consistency_comparison': consistency_comparison,
        'accuracy_changes': accuracy_changes,
        'overall_status': overall_status if 'overall_status' in locals() else "UNKNOWN"
    }

def main():
    """Main function"""
    print("🔬 Code Turnitin Algorithm Improvement Tester")
    print("=" * 60)
    print("Testing improved algorithm against baseline results...")
    print("=" * 60)
    
    # Load baseline results
    baseline_data = load_baseline_results()
    if not baseline_data:
        return
    
    # Run improved algorithm test
    try:
        improved_results = run_improved_algorithm_test()
        if not improved_results:
            print("❌ Failed to run improved algorithm tests")
            return
        
        # Compare results
        comparison = compare_with_baseline(improved_results, baseline_data)
        
        # Save improved results
        report_data = {
            'test_metadata': {
                'timestamp': time.time(),
                'algorithm_version': 'improved_v1',
                'test_cases': len(improved_results)
            },
            'improved_results': improved_results,
            'baseline_comparison': comparison,
            'baseline_file': baseline_data.get('test_metadata', {}).get('timestamp', 'unknown')
        }
        
        os.makedirs('tests/reports', exist_ok=True)
        report_file = f"tests/reports/algorithm_improved_after_{int(time.time())}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n📄 Improved algorithm report saved: {report_file}")
        print("\n✅ Algorithm improvement testing completed!")
        
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()