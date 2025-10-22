"""
Web Routes - Template Rendering
Handles all template rendering routes and static file serving
"""
from flask import Blueprint, render_template, send_from_directory, current_app, jsonify, request
import sys
from pathlib import Path

# Add demo modules to path
sys.path.append(str(Path(__file__).parent.parent))
from demo.demo_handler import get_demo_handler, initialize_demo
from demo.demo_similarity import get_demo_analyzer

# Create blueprint for web routes
web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Main index page"""
    return render_template('index.html')


@web_bp.route('/classroom')
def classroom_page():
    """Classroom management page"""
    return render_template('classroom.html')


@web_bp.route('/test-repos')
def test_repos_page():
    """Test repositories page"""
    return render_template('test_repos.html')


@web_bp.route('/demo')
def demo_page():
    """Demo page for thesis presentation"""
    # Initialize demo system
    success, issues = initialize_demo()
    
    if not success:
        return render_template('error.html', 
                             title='Demo System Error',
                             message='Failed to initialize demo system',
                             details=issues), 500
    
    # Get demo handler and basic info
    handler = get_demo_handler()
    demo_info = {
        'languages': handler.get_available_languages(),
        'total_repositories': handler.get_total_repositories(),
        'metadata': handler.get_demo_metadata(),
        'sample_repos': handler.get_sample_repositories(3)  # 3 samples per language
    }
    
    # Get available algorithms
    analyzer = get_demo_analyzer()
    algorithms = analyzer.get_available_algorithms()
    
    return render_template('demo.html', 
                         demo_info=demo_info, 
                         algorithms=algorithms)


@web_bp.route('/demo/api/repositories')
def demo_api_repositories():
    """API endpoint to get repositories by language"""
    language = request.args.get('language')
    search_query = request.args.get('search', '')
    
    handler = get_demo_handler()
    
    if search_query:
        # Search repositories
        repositories = handler.search_repositories(search_query, language)
    elif language:
        # Get repositories by language
        repos = handler.get_repositories_by_language(language)
        repositories = [handler.get_repository_summary(repo) for repo in repos]
    else:
        # Get all repositories from all languages
        all_repos = handler.get_all_repositories()
        repositories = []
        for lang, repos in all_repos.items():
            repositories.extend([handler.get_repository_summary(repo) for repo in repos])
    
    return jsonify({
        'repositories': repositories,
        'total_count': len(repositories),
        'language': language,
        'search_query': search_query
    })


@web_bp.route('/demo/api/analyze', methods=['POST'])
def demo_api_analyze():
    """API endpoint to perform similarity analysis"""
    try:
        data = request.get_json()
        source_repo_id = data.get('source_repo_id')
        target_repo_ids = data.get('target_repo_ids', [])
        algorithm = data.get('algorithm', 'jaccard')
        
        if not source_repo_id or not target_repo_ids:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Get repositories
        handler = get_demo_handler()
        source_repo = None
        target_repos = []
        
        # Find source repository
        for lang in handler.get_available_languages():
            repo = handler.get_repository_by_id(source_repo_id, lang)
            if repo:
                source_repo = repo
                break
        
        if not source_repo:
            return jsonify({'error': 'Source repository not found'}), 404
        
        # Find target repositories
        for target_id in target_repo_ids:
            for lang in handler.get_available_languages():
                repo = handler.get_repository_by_id(target_id, lang)
                if repo:
                    target_repos.append(repo)
                    break
        
        if not target_repos:
            return jsonify({'error': 'No target repositories found'}), 404
        
        # Perform analysis
        analyzer = get_demo_analyzer()
        results = analyzer.analyze_repositories(source_repo, target_repos, algorithm)
        
        # Record analysis in handler
        for comparison in results['comparisons']:
            handler.record_analysis(
                source_repo_id, 
                comparison['target_repository']['id'],
                source_repo['language'],
                comparison['similarity_score']
            )
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@web_bp.route('/demo/api/comparison-detail/<source_id>/<target_id>')
def demo_api_comparison_detail(source_id, target_id):
    """API endpoint to get detailed comparison between two repositories"""
    try:
        # Get repositories
        handler = get_demo_handler()
        source_repo = None
        target_repo = None
        
        # Find source repository
        for lang in handler.get_available_languages():
            repo = handler.get_repository_by_id(source_id, lang)
            if repo:
                source_repo = repo
                break
        
        # Find target repository
        for lang in handler.get_available_languages():
            repo = handler.get_repository_by_id(target_id, lang)
            if repo:
                target_repo = repo
                break
        
        if not source_repo or not target_repo:
            return jsonify({'error': 'One or both repositories not found'}), 404
        
        # Get detailed comparison
        analyzer = get_demo_analyzer()
        detailed_comparison = analyzer.get_detailed_comparison(source_repo, target_repo)
        
        return jsonify(detailed_comparison)
        
    except Exception as e:
        return jsonify({'error': f'Detailed comparison failed: {str(e)}'}), 500


@web_bp.route('/demo/api/file-pair-comparison/<source_id>/<target_id>')
def demo_api_file_pair_comparison(source_id, target_id):
    """API endpoint to get detailed comparison for specific file pair"""
    try:
        # Get file parameters from request
        from flask import request
        source_file = request.args.get('source_file')
        target_file = request.args.get('target_file')
        
        if not source_file or not target_file:
            return jsonify({'error': 'source_file and target_file parameters are required'}), 400
        
        # Get repositories
        handler = get_demo_handler()
        source_repo = None
        target_repo = None
        
        # Find source repository
        for lang in handler.get_available_languages():
            repo = handler.get_repository_by_id(source_id, lang)
            if repo:
                source_repo = repo
                break
        
        # Find target repository
        for lang in handler.get_available_languages():
            repo = handler.get_repository_by_id(target_id, lang)
            if repo:
                target_repo = repo
                break
        
        if not source_repo or not target_repo:
            return jsonify({'error': 'One or both repositories not found'}), 404
        
        # Get file pair comparison
        analyzer = get_demo_analyzer()
        source_path = analyzer._get_repository_path(source_repo)
        target_path = analyzer._get_repository_path(target_repo)
        
        if not source_path or not target_path:
            return jsonify({'error': 'Repository paths not found'}), 404
        
        file_pair_details = analyzer._get_file_pair_details(
            source_path, target_path, source_file, target_file
        )
        
        return jsonify(file_pair_details)
        
    except Exception as e:
        return jsonify({'error': f'File pair comparison failed: {str(e)}'}), 500


@web_bp.route('/demo/api/statistics')
def demo_api_statistics():
    """API endpoint to get demo session statistics"""
    handler = get_demo_handler()
    analyzer = get_demo_analyzer()
    
    stats = {
        'session': handler.get_session_statistics(),
        'demo_metadata': handler.get_demo_metadata(),
        'language_stats': handler.get_language_statistics(),
        'analysis_history': analyzer.get_analysis_history()[-10:],  # Last 10 analyses
        'cache_info': analyzer.get_cache_info()
    }
    
    return jsonify(stats)


@web_bp.route('/demo/api/candidates')
def demo_api_candidates():
    """API endpoint to get comparison candidates for a repository"""
    repo_id = request.args.get('repo_id')
    limit = request.args.get('limit', 50, type=int)  # Increase default limit to 50
    
    print(f"DEBUG: Candidates request - repo_id: {repo_id} (type: {type(repo_id)})")
    
    if not repo_id:
        return jsonify({'error': 'Repository ID is required'}), 400
    
    # Find the source repository
    handler = get_demo_handler()
    source_repo = None
    
    print(f"DEBUG: Available languages: {handler.get_available_languages()}")
    
    for lang in handler.get_available_languages():
        repo = handler.get_repository_by_id(repo_id, lang)
        print(f"DEBUG: Searching in {lang} for repo_id {repo_id}: {'Found' if repo else 'Not found'}")
        if repo:
            source_repo = repo
            break
    
    if not source_repo:
        print(f"DEBUG: Repository {repo_id} not found in any language")
        return jsonify({'error': 'Repository not found'}), 404
    
    print(f"DEBUG: Found source repo: {source_repo.get('name')} ({source_repo.get('language')})")
    
    # Get comparison candidates
    candidates = handler.get_comparison_candidates(source_repo, limit)
    
    print(f"DEBUG: Generated {len(candidates)} candidates")
    
    return jsonify({
        'source_repository': handler.get_repository_summary(source_repo),
        'candidates': candidates,
        'total_candidates': len(candidates)
    })


@web_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(current_app.static_folder, filename)


def register_web_routes(app):
    """
    Register web routes with the Flask application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(web_bp)
