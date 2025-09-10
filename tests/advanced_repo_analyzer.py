#!/usr/bin/env python3
"""
Advanced Repository Data Analyzer
Menganalisis dan memisahkan data repository ke dalam berbagai kategori
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import re
from typing import Dict, List, Any

class RepositoryDataAnalyzer:
    def __init__(self, json_file_path: str):
        """
        Initialize analyzer dengan file JSON
        
        Args:
            json_file_path: Path ke file JSON hasil scraping
        """
        self.json_file_path = json_file_path
        self.repos = []
        self.load_data()
    
    def load_data(self):
        """
        Load data dari file JSON
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.repos = json.load(f)
            print(f"✅ Loaded {len(self.repos)} repositories from {self.json_file_path}")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.repos = []
    
    def categorize_by_subject(self) -> Dict[str, List[Dict]]:
        """
        Kategorisasi berdasarkan mata kuliah/subject
        """
        categories = defaultdict(list)
        
        # Pattern untuk mendeteksi subject
        subject_patterns = {
            'Web Programming': [
                r'tugas-web-', r'tugas-pemrograman-web', r'web-lanjut', r'pemrograman-web-lab'
            ],
            'Elasticsearch': [
                r'elasticsearch-', r'tugas-elasticsearch', r'tugas-elastic'
            ],
            'React Native': [
                r'react-native-expo', r'expo-'
            ],
            'Computer Vision': [
                r'computer-vision'
            ],
            'Database': [
                r'normalisasi-db', r'cms-'
            ],
            'NestJS': [
                r'lab2-nest-js', r'nest-js'
            ],
            'Git/GitHub': [
                r'git-github-fundamentals'
            ],
            'Data Science': [
                r'codespaces-jupyter', r'fastText'
            ],
            'OpenMP': [
                r'openMP'
            ],
            'Node.js': [
                r'lab-basic-nodejs'
            ],
            'Python Basic': [
                r'python-basic'
            ],
            'System Management': [
                r'sistem-manajemen-konten'
            ]
        }
        
        # Kategorisasi berdasarkan nama repository
        for repo in self.repos:
            repo_name = repo.get('name', '').lower()
            categorized = False
            
            for subject, patterns in subject_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, repo_name):
                        categories[subject].append(repo)
                        categorized = True
                        break
                if categorized:
                    break
            
            # Jika tidak cocok dengan pattern manapun
            if not categorized:
                categories['Others'].append(repo)
        
        return dict(categories)
    
    def categorize_by_language(self) -> Dict[str, List[Dict]]:
        """
        Kategorisasi berdasarkan bahasa pemrograman
        """
        categories = defaultdict(list)
        
        for repo in self.repos:
            language = repo.get('language') or 'Unknown'
            categories[language].append(repo)
        
        return dict(categories)
    
    def categorize_by_year_semester(self) -> Dict[str, List[Dict]]:
        """
        Kategorisasi berdasarkan tahun dan semester
        """
        categories = defaultdict(list)
        
        for repo in self.repos:
            created_at = repo.get('created_at', '')
            updated_at = repo.get('updated_at', '')
            
            # Ambil tahun dari created_at
            try:
                if created_at:
                    year = datetime.fromisoformat(created_at.replace('Z', '+00:00')).year
                elif updated_at:
                    year = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).year
                else:
                    year = 'Unknown'
                    
                # Tentukan semester berdasarkan bulan
                if created_at:
                    month = datetime.fromisoformat(created_at.replace('Z', '+00:00')).month
                    semester = 'Ganjil' if month >= 8 or month <= 1 else 'Genap'
                    period = f"{year}-{semester}"
                else:
                    period = str(year)
                    
                categories[period].append(repo)
            except:
                categories['Unknown'].append(repo)
        
        return dict(categories)
    
    def categorize_by_student(self) -> Dict[str, List[Dict]]:
        """
        Kategorisasi berdasarkan nama mahasiswa (extract dari nama repo)
        """
        categories = defaultdict(list)
        
        # Pattern untuk extract username dari nama repository
        student_patterns = [
            r'tugas-\w+-(.+)$',  # tugas-web-username
            r'elasticsearch-(.+)$',  # elasticsearch-username
            r'react-native-expo-basic-installer-(.+)$',  # react-native-expo-basic-installer-username
            r'tugas-pemrograman-web-\d*-(.+)$',  # tugas-pemrograman-web-2-username
            r'final-web-lanjut-\d+-(.+)$',  # final-web-lanjut-20231-username
            r'git-github-fundamentals-(.+)$'  # git-github-fundamentals-username
        ]
        
        for repo in self.repos:
            repo_name = repo.get('name', '')
            student_found = False
            
            for pattern in student_patterns:
                match = re.search(pattern, repo_name)
                if match:
                    student_name = match.group(1)
                    categories[student_name].append(repo)
                    student_found = True
                    break
            
            if not student_found:
                categories['No Student Pattern'].append(repo)
        
        return dict(categories)
    
    def categorize_by_activity_level(self) -> Dict[str, List[Dict]]:
        """
        Kategorisasi berdasarkan tingkat aktivitas
        """
        categories = {
            'High Activity (>5 stars or forks)': [],
            'Medium Activity (1-5 stars or forks)': [],
            'Low Activity (0 stars and forks)': []
        }
        
        for repo in self.repos:
            stars = repo.get('stargazers_count', 0)
            forks = repo.get('forks_count', 0)
            total_activity = stars + forks
            
            if total_activity > 5:
                categories['High Activity (>5 stars or forks)'].append(repo)
            elif total_activity > 0:
                categories['Medium Activity (1-5 stars or forks)'].append(repo)
            else:
                categories['Low Activity (0 stars and forks)'].append(repo)
        
        return categories
    
    def categorize_by_repo_type(self) -> Dict[str, List[Dict]]:
        """
        Kategorisasi berdasarkan tipe repository
        """
        categories = {
            'GitHub Classroom Assignments': [],
            'Template Repositories': [],
            'Regular Projects': [],
            'Forked Projects': []
        }
        
        for repo in self.repos:
            description = (repo.get('description') or '').lower()
            name = (repo.get('name') or '').lower()
            
            if 'created by github classroom' in description:
                categories['GitHub Classroom Assignments'].append(repo)
            elif repo.get('fork', False):
                categories['Forked Projects'].append(repo)
            elif 'template' in name or repo.get('is_template', False):
                categories['Template Repositories'].append(repo)
            else:
                categories['Regular Projects'].append(repo)
        
        return categories
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Generate statistik comprehensive
        """
        stats = {}
        
        # Basic stats
        stats['total_repositories'] = len(self.repos)
        stats['total_stars'] = sum(repo.get('stargazers_count', 0) for repo in self.repos)
        stats['total_forks'] = sum(repo.get('forks_count', 0) for repo in self.repos)
        stats['total_issues'] = sum(repo.get('open_issues_count', 0) for repo in self.repos)
        
        # Privacy stats
        private_repos = [repo for repo in self.repos if repo.get('private', False)]
        stats['private_repositories'] = len(private_repos)
        stats['public_repositories'] = len(self.repos) - len(private_repos)
        
        # Language stats
        languages = Counter(repo.get('language', 'Unknown') for repo in self.repos)
        stats['languages'] = dict(languages.most_common())
        
        # Size stats
        sizes = [repo.get('size', 0) for repo in self.repos if repo.get('size', 0) > 0]
        if sizes:
            stats['average_size_kb'] = sum(sizes) / len(sizes)
            stats['total_size_kb'] = sum(sizes)
            stats['largest_repo_size_kb'] = max(sizes)
        
        # Activity timeline
        years = []
        for repo in self.repos:
            created_at = repo.get('created_at', '')
            if created_at:
                try:
                    year = datetime.fromisoformat(created_at.replace('Z', '+00:00')).year
                    years.append(year)
                except:
                    pass
        
        year_counts = Counter(years)
        stats['repositories_by_year'] = dict(year_counts.most_common())
        
        # Top contributors (students)
        student_counts = defaultdict(int)
        student_patterns = [
            r'tugas-\w+-(.+)$',
            r'elasticsearch-(.+)$',
            r'react-native-expo-basic-installer-(.+)$',
            r'tugas-pemrograman-web-\d*-(.+)$'
        ]
        
        for repo in self.repos:
            repo_name = repo.get('name', '')
            for pattern in student_patterns:
                match = re.search(pattern, repo_name)
                if match:
                    student_name = match.group(1)
                    student_counts[student_name] += 1
                    break
        
        stats['top_students'] = dict(Counter(student_counts).most_common(10))
        
        return stats
    
    def save_categorized_data(self, output_dir: str = "categorized_data"):
        """
        Save semua kategori ke file terpisah
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Categorize data
        print("🔄 Categorizing data...")
        
        categories = {
            'by_subject': self.categorize_by_subject(),
            'by_language': self.categorize_by_language(),
            'by_year_semester': self.categorize_by_year_semester(),
            'by_student': self.categorize_by_student(),
            'by_activity_level': self.categorize_by_activity_level(),
            'by_repo_type': self.categorize_by_repo_type()
        }
        
        # Save each category
        saved_files = []
        
        for category_name, category_data in categories.items():
            filename = f"{output_dir}/{category_name}_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(category_data, f, indent=2, ensure_ascii=False)
            saved_files.append(filename)
            print(f"💾 Saved {category_name}: {filename}")
        
        # Generate and save statistics
        stats = self.generate_statistics()
        stats_filename = f"{output_dir}/statistics_{timestamp}.json"
        with open(stats_filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        saved_files.append(stats_filename)
        print(f"📊 Saved statistics: {stats_filename}")
        
        # Generate summary report
        self.generate_summary_report(categories, stats, f"{output_dir}/summary_report_{timestamp}.md")
        
        return saved_files
    
    def generate_summary_report(self, categories: Dict, stats: Dict, filename: str):
        """
        Generate markdown summary report
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Lab-IF Repository Analysis Report\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Basic Statistics
            f.write("## 📊 Basic Statistics\n\n")
            f.write(f"- **Total Repositories:** {stats['total_repositories']:,}\n")
            f.write(f"- **Total Stars:** {stats['total_stars']:,}\n")
            f.write(f"- **Total Forks:** {stats['total_forks']:,}\n")
            f.write(f"- **Total Issues:** {stats['total_issues']:,}\n")
            f.write(f"- **Private Repositories:** {stats['private_repositories']:,} ({stats['private_repositories']/stats['total_repositories']*100:.1f}%)\n")
            f.write(f"- **Public Repositories:** {stats['public_repositories']:,} ({stats['public_repositories']/stats['total_repositories']*100:.1f}%)\n")
            
            if 'average_size_kb' in stats:
                f.write(f"- **Average Repository Size:** {stats['average_size_kb']:.1f} KB\n")
                f.write(f"- **Total Size:** {stats['total_size_kb']/1024:.1f} MB\n")
            
            f.write("\n")
            
            # Subject Categories
            f.write("## 📚 Subject Categories\n\n")
            subject_data = categories['by_subject']
            for subject, repos in sorted(subject_data.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"- **{subject}:** {len(repos):,} repositories\n")
            f.write("\n")
            
            # Language Distribution
            f.write("## 💻 Programming Languages\n\n")
            for lang, count in list(stats['languages'].items())[:10]:
                percentage = count / stats['total_repositories'] * 100
                f.write(f"- **{lang}:** {count:,} repositories ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Repository Types
            f.write("## 🏷️ Repository Types\n\n")
            repo_types = categories['by_repo_type']
            for repo_type, repos in repo_types.items():
                f.write(f"- **{repo_type}:** {len(repos):,} repositories\n")
            f.write("\n")
            
            # Activity Levels
            f.write("## 📈 Activity Levels\n\n")
            activity_levels = categories['by_activity_level']
            for level, repos in activity_levels.items():
                f.write(f"- **{level}:** {len(repos):,} repositories\n")
            f.write("\n")
            
            # Timeline
            f.write("## 📅 Repository Creation Timeline\n\n")
            for year, count in list(stats['repositories_by_year'].items())[:10]:
                f.write(f"- **{year}:** {count:,} repositories\n")
            f.write("\n")
            
            # Top Students
            f.write("## 🎓 Top Students (by repository count)\n\n")
            for student, count in list(stats['top_students'].items())[:10]:
                f.write(f"- **{student}:** {count:,} repositories\n")
            f.write("\n")
        
        print(f"📄 Generated summary report: {filename}")
    
    def print_category_summary(self):
        """
        Print ringkasan semua kategori
        """
        print("\n" + "="*80)
        print("🔍 REPOSITORY DATA ANALYSIS SUMMARY")
        print("="*80)
        
        categories = {
            'Subject': self.categorize_by_subject(),
            'Language': self.categorize_by_language(),
            'Year/Semester': self.categorize_by_year_semester(),
            'Student': self.categorize_by_student(),
            'Activity Level': self.categorize_by_activity_level(),
            'Repository Type': self.categorize_by_repo_type()
        }
        
        for category_name, category_data in categories.items():
            print(f"\n📋 {category_name.upper()} CATEGORIES:")
            print("-" * 50)
            
            # Sort by count
            sorted_categories = sorted(category_data.items(), key=lambda x: len(x[1]), reverse=True)
            
            for subcategory, repos in sorted_categories[:10]:  # Top 10
                count = len(repos)
                percentage = count / len(self.repos) * 100
                print(f"  {subcategory}: {count:,} repos ({percentage:.1f}%)")
            
            if len(sorted_categories) > 10:
                remaining = sum(len(repos) for _, repos in sorted_categories[10:])
                print(f"  ... and {len(sorted_categories)-10} more categories ({remaining:,} repos)")

def main():
    """
    Main function
    """
    print("🚀 Repository Data Analyzer")
    print("="*50)
    
    # Default file path
    default_file = "repo_analysis_Lab-IF_20250910_141914.json"
    
    json_file = input(f"JSON file path (default: {default_file}): ").strip()
    if not json_file:
        json_file = default_file
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    # Initialize analyzer
    analyzer = RepositoryDataAnalyzer(json_file)
    
    if not analyzer.repos:
        print("❌ No data to analyze")
        return
    
    while True:
        print("\n" + "="*50)
        print("Choose analysis option:")
        print("1. Print category summary")
        print("2. Save all categorized data to files")
        print("3. Generate specific category only")
        print("4. Generate statistics only")
        print("5. Exit")
        
        choice = input("Choice (1-5): ").strip()
        
        if choice == "1":
            analyzer.print_category_summary()
        
        elif choice == "2":
            output_dir = input("Output directory (default: categorized_data): ").strip()
            if not output_dir:
                output_dir = "categorized_data"
            
            saved_files = analyzer.save_categorized_data(output_dir)
            print(f"\n✅ Analysis complete! {len(saved_files)} files saved to '{output_dir}' directory")
        
        elif choice == "3":
            print("\nAvailable categories:")
            print("1. By Subject")
            print("2. By Language") 
            print("3. By Year/Semester")
            print("4. By Student")
            print("5. By Activity Level")
            print("6. By Repository Type")
            
            cat_choice = input("Category choice (1-6): ").strip()
            
            category_map = {
                '1': ('by_subject', analyzer.categorize_by_subject()),
                '2': ('by_language', analyzer.categorize_by_language()),
                '3': ('by_year_semester', analyzer.categorize_by_year_semester()),
                '4': ('by_student', analyzer.categorize_by_student()),
                '5': ('by_activity_level', analyzer.categorize_by_activity_level()),
                '6': ('by_repo_type', analyzer.categorize_by_repo_type())
            }
            
            if cat_choice in category_map:
                cat_name, cat_data = category_map[cat_choice]
                filename = f"{cat_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(cat_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Saved {cat_name} to: {filename}")
                
                # Print summary
                print(f"\n📋 {cat_name.upper()} SUMMARY:")
                for subcat, repos in sorted(cat_data.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                    print(f"  {subcat}: {len(repos):,} repositories")
        
        elif choice == "4":
            stats = analyzer.generate_statistics()
            stats_filename = f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Statistics saved to: {stats_filename}")
            
            # Print key stats
            print(f"\n📊 KEY STATISTICS:")
            print(f"  Total Repositories: {stats['total_repositories']:,}")
            print(f"  Total Stars: {stats['total_stars']:,}")
            print(f"  Total Forks: {stats['total_forks']:,}")
            print(f"  Private Repos: {stats['private_repositories']:,}")
            print(f"  Public Repos: {stats['public_repositories']:,}")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
