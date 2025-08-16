# Deployment Guide for Render

## Overview
This guide explains how to deploy your WhatsApp chat analysis backend to Render for public access.

## Prerequisites
1. A Render account (free tier available)
2. Your Gemini API key from Google AI Studio
3. The WhatsApp chat JSON file

## Key Changes Made for Production

### 1. Environment Variables
- **GEMINI_API_KEY**: Your Google Gemini API key (required)
- **FLASK_ENV**: Set to "production" on Render
- **PORT**: Automatically set by Render

### 2. ChromaDB Configuration
- The app now automatically falls back to in-memory ChromaDB if persistent storage fails
- This is necessary because Render's filesystem is ephemeral
- Data will be re-embedded on each deployment

### 3. Error Handling & Logging
- Added comprehensive error handling and logging
- Health check endpoint at `/health` for Render monitoring
- Graceful fallbacks for missing data

### 4. File Path Handling
- The app now looks for the JSON file in multiple locations
- Supports both local development and Render deployment

## Deployment Steps

### 1. Prepare Your Repository
Ensure your repository contains:
- `backend/app.py` (updated production version)
- `backend/requirements.txt`
- `render.yaml` (deployment configuration)
- `whatsapp_chat_rohan_full.json` (your chat data)

### 2. Set Up Render
1. Go to [render.com](https://render.com) and create an account
2. Connect your GitHub repository
3. Create a new Web Service

### 3. Configure Environment Variables
In Render dashboard, set:
- **GEMINI_API_KEY**: Your actual Gemini API key
- **FLASK_ENV**: `production`

### 4. Deploy
1. Render will automatically detect the `render.yaml` configuration
2. The build process will install dependencies and start the service
3. Monitor the build logs for any issues

## Important Notes

### Data Persistence
- **ChromaDB data is NOT persistent** on Render's free tier
- Each deployment will re-embed your WhatsApp chat data
- This process takes time but ensures data is always available

### API Limits
- Monitor your Gemini API usage
- The free tier has rate limits
- Consider upgrading if you expect high traffic

### Performance
- The free tier has limited resources
- Embedding generation happens on each deployment
- Consider using a paid tier for production use

## Testing Your Deployment

### Health Check
```
GET https://your-app-name.onrender.com/health
```

### Root Endpoint
```
GET https://your-app-name.onrender.com/
```

### Ask Endpoint
```
POST https://your-app-name.onrender.com/ask
Content-Type: application/json

{
  "question": "What did we talk about yesterday?"
}
```

## Troubleshooting

### Common Issues
1. **Build Failures**: Check that all dependencies are in `requirements.txt`
2. **API Key Errors**: Verify `GEMINI_API_KEY` is set correctly
3. **File Not Found**: Ensure `whatsapp_chat_rohan_full.json` is in the repository
4. **Memory Issues**: Reduce `max_workers` in the ThreadPoolExecutor if needed

### Logs
- Check Render dashboard for build and runtime logs
- The app includes comprehensive logging for debugging

## Security Considerations
- Never commit your actual API keys to the repository
- Use Render's environment variable system for sensitive data
- The app includes CORS configuration for frontend integration
- Consider adding rate limiting for production use

## Cost Optimization
- Free tier includes 750 hours/month
- Embedding generation happens on each deployment
- Consider caching strategies for production use
- Monitor API usage to avoid unexpected charges
