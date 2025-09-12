import os
import re
import time
import uuid
import json
from collections import Counter, defaultdict
from urllib.parse import quote_plus

import requests

from .github_scraper import scrape_repo_files

STOPWORDS = set([
    'if','else','for','while','do','return','function','var','const','let','class','public','private','protected',
    'static','void','int','float','double','char','bool','true','false','null','this','super','new','import','export',
    'default','try','catch','finally','async','await','break','continue','switch','case','in','of','typeof','instanceof',
    'def','from','as','with','open','lambda','yield','none','true','false','and','or','not','package','using','namespace',
    'main','app','test','tests','init','run','data','value','temp','result','calc','info','util','utils','helper'
])

MAX_STUDENT_FILES_FOR_FEATURES = 200
MAX_TOKEN_LEN = 40
TOKEN_REGEX = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b')

SEARCH_TIMEOUT_SECONDS = 15
MAX_CODE_SEARCH_QUERIES = 6
PER_PAGE = 20

EXT_TO_LANGUAGE = {
    '.py': 'Python', '.js': 'JavaScript', '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.cs': 'C#', '.rb': 'Ruby',
    '.php': 'PHP', '.go': 'Go', '.ts': 'TypeScript'
}

def _read_file_safely(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()[:20000]
    except Exception:
        return ''

def extract_features_from_student_repos(student_repo_urls, base_dir, scrape_func=scrape_repo_files):
    os.makedirs(base_dir, exist_ok=True)
    downloaded_files = []
    for repo_url in student_repo_urls:
        downloaded_files.extend(scrape_repo_files(repo_url, base_dir))
    limited_files = downloaded_files[:MAX_STUDENT_FILES_FOR_FEATURES]
    token_counter = Counter()
    file_basenames = []
    language_counter = Counter()
    for fname in limited_files:
        path = os.path.join(base_dir, fname)
        if not os.path.isfile(path):
            continue
        content = _read_file_safely(path)
        if not content:
            continue
        tokens = TOKEN_REGEX.findall(content)
        for t in tokens:
            tl = t.lower()
            if tl in STOPWORDS or len(tl) > MAX_TOKEN_LEN:
                continue
            token_counter[tl] += 1
        base = os.path.splitext(os.path.basename(fname))[0].lower()
        if base and base not in STOPWORDS and len(base) > 3:
            file_basenames.append(base)
        ext = os.path.splitext(fname)[1].lower()
        if ext:
            language_counter[ext] += 1
    dominant_ext = None
    if language_counter:
        dominant_ext = language_counter.most_common(1)[0][0]
    top_tokens = [t for t, _ in token_counter.most_common(20)]
    top_file_names = list(dict.fromkeys(file_basenames))[:10]
    return {
        'files': downloaded_files,
        'tokens': top_tokens,
        'file_basenames': top_file_names,
        'languages': language_counter,
        'dominant_ext': dominant_ext
    }

def build_code_search_queries(features):
    tokens = features['tokens']
    file_bases = features['file_basenames']
    dominant_lang = EXT_TO_LANGUAGE.get(features['dominant_ext'] or '', None)
    queries = []
    def quote_token(t):
        return f'"{t}"' if len(t) > 10 else t
    for fb in file_bases[:3]:
        if tokens:
            queries.append(f'{quote_token(fb)} {quote_token(tokens[0])}')
    for i in range(0, min(len(tokens), 6), 2):
        chunk = tokens[i:i+2]
        if len(chunk) >= 2:
            queries.append(' '.join(quote_token(c) for c in chunk))
    for t in tokens[:2]:
        queries.append(quote_token(t))
    seen = set()
    final_queries = []
    for q in queries:
        qn = q.strip()
        if qn and qn not in seen:
            seen.add(qn)
            final_queries.append(qn)
    output = []
    for idx, q in enumerate(final_queries):
        if dominant_lang and idx % 2 == 0:
            output.append({'q': q, 'language': dominant_lang})
        else:
            output.append({'q': q, 'language': None})
        if len(output) >= MAX_CODE_SEARCH_QUERIES:
            break
    return output

def perform_code_search(queries, github_token, deadline_ts):
    headers = {'Accept': 'application/vnd.github.text-match+json'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    repo_hits = defaultdict(lambda: {'files': set(), 'matched_tokens': Counter()})
    for qobj in queries:
        if time.time() > deadline_ts - 2:
            break
        q = qobj['q']
        language = qobj['language']
        full_query = q
        if language:
            full_query += f' language:{language}'
        url = f'https://api.github.com/search/code?q={quote_plus(full_query)}&per_page=20'
        try:
            resp = requests.get(url, headers=headers, timeout=3)
            if resp.status_code == 403:
                break
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue
        for item in data.get('items', []):
            repo = item.get('repository', {})
            full_name = repo.get('full_name')
            if not full_name:
                continue
            path = item.get('path') or ''
            repo_entry = repo_hits[full_name]
            repo_entry['files'].add(path)
            for token in q.split():
                tclean = token.strip('"').lower()
                if tclean and tclean not in STOPWORDS:
                    repo_entry['matched_tokens'][tclean] += 1
    return repo_hits

def enrich_repo_metadata(repo_hits, github_token, deadline_ts, max_repos=20):
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    ranked = []
    names = list(repo_hits.keys())[:max_repos]
    for name in names:
        if time.time() > deadline_ts - 1:
            break
        url = f'https://api.github.com/repos/{name}'
        size = stars = 0
        try:
            r = requests.get(url, headers=headers, timeout=3)
            if r.ok:
                j = r.json()
                size = j.get('size', 0)
                stars = j.get('stargazers_count', 0)
        except Exception:
            pass
        entry = repo_hits[name]
        ranked.append({
            'full_name': name,
            'files': list(entry['files']),
            'matched_tokens': dict(entry['matched_tokens']),
            'size_kb': size,
            'stars': stars,
        })
    return ranked

def score_and_select(repos, features, top_n=5):
    student_tokens_set = set(features['tokens']) if features['tokens'] else set()
    student_file_bases = set(features['file_basenames']) if features['file_basenames'] else set()
    scored = []
    for r in repos:
        matched_tokens = set(r['matched_tokens'].keys())
        token_overlap = 0.0
        if student_tokens_set:
            token_overlap = len(matched_tokens & student_tokens_set) / len(student_tokens_set)
        file_bases_repo = {os.path.splitext(os.path.basename(f))[0].lower() for f in r['files']}
        file_overlap = 0.0
        if student_file_bases:
            file_overlap = len(file_bases_repo & student_file_bases) / len(student_file_bases)
        hit_density = min(len(r['files']) / 10, 1.0)
        size_penalty = 0.0
        if r['size_kb'] > 5000:
            size_penalty = 0.2
        stars_penalty = 0.0
        if r['stars'] > 5000:
            stars_penalty = 0.1
        score = (0.35 * token_overlap + 0.25 * file_overlap + 0.25 * hit_density + 0.15 * (1 - size_penalty))
        score -= stars_penalty
        score = max(0.0, min(score, 1.0))
        r['score'] = score
        r['token_overlap'] = round(token_overlap, 3)
        r['file_overlap'] = round(file_overlap, 3)
        r['hit_density'] = round(hit_density, 3)
        r['penalties'] = {'size_penalty': size_penalty, 'stars_penalty': stars_penalty}
        scored.append(r)
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:top_n]
