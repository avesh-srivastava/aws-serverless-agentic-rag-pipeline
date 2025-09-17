# Support Escalation Agent - Ticket Creator
# Creates support tickets and sends notifications
import boto3
import json
import time
import uuid
from datetime import datetime

# Initialize clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

# Environment variables
TICKETS_TABLE = 'SupportTickets'
SUPPORT_EMAIL = 'support@yourcompany.com'

def lambda_handler(event, context):
    try:
        session_id = event.get('session_id')
        user_query = event.get('user_query')
        agent_response = event.get('agent_response')
        user_email = event.get('user_email', 'customer@example.com')
        
        # Generate ticket ID
        ticket_id = f"TICKET-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        # Create ticket in DynamoDB
        table = dynamodb.Table(TICKETS_TABLE)
        ticket_item = {
            'ticket_id': ticket_id,
            'session_id': session_id,
            'status': 'OPEN',
            'priority': 'MEDIUM',
            'created_at': datetime.utcnow().isoformat(),
            'customer_email': user_email,
            'original_query': user_query,
            'agent_response': agent_response,
            'category': 'UNRESOLVED_QUERY'
        }
        
        table.put_item(Item=ticket_item)
        
        # Send email notification to support team
        email_body = f"""
New Support Ticket Created: {ticket_id}

Customer Query: {user_query}

Agent Response: {agent_response}

Session ID: {session_id}
Customer Email: {user_email}
Created: {datetime.utcnow().isoformat()}

Please follow up with the customer.
        """
        
        ses.send_email(
            Source=SUPPORT_EMAIL,
            Destination={'ToAddresses': [SUPPORT_EMAIL]},
            Message={
                'Subject': {'Data': f'New Support Ticket: {ticket_id}'},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        
        return {
            'statusCode': 200,
            'ticket_id': ticket_id,
            'message': f'Support ticket {ticket_id} has been created. Our team will contact you soon.',
            'status': 'CREATED'
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'error': str(e),
            'message': 'Failed to create support ticket'
        }