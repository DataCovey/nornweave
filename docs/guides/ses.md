# AWS SES setup

1. In AWS: Create verified identities (domain or email), request production access if needed.
2. In NornWeave `.env`:
   - `EMAIL_PROVIDER=ses`
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
   - `EMAIL_DOMAIN=<verified sending domain or address>`
3. For receiving: Configure SES receipt rules to deliver to S3 or Lambda, then forward to your NornWeave webhook (e.g. via Lambda that POSTs to `https://your-server.com/webhooks/ses`). Exact steps depend on your AWS setup.
4. Ensure the IAM user has `ses:SendEmail` and any permissions needed for receiving (e.g. S3, Lambda).
