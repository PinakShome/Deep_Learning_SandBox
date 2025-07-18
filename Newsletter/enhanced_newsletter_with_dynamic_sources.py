#!/usr/bin/env python3
"""
Enhanced Newsletter Generator with Dynamic Source Management
"""

import os
import requests
import feedparser
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv
import openai
from bs4 import BeautifulSoup
import newspaper
from textblob import TextBlob
import pandas as pd
from dynamic_source_manager import DynamicSourceManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedNewsletterGeneratorWithDynamicSources:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.source_manager = DynamicSourceManager()
        self.articles = []
        self.top_articles = []
        
    def fetch_articles_from_dynamic_sources(self) -> List[Dict]:
        """Fetch articles from dynamically managed sources"""
        articles = []
        
        # Get top performing sources
        top_sources = self.source_manager.get_top_sources(limit=15)
        
        for source_name, feed_url in top_sources.items():
            try:
                logger.info(f"Fetching from {source_name}")
                feed = feedparser.parse(feed_url)
                
                relevant_count = 0
                total_count = 0
                relevance_scores = []
                
                for entry in feed.entries[:10]:  # Get top 10 from each source
                    article = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'source': source_name,
                        'score': 0
                    }
                    
                    # Extract text content if available
                    if hasattr(entry, 'content'):
                        article['content'] = entry.content[0].value
                    else:
                        article['content'] = entry.get('summary', '')
                    
                    # Analyze relevance
                    relevance_score = self.analyze_article_relevance(article)
                    article['score'] = relevance_score
                    relevance_scores.append(relevance_score)
                    
                    if relevance_score > 0.5:  # Consider relevant if score > 0.5
                        relevant_count += 1
                        articles.append(article)
                    
                    total_count += 1
                
                # Update source metrics
                avg_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
                self.source_manager.update_metrics(source_name, total_count, relevant_count, avg_score)
                
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
        
        return articles
    
    def analyze_article_relevance(self, article: Dict) -> float:
        """Analyze article relevance using AI"""
        try:
            # Create a prompt for relevance analysis
            prompt = f"""
            Analyze the relevance of this article to Computer Science, AI, and Software Engineering:
            
            Title: {article['title']}
            Summary: {article['summary'][:500]}
            
            Rate the relevance from 0.0 to 1.0 where:
            0.0 = Not relevant to CS/AI/Software Engineering
            0.5 = Somewhat relevant
            1.0 = Highly relevant to CS/AI/Software Engineering
            
            Return only the numerical score (0.0 to 1.0).
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            score_text = response.choices[0].message.content.strip()
            try:
                return float(score_text)
            except ValueError:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error analyzing relevance: {e}")
            return 0.0
    
    def rank_articles(self, articles: List[Dict]) -> List[Dict]:
        """Rank articles by relevance and recency"""
        # Sort by score (relevance) and recency
        sorted_articles = sorted(
            articles,
            key=lambda x: (x['score'], x.get('published', '')),
            reverse=True
        )
        
        return sorted_articles[:10]  # Return top 10 articles
    
    def generate_ai_insights(self, articles: List[Dict]) -> str:
        """Generate AI-powered insights about the articles"""
        try:
            # Create a summary of the top articles
            article_summaries = []
            for i, article in enumerate(articles[:5], 1):
                summary = f"{i}. {article['title']} (Score: {article['score']:.2f})"
                article_summaries.append(summary)
            
            prompt = f"""
            Based on these top tech articles, provide 3-5 key insights about current trends in Computer Science, AI, and Software Engineering:
            
            Articles:
            {chr(10).join(article_summaries)}
            
            Provide insights that would be valuable for a tech newsletter audience.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return "AI insights generation failed."
    
    def generate_newsletter(self) -> str:
        """Generate a complete newsletter with dynamic sources"""
        try:
            logger.info("Starting newsletter generation with dynamic sources...")
            
            # Fetch articles from dynamic sources
            articles = self.fetch_articles_from_dynamic_sources()
            
            if not articles:
                return "No relevant articles found."
            
            # Rank articles
            top_articles = self.rank_articles(articles)
            self.top_articles = top_articles
            
            # Generate AI insights
            insights = self.generate_ai_insights(top_articles)
            
            # Create newsletter content
            newsletter_content = self.format_newsletter(top_articles, insights)
            
            # Auto-optimize sources based on performance
            self.source_manager.auto_optimize_sources()
            
            return newsletter_content
            
        except Exception as e:
            logger.error(f"Error generating newsletter: {e}")
            return f"Error generating newsletter: {str(e)}"
    
    def format_newsletter(self, articles: List[Dict], insights: str) -> str:
        """Format the newsletter with professional styling"""
        timestamp = datetime.now().strftime("%B %d, %Y")
        
        newsletter = f"""# 🤖 AI & Tech Newsletter
*Generated on {timestamp}*

## 🚀 **Top Stories This Week**

"""
        
        # Add top articles
        for i, article in enumerate(articles, 1):
            newsletter += f"""### {i}. {article['title']}
**Source:** {article['source'].replace('_', ' ').title()} | **Relevance Score:** {article['score']:.2f}

{article['summary'][:200]}...

[Read More]({article['link']})

---
"""
        
        # Add AI insights
        newsletter += f"""
## 🧠 **AI-Powered Insights**

{insights}

## 📊 **Source Performance Report**

{self.get_source_performance_summary()}

---
*This newsletter is automatically generated using AI and dynamically managed news sources.*
"""
        
        return newsletter
    
    def get_source_performance_summary(self) -> str:
        """Get a summary of source performance"""
        report = self.source_manager.get_performance_report()
        
        summary = f"""
- **Active Sources:** {report['active_sources']}/{report['total_sources']}
- **Articles Processed:** {report['total_articles_processed']}
- **Relevance Rate:** {report['overall_relevance_rate']:.1%}
- **Top Sources:** {', '.join(list(report['top_performing_sources'].keys())[:3])}
"""
        return summary
    
    def record_user_engagement(self, source_name: str, action: str):
        """Record user engagement for dynamic optimization"""
        self.source_manager.record_user_engagement(source_name, action)

if __name__ == "__main__":
    # Test the enhanced newsletter generator
    generator = EnhancedNewsletterGeneratorWithDynamicSources()
    newsletter = generator.generate_newsletter()
    
    # Save newsletter
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dynamic_newsletter_{timestamp}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(newsletter)
    
    print(f"Newsletter generated and saved as {filename}")
    print("Source performance report:")
    print(generator.get_source_performance_summary())
