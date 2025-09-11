import logging
from typing import Any, Union
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from core.tool.tool_class import Tool

logger = logging.getLogger(__name__)


class MailSenderTool(Tool):
    """
    A tool for sending emails using SMTP.
    """
    
    def __init__(self):
        super().__init__(
            name="mail_sender",
            description="Sends emails using SMTP with configurable server settings"
        )
        self.name = "mail_sender"
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
    
    def get_input_schema_prompt(self) -> str:
        """
        Returns a string prompt describing the expected input schema for the mail sender tool.
        
        Returns:
            str: A description of the input schema
        """
        return """
Mail Sender Tool Input Schema:
The input should be a dictionary with the following required fields:
- 'to': str - Recipient email address
- 'subject': str - Email subject line
- 'body': str - Email body content (plain text)

Optional fields:
- 'to_list': list[str] - List of recipient email addresses (alternative to 'to')
- 'cc': list[str] - List of CC email addresses
- 'bcc': list[str] - List of BCC email addresses
- 'is_html': bool - Whether the body content is HTML (default: False)

Example:
{
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email message",
    "is_html": False
}

Environment variables required:
- SMTP_SERVER: SMTP server address (default: smtp.gmail.com)
- SMTP_PORT: SMTP server port (default: 587)
- SMTP_USERNAME: SMTP username/email
- SMTP_PASSWORD: SMTP password or app password
        """
    
    def validate_input_schema(self, input_data: Any) -> Union[bool, str]:
        """
        Validates the input data against the mail sender tool's expected schema.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            Union[bool, str]: True if validation passes, or a string error message
                            describing the current input schema and what's wrong
        """
        if not isinstance(input_data, dict):
            return {
                "success": False,
                "server_error": True,
                "error": f"Input must be a dictionary. Current input type: {type(input_data).__name__} {input_data}"
            }
        
        # Check for required fields
        required_fields = ['subject', 'body']
        missing_fields = []
        
        for field in required_fields:
            if field not in input_data:
                missing_fields.append(field)
        
        # Check that either 'to' or 'to_list' is provided
        if 'to' not in input_data and 'to_list' not in input_data:
            missing_fields.append("either 'to' or 'to_list'")
        
        if missing_fields:
            return {
                "success": False,
                "server_error": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}. {self.get_input_schema_prompt()}"
            }
        
        # Validate field types
        if 'to' in input_data and not isinstance(input_data['to'], str):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'to' must be a string. Current type: {type(input_data['to']).__name__}"
            }
        
        if 'to_list' in input_data and not isinstance(input_data['to_list'], list):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'to_list' must be a list. Current type: {type(input_data['to_list']).__name__}"
            }
        
        if not isinstance(input_data['subject'], str):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'subject' must be a string. Current type: {type(input_data['subject']).__name__}"
            }
        
        if not isinstance(input_data['body'], str):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'body' must be a string. Current type: {type(input_data['body']).__name__}"
            }
        
        # Validate optional fields
        if 'cc' in input_data and not isinstance(input_data['cc'], list):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'cc' must be a list. Current type: {type(input_data['cc']).__name__}"
            }
        
        if 'bcc' in input_data and not isinstance(input_data['bcc'], list):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'bcc' must be a list. Current type: {type(input_data['bcc']).__name__}"
            }
        
        if 'is_html' in input_data and not isinstance(input_data['is_html'], bool):
            return {
                "success": False,
                "server_error": False,
                "error": f"Field 'is_html' must be a boolean. Current type: {type(input_data['is_html']).__name__}"
            }
        
        # Check if SMTP credentials are configured
        if not self.username or not self.password:
            return {
                "success": False,
                "server_error": True,
                "error": f"SMTP credentials not configured. Please set SMTP_USERNAME and SMTP_PASSWORD environment variables. {self.get_input_schema_prompt()}"
            }
        
        return {
            "success": True,
            "server_error": False,
            "error": None
        }
    
    def run(self, input_data: Any) -> Any:
        """
        Executes the mail sender tool with the provided input data.
        
        Args:
            input_data: The input data containing email details
            
        Returns:
            Dict: Result of the email sending operation
        """
        try:
            logger.info(f"{self.name} is running with input data: {input_data}")

            # Validate input first
            validation_result = self.validate_input_schema(input_data)
            if validation_result['success'] is False:
                logger.info(f"{self.name} input data validation failed: {validation_result}")
                return {
                "success": False,
                "server_error": False,
                "error": validation_result
            }

            logger.info(f"{self.name} input data validated successfully")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            
            # Handle recipients
            if 'to' in input_data:
                msg['To'] = input_data['to']
                recipients = [input_data['to']]
            else:
                msg['To'] = ', '.join(input_data['to_list'])
                recipients = input_data['to_list']
            
            # Add CC and BCC
            if 'cc' in input_data:
                msg['Cc'] = ', '.join(input_data['cc'])
                recipients.extend(input_data['cc'])
            
            if 'bcc' in input_data:
                recipients.extend(input_data['bcc'])
            
            msg['Subject'] = input_data['subject']
            
            # Add body
            is_html = input_data.get('is_html', False)
            if is_html:
                msg.attach(MIMEText(input_data['body'], 'html'))
            else:
                msg.attach(MIMEText(input_data['body'], 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg, to_addrs=recipients)
            
            logger.info(f"{self.name} sent email successfully to {len(recipients)} recipient(s)")
            
            return {
                "success": True,
                "message": f"Email sent successfully to {len(recipients)} recipient(s)",
                "recipients": recipients
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"{self.name} SMTP authentication failed: {str(e)}")
            return {
                "success": False,
                "error": f"SMTP authentication failed: {str(e)}"
            }
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"{self.name} Recipients refused: {str(e)}")
            return {
                "success": False,
                "error": f"Recipients refused: {str(e)}"
            }
        except smtplib.SMTPException as e:
            logger.error(f"{self.name} SMTP error: {str(e)}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"{self.name} Input validation error: {str(e)}")
            return {
                "success": False,
                "error": f"Input validation error: {str(e)}"
            }
