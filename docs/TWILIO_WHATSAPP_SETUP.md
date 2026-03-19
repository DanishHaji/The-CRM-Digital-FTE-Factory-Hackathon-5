# Twilio WhatsApp Integration Setup Guide

This guide will help you set up WhatsApp integration for the Digital FTE Customer Success Agent using Twilio.

## Prerequisites

- Twilio Account (sign up at [twilio.com](https://www.twilio.com/try-twilio))
- Phone number for testing
- WhatsApp installed on your phone
- Basic understanding of webhooks

## Step 1: Create Twilio Account

1. Go to [Twilio Sign Up](https://www.twilio.com/try-twilio)
2. Fill in your details
3. Verify your email and phone number
4. Complete the getting started survey

**Free Trial**: Twilio provides $15 in credit for testing (enough for ~1,000 messages)

## Step 2: Get Twilio Credentials

1. Go to [Twilio Console](https://console.twilio.com/)
2. Find your **Account SID** and **Auth Token** on the dashboard
3. Copy these values - you'll need them for `.env`

```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token: your_auth_token_here
```

## Step 3: Set Up WhatsApp Sandbox (For Testing)

Twilio provides a WhatsApp Sandbox for testing without needing an approved Business Account.

### Enable Sandbox

1. In Twilio Console, go to **Messaging** > **Try it out** > **Send a WhatsApp message**
2. You'll see a sandbox number (e.g., `+1 415 523 8886`)
3. You'll see a join code (e.g., `join <word>-<word>`)

### Connect Your WhatsApp

1. Open WhatsApp on your phone
2. Send the join code to the sandbox number
   - Example: Send `join orange-cloud` to `+1 415 523 8886`
3. You'll receive a confirmation message
4. Your WhatsApp is now connected to the sandbox!

**Note**: Sandbox is for testing only. For production, you need an approved WhatsApp Business Account.

## Step 4: Configure Webhook URL

### Local Testing with ngrok

1. Install ngrok:
   ```bash
   # macOS
   brew install ngrok

   # Or download from: https://ngrok.com/download
   ```

2. Start ngrok:
   ```bash
   ngrok http 8000
   ```

3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Set Webhook in Twilio

1. In Twilio Console, go to **Messaging** > **Try it out** > **Send a WhatsApp message**
2. Scroll down to "Sandbox Configuration"
3. Find "WHEN A MESSAGE COMES IN" field
4. Enter your webhook URL:
   ```
   https://YOUR_NGROK_URL.ngrok.io/webhooks/whatsapp
   ```
5. Make sure HTTP method is **POST**
6. Click "Save"

## Step 5: Configure Environment Variables

Add these to your `.env` file:

```bash
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WEBHOOK_VALIDATE=true

# Channel Configuration (already in .env)
CHANNEL_WHATSAPP_MAX_RESPONSE_LENGTH=300
CHANNEL_WHATSAPP_SPLIT_THRESHOLD=1600
```

**Important**:
- `TWILIO_WHATSAPP_FROM` should be the sandbox number (or your approved number)
- Include the `whatsapp:` prefix
- `TWILIO_WEBHOOK_VALIDATE=true` for production (can set to `false` for local testing)

## Step 6: Test WhatsApp Integration

### Start Your Backend

```bash
cd backend
source venv/bin/activate
python run_api.py
```

### Verify Webhook Health

```bash
curl http://localhost:8000/webhooks/whatsapp/health
```

Expected response:
```json
{
  "status": "healthy",
  "webhook": "whatsapp",
  "channel": "whatsapp",
  "timestamp": "2024-03-17T10:30:00.000Z"
}
```

### Send Test Message

1. Open WhatsApp on your phone
2. Open the conversation with the Twilio sandbox number
3. Send a message: `Hi, I need help resetting my password`
4. Wait 2-3 seconds
5. You should receive a concise AI-powered response!

### Check Backend Logs

```bash
# In your terminal running the backend, you should see:
whatsapp_webhook_received | from_phone=+1234567890 | profile_name=YourName
whatsapp_message_sent | to_phone=+1234567890 | message_sid=SMxxx
whatsapp_webhook_processed | escalated=false | processing_time_ms=2500
```

## Step 7: Production Setup (WhatsApp Business Account)

For production use, you need an approved WhatsApp Business Account:

### Requirements

1. **Facebook Business Manager** account
2. **WhatsApp Business Account** (verified)
3. **Twilio WhatsApp Sender** (approved by WhatsApp)

### Steps

1. In Twilio Console, go to **Messaging** > **Senders** > **WhatsApp senders**
2. Click "Request to enable your Twilio numbers for WhatsApp"
3. Follow the approval process:
   - Submit your business info
   - Provide use case description
   - Wait for WhatsApp approval (1-3 weeks)
4. Once approved, configure your production number
5. Update `.env` with your approved number

## Step 8: Advanced Configuration

### Message Splitting

Long messages (> 1600 chars) are automatically split:

```bash
# Adjust thresholds in .env
CHANNEL_WHATSAPP_SPLIT_THRESHOLD=1600  # Max chars per message
```

### Response Length

Control how concise WhatsApp responses should be:

```bash
CHANNEL_WHATSAPP_MAX_RESPONSE_LENGTH=300  # Preferred length
```

### Signature Validation

For security, always validate Twilio signatures in production:

```bash
TWILIO_WEBHOOK_VALIDATE=true  # Always true in production
```

## Features Implemented

### ✅ Concise Responses
- No formal greeting ("Dear...")
- No signature block
- Direct and conversational
- Preferred length: < 300 chars

### ✅ Message Splitting
- Automatically splits messages > 1600 chars
- Splits at word boundaries (no partial words)
- Includes part indicators: "(part 1/2)", "(part 2/2)"
- Small delay between parts (0.5s) to ensure order

### ✅ Signature Validation
- Validates X-Twilio-Signature header
- HMAC-SHA1 verification
- Rejects invalid signatures with 403 Forbidden

### ✅ Phone Number Normalization
- Removes "whatsapp:" prefix
- Normalizes phone formats
- Handles international numbers

### ✅ Profile Name Extraction
- Uses WhatsApp profile name if available
- Falls back to phone number

### ✅ Escalation Keywords
- "human", "agent", "representative" trigger escalation
- All standard escalation keywords apply

## Troubleshooting

### Webhook Not Receiving Messages

**Problem**: Send WhatsApp message but backend doesn't receive it

**Solutions**:
1. Check ngrok is running: `curl https://YOUR_URL.ngrok.io/webhooks/whatsapp/health`
2. Verify webhook URL in Twilio Console matches ngrok URL
3. Check ngrok terminal for incoming requests
4. Ensure WhatsApp is connected to sandbox (send join code again)

### Invalid Signature Error

**Problem**: `403 Forbidden - Invalid Twilio signature`

**Solutions**:
1. Check `TWILIO_AUTH_TOKEN` in `.env` is correct
2. Verify webhook URL matches exactly (including https://)
3. For local testing, set `TWILIO_WEBHOOK_VALIDATE=false` temporarily
4. Check that request URL includes query parameters if any

### No Response Sent

**Problem**: Backend processes message but WhatsApp doesn't receive response

**Solutions**:
1. Check backend logs for errors
2. Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct
3. Check `TWILIO_WHATSAPP_FROM` matches your sandbox/approved number
4. Ensure Groq API key is valid
5. Check Twilio Console > Monitor > Logs for API errors

### Message Too Long

**Problem**: Message is truncated or doesn't send

**Solution**:
- Messages > 1600 chars are automatically split
- If still having issues, reduce `CHANNEL_WHATSAPP_SPLIT_THRESHOLD`

### Sandbox Expired

**Problem**: "Your session has expired" message

**Solution**:
- Sandbox connection expires after 24 hours of inactivity
- Send join code again: `join <word>-<word>`

## Testing Checklist

Test these scenarios:

- [ ] Send simple question → Receive concise response
- [ ] Send long question → Response is < 300 chars
- [ ] Request "human agent" → Escalation message received
- [ ] Send legal keyword → Escalation triggered
- [ ] Multiple messages → All processed correctly
- [ ] Long response → Multiple messages received (if > 1600 chars)
- [ ] Check database → Customer, conversation, messages created
- [ ] Test with multiple users → All work independently

## Cost Estimation

### Sandbox (Free Trial)
- $15 credit
- ~1,000 messages
- Perfect for testing

### Production Pricing
- **WhatsApp Messages**: $0.005 per message (incoming + outgoing)
- **Average cost per conversation**: $0.02 - $0.05
- **1,000 customers/month**: ~$20-50/month
- Much cheaper than human agents!

## Security Best Practices

1. **Always validate signatures in production**:
   ```bash
   TWILIO_WEBHOOK_VALIDATE=true
   ```

2. **Never commit credentials**:
   - Add `.env` to `.gitignore`
   - Use environment variables

3. **Rotate credentials regularly**:
   - Generate new Auth Token periodically
   - Update in Twilio Console and `.env`

4. **Monitor for suspicious activity**:
   - Check Twilio Console > Monitor > Logs
   - Set up alerts for unusual patterns

5. **Rate limiting**:
   - Implement rate limiting for high volume
   - Use Twilio's built-in rate limits

## Additional Resources

- [Twilio WhatsApp API Documentation](https://www.twilio.com/docs/whatsapp/api)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Twilio Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)
- [Webhook Security](https://www.twilio.com/docs/usage/webhooks/webhooks-security)
- [Pricing](https://www.twilio.com/whatsapp/pricing)

## Support

If you encounter issues:
1. Check backend logs: `tail -f backend/logs/digital-fte.log`
2. Check Twilio Console > Monitor > Logs
3. Test webhook health endpoint
4. Verify all environment variables are set
5. Try with `TWILIO_WEBHOOK_VALIDATE=false` for debugging

## Next Steps

After WhatsApp is working:
1. Test cross-channel: Email → WhatsApp → Web Form
2. Verify customer linking works correctly
3. Test escalation flows
4. Set up monitoring and alerts
5. Plan for production WhatsApp Business approval
