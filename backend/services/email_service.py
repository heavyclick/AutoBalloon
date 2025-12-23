"""
Email Service
Send transactional emails using Resend
"""
import resend
from typing import Optional
from config import RESEND_API_KEY, EMAIL_FROM, APP_URL, APP_NAME


class EmailService:
    """
    Email service using Resend.
    Handles magic links, welcome emails, and receipts.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or RESEND_API_KEY
        if self.api_key:
            resend.api_key = self.api_key
    
    def send_magic_link(self, email: str, token: str) -> bool:
        """
        Send a magic login link to the user.
        
        Args:
            email: User's email address
            token: Magic link token
            
        Returns:
            True if sent successfully
        """
        magic_link_url = f"{APP_URL}/auth/verify?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0D0D0D; color: #ffffff; padding: 40px 20px; margin: 0;">
            <div style="max-width: 480px; margin: 0 auto; background-color: #161616; border-radius: 16px; padding: 40px; border: 1px solid #262626;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #E63946; font-size: 28px; margin: 0;">{APP_NAME}</h1>
                </div>
                
                <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 16px; text-align: center;">
                    Your Login Link
                </h2>
                
                <p style="color: #9CA3AF; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 32px;">
                    Click the button below to log in to your account. This link expires in 15 minutes.
                </p>
                
                <div style="text-align: center; margin-bottom: 32px;">
                    <a href="{magic_link_url}" 
                       style="display: inline-block; background-color: #E63946; color: #ffffff; text-decoration: none; padding: 16px 32px; border-radius: 12px; font-weight: bold; font-size: 16px;">
                        Log In to {APP_NAME}
                    </a>
                </div>
                
                <p style="color: #6B7280; font-size: 14px; text-align: center; margin-bottom: 16px;">
                    Or copy and paste this link:
                </p>
                
                <div style="background-color: #0D0D0D; border-radius: 8px; padding: 12px; margin-bottom: 32px; word-break: break-all;">
                    <code style="color: #9CA3AF; font-size: 12px;">{magic_link_url}</code>
                </div>
                
                <p style="color: #6B7280; font-size: 12px; text-align: center;">
                    If you didn't request this email, you can safely ignore it.
                </p>
            </div>
        </body>
        </html>
        """
        
        try:
            resend.Emails.send({
                "from": EMAIL_FROM,
                "to": email,
                "subject": f"Log in to {APP_NAME}",
                "html": html_content
            })
            return True
        except Exception as e:
            print(f"Failed to send magic link email: {e}")
            return False
    
    def send_welcome_email(self, email: str) -> bool:
        """
        Send welcome email to new Pro subscriber.
        
        Args:
            email: User's email address
            
        Returns:
            True if sent successfully
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0D0D0D; color: #ffffff; padding: 40px 20px; margin: 0;">
            <div style="max-width: 480px; margin: 0 auto; background-color: #161616; border-radius: 16px; padding: 40px; border: 1px solid #262626;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #E63946; font-size: 28px; margin: 0;">{APP_NAME}</h1>
                    <span style="background-color: #F59E0B; color: #000000; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px; margin-left: 8px;">PRO</span>
                </div>
                
                <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 16px; text-align: center;">
                    Welcome to Pro! 🎉
                </h2>
                
                <p style="color: #9CA3AF; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 24px;">
                    Thank you for subscribing to {APP_NAME} Pro. You now have unlimited access to:
                </p>
                
                <div style="background-color: #0D0D0D; border-radius: 12px; padding: 24px; margin-bottom: 32px;">
                    <ul style="color: #9CA3AF; font-size: 14px; line-height: 2; margin: 0; padding-left: 20px;">
                        <li>✓ Unlimited blueprint processing</li>
                        <li>✓ Unlimited AS9102 exports</li>
                        <li>✓ Permanent history storage</li>
                        <li>✓ Priority processing</li>
                        <li>✓ Early Adopter pricing locked in forever</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-bottom: 32px;">
                    <a href="{APP_URL}" 
                       style="display: inline-block; background-color: #E63946; color: #ffffff; text-decoration: none; padding: 16px 32px; border-radius: 12px; font-weight: bold; font-size: 16px;">
                        Start Using {APP_NAME}
                    </a>
                </div>
                
                <p style="color: #6B7280; font-size: 12px; text-align: center;">
                    Questions? Reply to this email and we'll help you out.
                </p>
            </div>
        </body>
        </html>
        """
        
        try:
            resend.Emails.send({
                "from": EMAIL_FROM,
                "to": email,
                "subject": f"Welcome to {APP_NAME} Pro! 🎉",
                "html": html_content
            })
            return True
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False
    
    def send_subscription_cancelled(self, email: str) -> bool:
        """
        Send email when subscription is cancelled.
        
        Args:
            email: User's email address
            
        Returns:
            True if sent successfully
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0D0D0D; color: #ffffff; padding: 40px 20px; margin: 0;">
            <div style="max-width: 480px; margin: 0 auto; background-color: #161616; border-radius: 16px; padding: 40px; border: 1px solid #262626;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="color: #E63946; font-size: 28px; margin: 0;">{APP_NAME}</h1>
                </div>
                
                <h2 style="color: #ffffff; font-size: 24px; margin-bottom: 16px; text-align: center;">
                    Subscription Cancelled
                </h2>
                
                <p style="color: #9CA3AF; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 24px;">
                    Your {APP_NAME} Pro subscription has been cancelled. You'll continue to have access until the end of your current billing period.
                </p>
                
                <p style="color: #9CA3AF; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 32px;">
                    We're sorry to see you go. If you change your mind, you can resubscribe at any time—but note that you may lose your Early Adopter pricing.
                </p>
                
                <div style="text-align: center;">
                    <a href="{APP_URL}" 
                       style="display: inline-block; background-color: #374151; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-size: 14px;">
                        Resubscribe
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            resend.Emails.send({
                "from": EMAIL_FROM,
                "to": email,
                "subject": f"Your {APP_NAME} subscription has been cancelled",
                "html": html_content
            })
            return True
        except Exception as e:
            print(f"Failed to send cancellation email: {e}")
            return False


# Singleton instance
email_service = EmailService()
