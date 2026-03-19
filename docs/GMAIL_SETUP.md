# Gmail Integration Setup Guide

This guide will help you set up Gmail integration for the Digital FTE Customer Success Agent.

## Prerequisites

- Google Cloud Account
- Gmail account for support email (e.g., support@yourcompany.com)
- Basic understanding of Google Cloud Console

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project"
3. Name your project (e.g., "digital-fte-gmail")
4. Click "Create"

## Step 2: Enable Gmail API

1. In your project, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Create Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click "Create Credentials" > "Service Account"
3. Fill in details:
   - Service account name: `digital-fte-agent`
   - Service account ID: `digital-fte-agent`
   - Description: "Service account for Digital FTE to send emails"
4. Click "Create and Continue"
5. **Grant Role**: Select "Project" > "Editor"
6. Click "Continue" and "Done"

## Step 4: Create Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Click "Create"
6. A JSON file will be downloaded - save this securely!

## Step 5: Move Credentials File

1. Create `credentials` directory in your project:
   ```bash
   mkdir -p backend/credentials
   ```

2. Move the downloaded JSON file:
   ```bash
   mv ~/Downloads/digital-fte-gmail-*.json backend/credentials/gmail_credentials.json
   ```

3. Update `.env` file:
   ```bash
   GMAIL_CREDENTIALS_FILE=backend/credentials/gmail_credentials.json
   SUPPORT_EMAIL=support@yourcompany.com
   ```

## Step 6: Enable Domain-Wide Delegation (Optional for G Suite)

If using G Suite / Google Workspace:

1. Go to service account details
2. Enable "Enable G Suite Domain-wide Delegation"
3. Copy the "Client ID"
4. In Google Workspace Admin Console:
   - Go to **Security** > **API Controls** > **Domain-wide Delegation**
   - Click "Add new"
   - Paste Client ID
   - Add OAuth Scope: `https://www.googleapis.com/auth/gmail.send`
   - Click "Authorize"

## Step 7: Set Up Gmail Pub/Sub Push Notifications

### Create Pub/Sub Topic

1. Go to [Pub/Sub Console](https://console.cloud.google.com/cloudpubsub)
2. Click "Create Topic"
3. Topic ID: `gmail-push-notifications`
4. Click "Create"

### Create Pub/Sub Subscription

1. Click on the topic you just created
2. Click "Create Subscription"
3. Subscription ID: `gmail-push-sub`
4. Delivery type: "Push"
5. Endpoint URL: `https://your-api-domain.com/webhooks/gmail`
   - For local testing: Use [ngrok](https://ngrok.com/) to expose localhost
6. Click "Create"

### Grant Gmail Permission to Publish

1. In Pub/Sub topic, go to **Permissions**
2. Click "Add Principal"
3. Principal: `gmail-api-push@system.gserviceaccount.com`
4. Role: "Pub/Sub Publisher"
5. Click "Save"

### Set Up Gmail Watch

Use the Gmail API to set up a watch on your inbox:

```bash
# Install gcloud CLI: https://cloud.google.com/sdk/install

# Authenticate
gcloud auth application-default login

# Set up watch
curl -X POST \
  https://www.googleapis.com/gmail/v1/users/me/watch \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "topicName": "projects/YOUR_PROJECT_ID/topics/gmail-push-notifications",
    "labelIds": ["INBOX"]
  }'
```

**Note**: Gmail watch expires after 7 days. You need to renew it periodically.

## Step 8: Test Gmail Integration

### Local Testing with ngrok

1. Start ngrok:
   ```bash
   ngrok http 8000
   ```

2. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

3. Update Pub/Sub subscription endpoint:
   - Go to Pub/Sub Console
   - Edit subscription
   - Change endpoint URL to: `https://abc123.ngrok.io/webhooks/gmail`

4. Start your backend:
   ```bash
   cd backend
   source venv/bin/activate
   python run_api.py
   ```

5. Send a test email to your support email

6. Check ngrok terminal for incoming webhook

7. Check backend logs for processing

### Verify Gmail Webhook

Test the health endpoint:
```bash
curl http://localhost:8000/webhooks/gmail/health
```

Expected response:
```json
{
  "status": "healthy",
  "webhook": "gmail",
  "channel": "email",
  "timestamp": "2024-03-17T10:30:00.000Z"
}
```

## Step 9: Production Deployment

1. Deploy your API to a public domain
2. Update Pub/Sub subscription endpoint to production URL
3. Set up Gmail watch with production credentials
4. Set up monitoring for Gmail webhook failures

## Environment Variables

Add these to your `.env` file:

```bash
# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=backend/credentials/gmail_credentials.json
GMAIL_TOKEN_FILE=backend/credentials/gmail_token.json
GMAIL_PUBSUB_TOPIC=projects/your-project-id/topics/gmail-push-notifications
GMAIL_PUBSUB_SUBSCRIPTION=projects/your-project-id/subscriptions/gmail-push-sub
SUPPORT_EMAIL=support@yourcompany.com
```

## Troubleshooting

### "Invalid grant" Error

- Check that service account has correct permissions
- Verify domain-wide delegation is enabled (for G Suite)
- Ensure OAuth scopes are correct

### Pub/Sub Webhook Not Receiving Messages

- Check that subscription endpoint URL is correct
- Verify that `gmail-api-push@system.gserviceaccount.com` has Publisher role
- Check Gmail watch is still active (expires after 7 days)
- Use ngrok for local testing

### Gmail API Quota Exceeded

- Default quota: 250 quota units per user per second
- Each send = 100 units = 2.5 emails/second
- Request quota increase in Google Cloud Console if needed

### Service Account Permission Denied

- Verify service account has "Editor" role
- Check that domain-wide delegation is enabled
- Ensure credentials file path is correct

## Security Best Practices

1. **Never commit credentials to Git**:
   - Add `credentials/` to `.gitignore`
   - Use environment variables for sensitive data

2. **Restrict Service Account Permissions**:
   - Use least privilege principle
   - Only grant necessary scopes

3. **Rotate Credentials Regularly**:
   - Create new service account keys periodically
   - Delete old keys

4. **Monitor API Usage**:
   - Set up alerts for quota usage
   - Monitor for suspicious activity

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Gmail Push Notifications](https://developers.google.com/gmail/api/guides/push)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)

## Support

If you encounter issues:
1. Check backend logs for error messages
2. Verify all environment variables are set
3. Test with ngrok locally first
4. Check Google Cloud Console for API errors
