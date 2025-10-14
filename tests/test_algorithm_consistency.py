#!/usr/bin/env python3
"""
Algorithm Consistency Testing for Code Turnitin

This script tests the current algorithm consistency issues by:
1. Running same comparisons multiple times
2. Testing with real repository data
3. Documenting inconsistent results for fixing

Author: Created for Code Turnitin thesis presentation
Date: October 2025
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project paths
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import demo similarity analyzer
from demo.demo_similarity import get_demo_analyzer
from demo.demo_handler import get_demo_handler, initialize_demo

class AlgorithmConsistencyTester:
    """Test consistency of current similarity algorithm"""
    
    def __init__(self):
        """Initialize the consistency tester"""
        self.test_results = []
        self.demo_analyzer = None
        self.demo_handler = None
        
    def initialize_demo_system(self):
        """Initialize demo system for testing"""
        print("🔧 Initializing demo system...")
        success, issues = initialize_demo()
        if not success:
            print(f"❌ Failed to initialize demo system: {issues}")
            return False
            
        self.demo_analyzer = get_demo_analyzer()
        self.demo_handler = get_demo_handler()
        print("✅ Demo system initialized successfully")
        return True
    
    def get_test_repositories(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get real repositories for testing"""
        print(f"📋 Getting {count} test repositories...")
        
        # Get repositories from different languages
        test_repos = []
        
        # Get Java repositories
        java_repos = self.demo_handler.get_repositories_by_language('Java')
        if java_repos:
            test_repos.extend(java_repos[:2])  # Take 2 Java repos
            
        # Get JavaScript repositories  
        js_repos = self.demo_handler.get_repositories_by_language('JavaScript')
        if js_repos:
            test_repos.extend(js_repos[:2])  # Take 2 JS repos
            
        # Get Python repositories
        python_repos = self.demo_handler.get_repositories_by_language('Python')
        if python_repos:
            test_repos.extend(python_repos[:1])  # Take 1 Python repo
            
        test_repos = test_repos[:count]  # Limit to requested count
        print(f"✅ Found {len(test_repos)} test repositories")
        return test_repos
    
    def test_algorithm_consistency(self, repo1: Dict[str, Any], repo2: Dict[str, Any], 
                                 runs: int = 5) -> Dict[str, Any]:
        """Test consistency by running same comparison multiple times"""
        print(f"🧪 Testing consistency: {repo1.get('name')} vs {repo2.get('name')} ({runs} runs)")
        
        results = []
        start_time = time.time()
        
        for run in range(runs):
            print(f"   Run {run + 1}/{runs}...", end=" ")
            
            try:
                # Run the same comparison
                comparison_result = self.demo_analyzer.compare_repositories(
                    source_repo=repo1,
                    target_repo=repo2,
                    algorithm='jaccard'
                )
                
                similarity_score = comparison_result.get('similarity_score', 0.0)
                processing_time = comparison_result.get('processing_time', 0.0)
                
                results.append({
                    'run': run + 1,
                    'similarity_score': similarity_score,
                    'processing_time': processing_time,
                    'timestamp': time.time()
                })
                
                print(f"Score: {similarity_score:.4f}")
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                results.append({
                    'run': run + 1,
                    'error': str(e),
                    'timestamp': time.time()
                })
                
        total_time = time.time() - start_time
        
        # Analyze consistency
        valid_scores = [r['similarity_score'] for r in results if 'similarity_score' in r]
        
        if valid_scores:
            min_score = min(valid_scores)
            max_score = max(valid_scores)
            avg_score = sum(valid_scores) / len(valid_scores)
            score_variance = max_score - min_score
            
            is_consistent = score_variance < 0.001  # Threshold for consistency
            
            consistency_analysis = {
                'repo1': {'id': repo1.get('id'), 'name': repo1.get('name'), 'language': repo1.get('language')},
                'repo2': {'id': repo2.get('id'), 'name': repo2.get('name'), 'language': repo2.get('language')},
                'total_runs': runs,
                'successful_runs': len(valid_scores),
                'failed_runs': runs - len(valid_scores),
                'results': results,
                'analysis': {
                    'min_score': min_score,
                    'max_score': max_score,
                    'average_score': avg_score,
                    'score_variance': score_variance,
                    'is_consistent': is_consistent,
                    'consistency_level': 'GOOD' if score_variance < 0.001 else ('MEDIUM' if score_variance < 0.01 else 'POOR')
                },
                'total_time': total_time,
                'average_processing_time': sum(r.get('processing_time', 0) for r in results) / len(results)
            }
            
            print(f"   📊 Results: Min={min_score:.4f}, Max={max_score:.4f}, Variance={score_variance:.4f}")
            print(f"   🎯 Consistency: {consistency_analysis['analysis']['consistency_level']}")
            
        else:
            consistency_analysis = {
                'repo1': {'id': repo1.get('id'), 'name': repo1.get('name')},
                'repo2': {'id': repo2.get('id'), 'name': repo2.get('name')},
                'error': 'All runs failed',
                'total_runs': runs,
                'successful_runs': 0,
                'failed_runs': runs,
                'results': results
            }
            print("   ❌ All runs failed!")
            
        return consistency_analysis
    
    def run_comprehensive_test(self, test_pairs: int = 10, runs_per_pair: int = 5):
        """Run comprehensive consistency testing"""
        print(f"🚀 Starting comprehensive algorithm consistency test")
        print(f"📋 Test parameters: {test_pairs} pairs, {runs_per_pair} runs each")
        print("=" * 60)
        
        # Get test repositories
        test_repos = self.get_test_repositories(count=6)
        
        if len(test_repos) < 2:
            print("❌ Not enough repositories for testing")
            return None
            
        # Generate test pairs
        test_cases = []
        repo_count = len(test_repos)
        
        for i in range(min(test_pairs, repo_count * (repo_count - 1) // 2)):
            repo1_idx = i % repo_count
            repo2_idx = (i + 1) % repo_count
            if repo1_idx != repo2_idx:
                test_cases.append((test_repos[repo1_idx], test_repos[repo2_idx]))
        
        print(f"📝 Generated {len(test_cases)} test cases")
        print("=" * 60)
        
        # Run tests
        all_results = []
        consistency_summary = {
            'good': 0,
            'medium': 0, 
            'poor': 0,
            'failed': 0
        }
        
        for idx, (repo1, repo2) in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {idx}/{len(test_cases)}")
            result = self.test_algorithm_consistency(repo1, repo2, runs_per_pair)
            all_results.append(result)
            
            # Update summary
            if 'analysis' in result:
                level = result['analysis']['consistency_level']
                if level == 'GOOD':
                    consistency_summary['good'] += 1
                elif level == 'MEDIUM':
                    consistency_summary['medium'] += 1
                else:
                    consistency_summary['poor'] += 1
            else:
                consistency_summary['failed'] += 1
        
        # Generate final report
        print("\n" + "=" * 60)
        print("📊 ALGORITHM CONSISTENCY TEST RESULTS")
        print("=" * 60)
        
        total_tests = len(all_results)
        print(f"Total test cases: {total_tests}")
        print(f"✅ Good consistency (variance < 0.001): {consistency_summary['good']} ({consistency_summary['good']/total_tests*100:.1f}%)")
        print(f"⚠️  Medium consistency (variance < 0.01): {consistency_summary['medium']} ({consistency_summary['medium']/total_tests*100:.1f}%)")
        print(f"❌ Poor consistency (variance >= 0.01): {consistency_summary['poor']} ({consistency_summary['poor']/total_tests*100:.1f}%)")
        print(f"💥 Failed tests: {consistency_summary['failed']} ({consistency_summary['failed']/total_tests*100:.1f}%)")
        
        # Overall assessment
        good_percentage = consistency_summary['good'] / total_tests * 100
        if good_percentage >= 90:
            overall_status = "🟢 EXCELLENT"
        elif good_percentage >= 70:
            overall_status = "🟡 ACCEPTABLE"  
        elif good_percentage >= 50:
            overall_status = "🟠 NEEDS IMPROVEMENT"
        else:
            overall_status = "🔴 CRITICAL - MAJOR ISSUES"
            
        print(f"\n🎯 Overall Algorithm Status: {overall_status}")
        
        # Save detailed results
        report_data = {
            'test_metadata': {
                'timestamp': time.time(),
                'test_pairs': test_pairs,
                'runs_per_pair': runs_per_pair,
                'total_test_cases': total_tests
            },
            'summary': consistency_summary,
            'overall_status': overall_status,
            'detailed_results': all_results
        }
        
        # Save to file
        os.makedirs('tests/reports', exist_ok=True)
        report_file = f"tests/reports/algorithm_consistency_before_{int(time.time())}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"📄 Detailed report saved: {report_file}")
        
        return report_data

def main():
    """Main testing function"""
    print("🧪 Code Turnitin Algorithm Consistency Tester")
    print("=" * 60)
    print("Testing current algorithm for consistency issues...")
    print("This will help establish baseline before fixes.")
    print("=" * 60)
    
    # Initialize tester
    tester = AlgorithmConsistencyTester()
    
    # Initialize demo system
    if not tester.initialize_demo_system():
        return
    
    # Run comprehensive test
    try:
        report = tester.run_comprehensive_test(
            test_pairs=8,  # Test 8 pairs
            runs_per_pair=5  # 5 runs each for consistency check
        )
        
        if report:
            print("\n✅ Testing completed successfully!")
            print("📋 Next steps:")
            print("1. Review the consistency results")
            print("2. Identify problematic areas") 
            print("3. Implement algorithm fixes")
            print("4. Re-run tests to verify improvements")
        else:
            print("\n❌ Testing failed!")
            
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()