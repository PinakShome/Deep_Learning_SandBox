#!/usr/bin/env python3
"""
Dynamic Source Manager - Automatically manages news sources based on user engagement
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from dataclasses import dataclass
import requests
import feedparser
from collections import defaultdict
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class SourceMetrics:
    """Track metrics for each news source"""
    name: str
    url: str
    total_articles: int = 0
    relevant_articles: int = 0
    user_clicks: int = 0
    user_downloads: int = 0
    avg_relevance_score: float = 0.0
    last_updated: datetime = None
    is_active: bool = True
    engagement_rate: float = 0.0

class DynamicSourceManager:
    def __init__(self, metrics_file: str = "source_metrics.json"):
        self.metrics_file = metrics_file
        self.sources = {}
        self.metrics = {}
        self.engagement_threshold = 0.3  # Minimum engagement rate to keep source
        self.relevance_threshold = 0.5   # Minimum relevance score
        self.max_sources = 50            # Maximum number of active sources
        
        # Tech keywords for relevance checking
        self.tech_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'software engineering', 'programming', 'technology', 'tech',
            'computer science', 'data science', 'AI', 'ML', 'coding'
        ]
        
        # Load existing metrics
        self.load_metrics()
        
        # Initialize with default sources
        self.initialize_default_sources()
    
    def initialize_default_sources(self):
        """Initialize with default high-quality sources"""
        default_sources = {
            'tech_crunch': 'https://techcrunch.com/feed/',
            'venture_beat': 'https://venturebeat.com/feed/',
            'wired': 'https://www.wired.com/feed/rss',
            'arstechnica': 'https://feeds.arstechnica.com/arstechnica/index',
            'the_verge': 'https://www.theverge.com/rss/index.xml',
            'mit_tech_review': 'https://www.technologyreview.com/feed/',
            'ieee_spectrum': 'https://spectrum.ieee.org/rss',
            'science_daily': 'https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml'
        }
        
        for name, url in default_sources.items():
            if name not in self.metrics:
                self.add_source(name, url)
    
    def add_source(self, name: str, url: str) -> bool:
        """Add a new source and test its validity"""
        try:
            # Test if the RSS feed is valid
            feed = feedparser.parse(url)
            if feed.entries:
                self.sources[name] = url
                self.metrics[name] = SourceMetrics(
                    name=name,
                    url=url,
                    last_updated=datetime.now()
                )
                logger.info(f"Added new source: {name}")
                return True
            else:
                logger.warning(f"Invalid RSS feed for {name}: {url}")
                return False
        except Exception as e:
            logger.error(f"Error adding source {name}: {e}")
            return False
    
    def remove_source(self, name: str):
        """Remove a source based on poor performance"""
        if name in self.sources:
            del self.sources[name]
            if name in self.metrics:
                del self.metrics[name]
            logger.info(f"Removed source: {name}")
    
    def update_metrics(self, source_name: str, article_count: int, 
                      relevant_count: int, avg_score: float):
        """Update metrics for a source after processing"""
        if source_name in self.metrics:
            metrics = self.metrics[source_name]
            metrics.total_articles += article_count
            metrics.relevant_articles += relevant_count
            metrics.avg_relevance_score = avg_score
            metrics.last_updated = datetime.now()
            
            # Calculate engagement rate
            if metrics.total_articles > 0:
                metrics.engagement_rate = metrics.relevant_articles / metrics.total_articles
    
    def record_user_engagement(self, source_name: str, action: str):
        """Record user engagement (clicks, downloads, etc.)"""
        if source_name in self.metrics:
            metrics = self.metrics[source_name]
            if action == 'click':
                metrics.user_clicks += 1
            elif action == 'download':
                metrics.user_downloads += 1
    
    def get_top_sources(self, limit: int = 20) -> Dict[str, str]:
        """Get top performing sources based on engagement"""
        # Sort sources by engagement rate and relevance score
        sorted_sources = sorted(
            self.metrics.items(),
            key=lambda x: (x[1].engagement_rate, x[1].avg_relevance_score),
            reverse=True
        )
        
        return {name: self.sources[name] for name, _ in sorted_sources[:limit]}
    
    def auto_optimize_sources(self):
        """Automatically optimize source list based on performance"""
        # Remove poor performing sources
        sources_to_remove = []
        for name, metrics in self.metrics.items():
            if (metrics.engagement_rate < self.engagement_threshold and 
                metrics.avg_relevance_score < self.relevance_threshold):
                sources_to_remove.append(name)
        
        for name in sources_to_remove:
            self.remove_source(name)
        
        # Add new sources if we have room
        if len(self.sources) < self.max_sources:
            new_sources = self.discover_new_sources()
            for source in new_sources:
                if len(self.sources) >= self.max_sources:
                    break
                self.add_source(source['name'], source['url'])
        
        # Save updated metrics
        self.save_metrics()
    
    def discover_new_sources(self) -> List[Dict[str, str]]:
        """Discover new sources from various methods"""
        new_sources = []
        
        # Method 1: Curated lists (most reliable)
        new_sources.extend(self.discover_from_curated_lists())
        
        # Method 2: RSS directories
        new_sources.extend(self.discover_from_rss_directories())
        
        # Method 3: Tech aggregators
        new_sources.extend(self.discover_from_tech_aggregators())
        
        return new_sources
    
    def discover_from_curated_lists(self) -> List[Dict[str, str]]:
        """Discover sources from curated tech blog lists"""
        curated_sources = [
            {'name': 'hacker_news', 'url': 'https://news.ycombinator.com/rss'},
            {'name': 'slashdot', 'url': 'https://rss.slashdot.org/Slashdot/slashdotMain'},
            {'name': 'engadget', 'url': 'https://www.engadget.com/rss.xml'},
            {'name': 'gizmodo', 'url': 'https://gizmodo.com/rss'},
            {'name': 'tech_radar', 'url': 'https://www.techradar.com/rss'},
            {'name': 'zdnet', 'url': 'https://www.zdnet.com/news/rss.xml'},
            {'name': 'cnet', 'url': 'https://www.cnet.com/rss/all/'},
            {'name': 'tech_republic', 'url': 'https://www.techrepublic.com/rssfeeds/articles/'},
            {'name': 'information_week', 'url': 'https://www.informationweek.com/rss_simple.asp'},
            {'name': 'computer_world', 'url': 'https://www.computerworld.com/index.rss'},
            {'name': 'ai_news', 'url': 'https://artificialintelligence-news.com/feed/'},
            {'name': 'machine_learning_mastery', 'url': 'https://machinelearningmastery.com/feed/'},
            {'name': 'deep_learning_ai', 'url': 'https://www.deeplearning.ai/feed/'},
            {'name': 'google_ai_blog', 'url': 'https://ai.googleblog.com/feeds/posts/default'},
            {'name': 'openai_blog', 'url': 'https://openai.com/blog/rss.xml'},
            {'name': 'nvidia_ai', 'url': 'https://blogs.nvidia.com/feed/'},
            {'name': 'microsoft_ai', 'url': 'https://blogs.microsoft.com/ai/feed/'},
            {'name': 'aws_ai', 'url': 'https://aws.amazon.com/blogs/machine-learning/feed/'},
            {'name': 'google_cloud_ai', 'url': 'https://cloud.google.com/blog/products/ai-machine-learning/rss'},
            {'name': 'ibm_watson', 'url': 'https://www.ibm.com/blogs/watson/feed/'},
            {'name': 'stack_overflow_blog', 'url': 'https://stackoverflow.blog/feed/'},
            {'name': 'github_blog', 'url': 'https://github.blog/feed/'},
            {'name': 'dev_to', 'url': 'https://dev.to/feed'},
            {'name': 'medium_programming', 'url': 'https://medium.com/feed/tag/programming'},
            {'name': 'hashnode', 'url': 'https://hashnode.com/rss'},
        ]
        
        new_sources = []
        for source in curated_sources:
            # Only add if not already in our sources
            if source['name'] not in self.sources:
                new_sources.append({
                    'name': source['name'],
                    'url': source['url'],
                    'method': 'curated_list'
                })
        
        return new_sources
    
    def discover_from_rss_directories(self) -> List[Dict[str, str]]:
        """Discover sources from RSS directories"""
        rss_directories = [
            'https://feedly.com/i/discover/sources/search/feed/',
            'https://rss.com/blog/rss-feeds/',
        ]
        
        new_sources = []
        for directory in rss_directories:
            try:
                # Implementation would scrape RSS directories
                pass
            except Exception as e:
                logger.error(f"Error discovering from {directory}: {e}")
        
        return new_sources
    
    def discover_from_tech_aggregators(self) -> List[Dict[str, str]]:
        """Discover sources from tech aggregators"""
        aggregators = [
            'https://alltop.com/technology',
            'https://techmeme.com/river',
        ]
        
        new_sources = []
        for aggregator in aggregators:
            try:
                # Implementation would scrape aggregator sites
                pass
            except Exception as e:
                logger.error(f"Error discovering from {aggregator}: {e}")
        
        return new_sources
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get a comprehensive performance report"""
        total_sources = len(self.sources)
        active_sources = len([m for m in self.metrics.values() if m.is_active])
        total_articles = sum(m.total_articles for m in self.metrics.values())
        total_relevant = sum(m.relevant_articles for m in self.metrics.values())
        
        return {
            'total_sources': total_sources,
            'active_sources': active_sources,
            'total_articles_processed': total_articles,
            'total_relevant_articles': total_relevant,
            'overall_relevance_rate': total_relevant / total_articles if total_articles > 0 else 0,
            'top_performing_sources': self.get_top_sources(5),
            'recent_additions': [name for name, metrics in self.metrics.items() 
                               if metrics.last_updated and 
                               (datetime.now() - metrics.last_updated).days < 7]
        }
    
    def load_metrics(self):
        """Load metrics from file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    for name, metrics_data in data.items():
                        self.metrics[name] = SourceMetrics(**metrics_data)
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            data = {}
            for name, metrics in self.metrics.items():
                data[name] = {
                    'name': metrics.name,
                    'url': metrics.url,
                    'total_articles': metrics.total_articles,
                    'relevant_articles': metrics.relevant_articles,
                    'user_clicks': metrics.user_clicks,
                    'user_downloads': metrics.user_downloads,
                    'avg_relevance_score': metrics.avg_relevance_score,
                    'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None,
                    'is_active': metrics.is_active,
                    'engagement_rate': metrics.engagement_rate
                }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

if __name__ == "__main__":
    # Test the dynamic source manager
    manager = DynamicSourceManager()
    print("Dynamic Source Manager initialized!")
    print(f"Active sources: {len(manager.sources)}")
    print("Top performing sources:", manager.get_top_sources(3))
    
    # Test source discovery
    print("\n🔍 Discovering new sources...")
    new_sources = manager.discover_new_sources()
    print(f"Found {len(new_sources)} new sources to add")
    for source in new_sources[:5]:
        print(f"- {source['name']} ({source['method']})")
