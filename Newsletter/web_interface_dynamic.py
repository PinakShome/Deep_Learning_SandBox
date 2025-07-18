from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
import json
from datetime import datetime
from enhanced_newsletter_with_dynamic_sources import EnhancedNewsletterGeneratorWithDynamicSources
from scheduler import NewsletterScheduler
import threading
import time

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Global instances
generator = EnhancedNewsletterGeneratorWithDynamicSources()
scheduler = NewsletterScheduler()

# Store newsletters in memory (in production, use a database)
newsletters = []

@app.route('/')
def index():
    """Main dashboard with dynamic source management"""
    # Get source performance data
    source_report = generator.source_manager.get_performance_report()
    return render_template('index.html', 
                         newsletters=newsletters[-5:],
                         source_report=source_report)

@app.route('/generate', methods=['POST'])
def generate_newsletter():
    """Generate a new newsletter with dynamic sources"""
    try:
        newsletter_content = generator.generate_newsletter()
        
        # Store newsletter
        newsletter_data = {
            'id': len(newsletters) + 1,
            'content': newsletter_content,
            'generated_at': datetime.now().isoformat(),
            'filename': f"dynamic_newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        }
        
        newsletters.append(newsletter_data)
        
        # Save to file
        with open(newsletter_data['filename'], 'w', encoding='utf-8') as f:
            f.write(newsletter_content)
        
        return jsonify({
            'success': True,
            'message': 'Newsletter generated successfully with dynamic sources!',
            'newsletter': newsletter_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating newsletter: {str(e)}'
        }), 500

@app.route('/sources')
def manage_sources():
    """Manage dynamic sources"""
    source_report = generator.source_manager.get_performance_report()
    return render_template('sources.html', source_report=source_report)

@app.route('/sources/add', methods=['POST'])
def add_source():
    """Add a new source"""
    name = request.form.get('name')
    url = request.form.get('url')
    
    if name and url:
        success = generator.source_manager.add_source(name, url)
        if success:
            return jsonify({
                'success': True,
                'message': f'Source {name} added successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add source. Please check the URL.'
            }), 400
    else:
        return jsonify({
            'success': False,
            'message': 'Name and URL are required.'
        }), 400

@app.route('/sources/remove', methods=['POST'])
def remove_source():
    """Remove a source"""
    name = request.form.get('name')
    
    if name:
        generator.source_manager.remove_source(name)
        return jsonify({
            'success': True,
            'message': f'Source {name} removed successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Source name is required.'
        }), 400

@app.route('/sources/optimize', methods=['POST'])
def optimize_sources():
    """Run automatic source optimization"""
    try:
        generator.source_manager.auto_optimize_sources()
        return jsonify({
            'success': True,
            'message': 'Source optimization completed!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error optimizing sources: {str(e)}'
        }), 500

@app.route('/api/sources/performance')
def api_source_performance():
    """API endpoint for source performance data"""
    return jsonify(generator.source_manager.get_performance_report())

@app.route('/api/sources/top')
def api_top_sources():
    """API endpoint for top performing sources"""
    top_sources = generator.source_manager.get_top_sources(10)
    return jsonify({
        'top_sources': top_sources,
        'total_sources': len(generator.source_manager.sources)
    })

@app.route('/newsletter/<int:newsletter_id>')
def view_newsletter(newsletter_id):
    """View a specific newsletter"""
    if 0 <= newsletter_id < len(newsletters):
        return render_template('view_newsletter.html', 
                             newsletter=newsletters[newsletter_id], 
                             newsletter_id=newsletter_id)
    else:
        return "Newsletter not found", 404

@app.route('/download/<int:newsletter_id>')
def download_newsletter(newsletter_id):
    """Download newsletter as markdown file"""
    if 0 <= newsletter_id < len(newsletters):
        newsletter = newsletters[newsletter_id]
        return send_file(
            newsletter['filename'],
            as_attachment=True,
            download_name=f"dynamic_newsletter_{newsletter_id}.md"
        )
    else:
        return "Newsletter not found", 404

@app.route('/subscribers')
def manage_subscribers():
    """Manage subscribers page"""
    return render_template('subscribers.html', subscribers=scheduler.subscribers)

@app.route('/subscribers/add', methods=['POST'])
def add_subscriber():
    """Add a new subscriber"""
    email = request.form.get('email')
    if email and '@' in email:
        scheduler.add_subscriber(email)
        return jsonify({
            'success': True,
            'message': f'Subscriber {email} added successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid email address'
        }), 400

@app.route('/subscribers/remove', methods=['POST'])
def remove_subscriber():
    """Remove a subscriber"""
    email = request.form.get('email')
    if email in scheduler.subscribers:
        scheduler.remove_subscriber(email)
        return jsonify({
            'success': True,
            'message': f'Subscriber {email} removed successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Subscriber not found'
        }), 404

@app.route('/schedule')
def manage_schedule():
    """Manage newsletter schedule"""
    return render_template('schedule.html')

@app.route('/schedule/daily', methods=['POST'])
def schedule_daily():
    """Schedule daily newsletter"""
    time_str = request.form.get('time', '09:00')
    scheduler.schedule_daily_newsletter(time_str)
    return jsonify({
        'success': True,
        'message': f'Daily newsletter scheduled at {time_str}'
    })

@app.route('/schedule/weekly', methods=['POST'])
def schedule_weekly():
    """Schedule weekly newsletter"""
    day = request.form.get('day', 'monday')
    time_str = request.form.get('time', '09:00')
    scheduler.schedule_weekly_newsletter(day, time_str)
    return jsonify({
        'success': True,
        'message': f'Weekly newsletter scheduled on {day} at {time_str}'
    })

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    source_report = generator.source_manager.get_performance_report()
    return jsonify({
        'total_newsletters': len(newsletters),
        'subscribers': len(scheduler.subscribers),
        'last_generated': newsletters[-1]['generated_at'] if newsletters else None,
        'source_performance': source_report
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
