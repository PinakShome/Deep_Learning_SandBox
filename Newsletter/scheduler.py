import schedule
import time
import threading
from datetime import datetime
import logging
from enhanced_newsletter_with_dynamic_sources import EnhancedNewsletterGeneratorWithDynamicSources
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsletterScheduler:
    def __init__(self):
        self.generator = EnhancedNewsletterGeneratorWithDynamicSources()
        self.subscribers = []
        
    def generate_and_send_newsletter(self):
        """Generate newsletter and send to subscribers"""
        try:
            logger.info("Starting scheduled newsletter generation...")
            
            # Generate newsletter
            newsletter_content = self.generator.generate_newsletter()
            
            # Send to subscribers
            if self.subscribers:
                self.send_newsletter_to_subscribers(newsletter_content)
            
            logger.info("Scheduled newsletter completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in scheduled newsletter generation: {e}")
    
    def send_newsletter_to_subscribers(self, content: str):
        """Send newsletter to all subscribers via email"""
        try:
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            email_address = os.getenv('EMAIL_ADDRESS')
            email_password = os.getenv('EMAIL_PASSWORD')
            
            if not all([email_address, email_password]):
                logger.warning("Email credentials not configured. Skipping email send.")
                return
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"AI & Software Engineering Newsletter - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = email_address
            
            # Convert markdown to HTML (simple conversion)
            html_content = self.convert_markdown_to_html(content)
            
            # Add HTML and text versions
            text_part = MIMEText(content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send to each subscriber
            for subscriber in self.subscribers:
                try:
                    msg['To'] = subscriber
                    
                    # Connect to SMTP server
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(email_address, email_password)
                    
                    # Send email
                    server.send_message(msg)
                    server.quit()
                    
                    logger.info(f"Newsletter sent to {subscriber}")
                    
                except Exception as e:
                    logger.error(f"Error sending to {subscriber}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in email sending: {e}")
    
    def convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to HTML"""
        html = markdown_content
        
        # Simple markdown to HTML conversion
        html = html.replace('# ', '<h1>').replace('\n# ', '</h1>\n<h1>')
        html = html.replace('## ', '<h2>').replace('\n## ', '</h2>\n<h2>')
        html = html.replace('### ', '<h3>').replace('\n### ', '</h3>\n<h3>')
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        html = html.replace('*', '<em>').replace('*', '</em>')
        html = html.replace('\n\n', '</p>\n<p>')
        
        # Wrap in HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                {html}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def add_subscriber(self, email: str):
        """Add a new subscriber"""
        if email not in self.subscribers:
            self.subscribers.append(email)
            logger.info(f"Added subscriber: {email}")
    
    def remove_subscriber(self, email: str):
        """Remove a subscriber"""
        if email in self.subscribers:
            self.subscribers.remove(email)
            logger.info(f"Removed subscriber: {email}")
    
    def schedule_daily_newsletter(self, time_str: str = "09:00"):
        """Schedule daily newsletter at specified time"""
        schedule.every().day.at(time_str).do(self.generate_and_send_newsletter)
        logger.info(f"Scheduled daily newsletter at {time_str}")
    
    def schedule_weekly_newsletter(self, day: str = "monday", time_str: str = "09:00"):
        """Schedule weekly newsletter"""
        getattr(schedule.every(), day).at(time_str).do(self.generate_and_send_newsletter)
        logger.info(f"Scheduled weekly newsletter on {day} at {time_str}")
    
    def run_scheduler(self):
        """Run the scheduler"""
        logger.info("Starting newsletter scheduler...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_once(self):
        """Run newsletter generation once"""
        self.generate_and_send_newsletter()

def main():
    """Main function to run the scheduler"""
    scheduler = NewsletterScheduler()
    
    # Add some test subscribers (replace with real emails)
    # scheduler.add_subscriber("test@example.com")
    
    # Schedule daily newsletter at 9 AM
    scheduler.schedule_daily_newsletter("09:00")
    
    # Run the scheduler
    scheduler.run_scheduler()

if __name__ == "__main__":
    main() 